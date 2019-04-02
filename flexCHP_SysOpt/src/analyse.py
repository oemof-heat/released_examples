
__copyright__ = "Beuth Hochschule für Technik Berlin, Reiner Lemoine Institut"
__license__ = "GPLv3"
__author__ = "jakob-wo (jakob.wolf@beuth-hochschule.de)"

###############################################################################
# imports
###############################################################################

import oemof.solph as solph
import oemof.outputlib as outputlib
from oemof.outputlib import processing, views
import oemof.tools.economics as eco

import os
import pandas as pd
import pprint as pp
import matplotlib
import numpy as np
import matplotlib.pyplot as plt
import yaml


def analyse_energy_system(config_path, variation_nr):

    ##########################################################################
    # Read external data
    ##########################################################################

    # Read configuration file
    with open(config_path, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))

    # Read parameters
    file_path_param_01 = abs_path + cfg['parameters_energy_system']
    file_path_param_02 = abs_path + cfg['parameter_variation'][variation_nr]
    param_df_01 = pd.read_csv(file_path_param_01, index_col=1)
    param_df_02 = pd.read_csv(file_path_param_02, index_col=1)
    param_df = pd.concat([param_df_01, param_df_02])
    param_value = param_df['value']

    # Read district heating and electricity demand
    file_path_demand_ts = abs_path + cfg['demand_time_series']
    data = pd.read_csv(file_path_demand_ts)

    ##########################################################################
    # Restore optimization results
    ##########################################################################

    energysystem = solph.EnergySystem()

    # Decide which results (oemof-file) is to be analysed depending on
    # the settings in the config-file
    if cfg['price_el_quadratic']:
        energysystem.restore(
            dpath=(abs_path + "/results/optimisation_results/dumps/"
                              "quadratic_price_relationship"),
            filename=(cfg['filename_dumb'] + '_scenario_{0}.oemof'.
                      format(variation_nr)))
        price_relation = 'quadratic'
    if cfg['price_el_quadratic'] == False:
        energysystem.restore(
            dpath=(abs_path + "/results/optimisation_results/dumps/"
                              "linear_price_relationship"),
            filename=(cfg['filename_dumb'] + '_scenario_{0}.oemof'.
                      format(variation_nr)))
        price_relation = 'linear'

    results = energysystem.results['main']

    string_results = outputlib.views.convert_keys_to_strings(
        energysystem.results['main'])

    ##########################################################################
    # Display accumulated flows of buses
    ##########################################################################

    print('\n*** Analysis of scenario {} *** '.format(variation_nr))
    print('Used price relationship: {}  '.format(price_relation))
    print("")

    electricity_bus = outputlib.views.node(results, 'electricity')
    print('electricity bus: sums in GWh_el')
    print(electricity_bus['sequences'].sum(axis=0)/1e3)

    heat_bus = outputlib.views.node(results, 'heat')
    print('heat bus: sums in GWh_th')
    print(heat_bus['sequences'].sum(axis=0)/1e3)

    ##########################################################################
    # Extract information from the results file
    ##########################################################################

    # Get sequences (time series) for specific components from the results file
    CHP_01_heat = string_results[('CHP_01', 'heat')]['sequences']
    CHP_01_electricity = string_results[('CHP_01', 'electricity')]['sequences']
    residual_load = string_results[('residual_el', 'residual')]['sequences']
    boiler = string_results[('boiler', 'heat')]['sequences']
    P2H_th = string_results['P2H', 'heat']['sequences']
    TES_discharge = string_results['storage_th', 'heat']['sequences']
    TES_charge = string_results['heat', 'storage_th']['sequences']
    TES_soc = (string_results['storage_th', 'None'][
            'sequences'])  # State of charge (SOC) in MWh_th
    TES_soc_rel = (string_results['storage_th', 'None']['sequences']
                   / string_results['storage_th', 'None']['sequences'].
                   max()*100)  # State of charge in %
    battery_discharge = string_results['storage_el', 'electricity'][
        'sequences']
    battery_charge = string_results['electricity', 'storage_el']['sequences']
    battery_soc = string_results['storage_el', 'None']['sequences']
    battery_soc_rel = (string_results['storage_el', 'None']['sequences']
                       /string_results['storage_el', 'None']['sequences']
                       .max()*100)
    shortage_electricity = string_results['shortage_bel', 'electricity'][
        'sequences']
    shortage_heat = string_results['shortage_bth', 'heat']['sequences']
    excess_electricity = string_results['electricity', 'excess_bel'][
        'sequences']
    excess_heat = string_results['heat', 'excess_bth']['sequences']
    gas_consumption = string_results['rgas', 'natural_gas']['sequences']
    demand_th = string_results['heat', 'demand_th']['sequences']
    demand_el = string_results['electricity', 'demand_el']['sequences']
    gas_consumption_CHP = string_results['natural_gas', 'CHP_01']['sequences']
    eta_el = (string_results[('CHP_01', 'electricity')]['sequences']
              /gas_consumption_CHP)

    omega_CHP = ((string_results[('CHP_01', 'electricity')]['sequences']
                  + string_results[('CHP_01', 'heat')]['sequences'])
                 /gas_consumption_CHP)
    eta_el_sum = (string_results[('CHP_01', 'electricity')]['sequences'].
                  sum()/gas_consumption_CHP.sum())
    omega_CHP_sum = ((string_results[('CHP_01', 'electricity')]['sequences'].
                      flow.sum()
                      + string_results[('CHP_01', 'heat')]['sequences'].flow.
                      sum())/gas_consumption_CHP.flow.sum())
    stored_el = residual_load - demand_el[residual_load > 0]

    # Auxiliary values for the later operation analysis
    aux_shortage_df = shortage_heat.add(shortage_electricity)
    aux_chp_01_df = CHP_01_heat.add(CHP_01_electricity)

    # Get investment results (i.e., installed capacity or power of the
    # components) from the results file. Scalar values.
    storage_el_cap = (outputlib.views.node(results, 'storage_el')[
        'scalars'][(('storage_el', 'None'), 'invest')])
    storage_th_cap = (outputlib.views.node(results, 'storage_th')[
        'scalars'][(('storage_th', 'None'), 'invest')])
    chp_cap = (outputlib.views.node(results, 'CHP_01')[
                   'scalars'][(('natural_gas', 'CHP_01'), 'invest')]
               * param_value['conv_factor_full_cond'])
    P2H_cap = (outputlib.views.node(results, 'P2H')[
        'scalars'][(('P2H', 'heat'), 'invest')])
    boiler_cap = (outputlib.views.node(results, 'boiler')[
        'scalars'][(('boiler', 'heat'), 'invest')])

    ##########################################################################
    # Display analysis
    ##########################################################################

    print('-- Consumption, Shortage and Excess Energy --')
    print("Total shortage electr.: {:.3f}".
          format(shortage_electricity.flow.sum()/1e3),"GWh_el")
    print("Total shortage heat:    {:.3f}".
        format(shortage_heat.flow.sum()/1e3), "GWh_el")
    print("Total excess electr.:   {:.2f}".
        format(excess_electricity.flow.sum()/1e3), "GWh_el")
    print("Total excess heat.:     {:.2f}".
        format(excess_heat.flow.sum()/1e3), "GWh_el")
    print("Total electrical consumption (neg. residual load):  {:.2f}".
        format(residual_load.flow.sum() / 1e3), "GWh_el")
    print(residual_load[battery_charge > 0.5].flow.sum()/1e3)
    print("Consumed electr by charging EES: %3.2f GWh_el"
          % (stored_el.flow.sum()/1e3))
    print("Total gas consumption:  {:.2f}".
          format(gas_consumption.flow.sum()/1e3), "GWh_th")
    print("Total el demand:  {:.2f}".format(demand_el.flow.sum()/1e3),
          "GWh_th")
    print("Total heat demand:  {:.2f}".format(demand_th.flow.sum()/1e3),
          "GWh_th")
    print('--- Efficiencies ---')
    print('Electr. efficiency CHP: eta_min= {:2.4f}, '
          'eta_max= {:2.4f}'.format(eta_el.flow.min(), eta_el.flow.max()))
    print('Energetic Efficiency CHP: omega_min= {:2.4f}, omega_max= {:2.4f}'.
        format(omega_CHP.flow.min(), omega_CHP.flow.max()))
    print('Energetic Efficiency (whole year): {:2.4f}'.format(omega_CHP_sum))
    print('-- Hours in simulated period --')
    print(CHP_01_electricity.flow.count(), "h")
    print('Hours of electric. shortage :', aux_shortage_df[aux_shortage_df > 0].
        flow.count(),"h")
    print('-- Hours of Operation --')
    print('CHP_01:', aux_chp_01_df[aux_chp_01_df > 0.2].flow.count(), "h")
    print('Boiler:', boiler[boiler > 0.2].flow.count(), "h")
    print('P2H:', P2H_th[P2H_th > 0.1].flow.count(), "h")
    print('Hours of charging TES: ', TES_charge[TES_charge > 0.1].
          flow.count(), "h")
    print('Hours of discharging TES: ', TES_discharge[TES_discharge > 0.1].
          flow.count(), "h")
    print('Hours of charging EES: ', battery_charge[battery_charge > 0.1].
          flow.count(), "h")
    print('Hours of discharging EES: ', battery_discharge[
        battery_discharge > 0.1].flow.count(), "h")
    print('Hours of feed in (in to the grid): ', demand_el[
        demand_el > 0.1].flow.count(), "h")
    print('-- Installed capacity of thermal energy storage (TES) --')
    print(storage_th_cap, "MWh")
    print("Maximum discharge capacity: ", TES_discharge.flow.max(), "MW_el")
    print('-- Installed capacity of electrical energy storage (EES) --')
    print(storage_el_cap, "MWh")
    print("Maximum discharge capacity: ", battery_discharge.
          flow.max(), "MW_el")
    print('-- Installed capacity of CHP --')
    print(chp_cap, "MW_el")
    print('-- Installed capacity of conventional boiler --')
    print(boiler_cap, "MW_th")
    print('-- Installed capacity of P2H --')
    print(P2H_cap, "MW_th")
    print('*** End analysis  *** ')

    ###########################################################################
    # Save data
    ###########################################################################

    # Save investment results, i.e., installed capacity (MWh) and power (MW)
    d = {'id': [variation_nr],
         'CHP_cap_MW_el': [chp_cap],
         'TES_cap_MWh': [storage_th_cap],
         'EES_cap_MWh': [storage_el_cap],
         'P2H_cap_MW_th': [P2H_cap],
         'Boiler_cap_MW_th': [boiler_cap],
         'gas_comsumption_MWh': [gas_consumption.flow.sum()]}
    invest_results = pd.DataFrame(data=d, index=[variation_nr])
    print('invest results: ')
    print(invest_results)
    if cfg['price_el_quadratic']:
        invest_results.to_csv('../results/optimisation_results/data/'
                              'quadratic_price_relationship/'
                              'invest_results_{0}.csv'.format(variation_nr))
    if not cfg['price_el_quadratic']:
        invest_results.to_csv('../results/optimisation_results/data/'
                              'linear_price_relationship/'
                              'invest_results_{0}.csv'.format(variation_nr))

    # Save specific time series for plotting and postprocessing
    if cfg['run_single_scenario']:
        zeitreihen = pd.DataFrame()
        zeitreihen['Strombedarf'] = demand_el.flow
        zeitreihen['Waermebedarf'] = demand_th.flow
        zeitreihen['P2H_th'] = P2H_th.flow
        zeitreihen['CHP_01_th'] = CHP_01_heat.flow
        zeitreihen['CHPs_th'] = CHP_01_heat
        zeitreihen['CHP_01_el'] = CHP_01_electricity
        zeitreihen['CHPs_el'] = CHP_01_electricity
        zeitreihen['Kessel'] = boiler
        zeitreihen['negative_Residuallast_MW_el'] = residual_load.flow
        zeitreihen['Fuellstand_Waermespeicher_relativ'] = TES_soc_rel
        zeitreihen['Waermespeicher_beladung'] = TES_charge
        zeitreihen['Waermespeicher_entladung'] = TES_discharge
        zeitreihen['Fuellstand_Batterie_relativ'] = battery_soc_rel
        zeitreihen['batterie_beladen'] = battery_charge
        zeitreihen['batterie_entladen'] = battery_discharge
        if cfg['price_el_quadratic'] == False:
            zeitreihen.to_csv('../results/data_postprocessed/'
                              'linear_price_relationship/zeitreihen_A{0}.csv'.
                              format(variation_nr))
        if cfg['price_el_quadratic'] == True:
            zeitreihen.to_csv('../results/data_postprocessed/'
                              'quadratic_price_relationship/'
                              'zeitreihen_A{0}.csv'.format(variation_nr))

        #######################################################################
        # Plots
        #######################################################################

        beuth_red = (239 / 255, 24 / 255, 30 / 255)
        beuth_col_1 = (190 / 255, 226 / 255, 226 / 255)
        beuth_col_2 = (57 / 255, 183 / 255, 188 / 255)
        beuth_col_3 = (0 / 255, 152 / 255, 161 / 255)

        fig3, ax3 = plt.subplots(2, 2, sharey=True, sharex=True)
        size__01 = 5
        size_02 = 5
        fig3.subplots_adjust(hspace=.3)
        ax3[0, 0].grid(zorder=2)
        ax3[0, 1].grid(zorder=2)
        ax3[1, 0].grid(zorder=2)
        ax3[1, 1].grid(zorder=2)
        # Upper left diagram
        ax3[0, 0].scatter(
            x=zeitreihen['Waermebedarf'],
            y=zeitreihen['Strombedarf'],
            label='Total production',
            marker='o',
            s=size__01**2,
            color=beuth_col_2,
            zorder=10
        )
        ax3[0, 0].scatter(
            x=zeitreihen['Waermebedarf'][zeitreihen[
                                             'Waermespeicher_entladung'] > 3],
            y=zeitreihen['Strombedarf'][zeitreihen[
                                            'Waermespeicher_entladung'] > 3],
            label='TES discharge',
            marker='x',
            s=size_02**2,
            color=beuth_red,
            zorder=10
        )
        # Upper right diagram
        ax3[0, 1].scatter(
            x=zeitreihen['Waermebedarf'],
            y=zeitreihen['Strombedarf'],
            label='Total production',
            marker='o',
            s=size__01**2,
            color=beuth_col_2,
            zorder=10
        )
        ax3[0, 1].scatter(
            x=zeitreihen['Waermebedarf'][zeitreihen['batterie_entladen'] > 3],
            y=zeitreihen['Strombedarf'][zeitreihen['batterie_entladen'] > 3],
            label='EES discharge',
            marker='x',
            s=size_02**2,
            color=beuth_red,
            zorder=10
        )
        # Lower left diagram
        ax3[1, 0].scatter(
            x=zeitreihen['Waermebedarf'],
            y=zeitreihen['Strombedarf'],
            label='Total production',
            marker='o',
            s=size__01**2,
            color=beuth_col_2,
            zorder=10
        )
        ax3[1, 0].scatter(
            x=zeitreihen['Waermebedarf'][zeitreihen[
                                             'Waermespeicher_beladung'] > 3],
            y=zeitreihen['Strombedarf'][zeitreihen[
                                            'Waermespeicher_beladung'] > 3],
            label='TES charge',
            marker='x',
            s=size_02**2,
            color=beuth_red,
            zorder=10
        )
        # Lower right diagram
        ax3[1, 1].scatter(
            x=zeitreihen['Waermebedarf'],
            y=zeitreihen['Strombedarf'],
            label='Total production',
            marker='o',
            s=size__01**2,
            color=beuth_col_2,
            zorder=10
        )
        ax3[1, 1].scatter(
            x=zeitreihen['Waermebedarf'][zeitreihen['batterie_beladen'] > 3],
            y=zeitreihen['Strombedarf'][zeitreihen['batterie_beladen'] > 3],
            label='EES charge',
            marker='x',
            s=size_02**2,
            color=beuth_red,
            zorder=10
        )
        # ax3[0, 0].legend()
        ax3_ylim = [-120, 2000]
        ax3_xlim = [0, 1050]
        ax3[0, 0].set_ylim(ax3_ylim)
        ax3[0, 0].set_xlim(ax3_xlim)
        ax3[0, 0].set_title('TES discharge')
        ax3[0, 1].set_title('EES discharge')
        ax3[1, 0].set_title('TES charge')
        ax3[1, 1].set_title('EES charge')
        ax3[1, 1].set_xlabel('District Heating '
                             'Distribution ($\mathrm{MWh_{th}}$)')
        ax3[1, 0].set_xlabel('District Heating '
                             'Distribution ($\mathrm{MWh_{th}}$)')
        ax3[0, 0].set_ylabel('Power Supply ($\mathrm{MWh_{el}}$)')
        ax3[1, 0].set_ylabel('Power Supply ($\mathrm{MWh_{el}}$)')
        if cfg['price_el_quadratic'] == True:
            plt.savefig(
                '../results/plots/quadratic_price_relationship/'
                'scatter_plot_store_sc_{0}.png'.format(variation_nr),
                dpi=300
            )
        if cfg['price_el_quadratic'] == False:
            plt.savefig(
                '../results/plots/linear_price_relationship/'
                'scatter_plot_store_sc_{0}.png'.format(variation_nr),
                dpi=300
            )

        # Plot power supply over electricity price
        plt.style.use('ggplot')
        if cfg['price_el_quadratic'] == False:
            el_price_aux = param_value['el_price']*-1 * data['demand_el']
            el_price = el_price_aux[0:8759]
        if cfg['price_el_quadratic'] == True:
            el_price_aux = param_value['el_price']*-1 \
                           * param_value['price_factor_sqr'] \
                           * data['demand_el'] ** 2
            el_price = el_price_aux[0:8759]

        fig4, ax4 = plt.subplots()
        power_supply = (zeitreihen['Strombedarf'][0:8759]
                        - zeitreihen['negative_Residuallast_MW_el'][0:8759])
        ax4.scatter(
            x=el_price,
            y=power_supply.clip(lower=0),
            color=beuth_col_3
        )
        ax4.scatter(
            x=el_price,
            y=power_supply,
            color=beuth_red,
            marker='x'
        )
        ax4.set_ylim([-100, 1950])
        ax4.set_xlim([-10, 220])
        ax4.set_ylabel('Power supply ($\mathrm{MWh_{el}})$')
        ax4.set_xlabel('Electricity price ($\mathrm{EUR/MWh_{el}}$)')
        if cfg['price_el_quadratic'] == True:
            plt.savefig(
                '../results/plots/quadratic_price_relationship/'
                'el_supply_over_price_{0}.png'.format(variation_nr),
                dpi=300
            )
        if cfg['price_el_quadratic'] == False:
            plt.savefig(
                '../results/plots/linear_price_relationship/'
                'el_supply_over_price_{0}.png'.format(variation_nr),
                dpi=300
            )
