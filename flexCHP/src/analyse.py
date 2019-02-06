###############################################################################
# imports
###############################################################################

import oemof.solph as solph
import oemof.outputlib as outputlib

import os
import pandas as pd
import pprint as pp
import matplotlib
import numpy as np
import matplotlib.pyplot as plt
import yaml


def analyse_and_print(config_path, scenario_nr):

    with open(config_path, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))

    file_path_param_01 = abs_path + cfg['parameters_energy_system'][scenario_nr-1]
    file_path_param_02 = abs_path + cfg['parameters_all_energy_systems']
    param_df_01 = pd.read_csv(file_path_param_01, index_col=1)
    param_df_02 = pd.read_csv(file_path_param_02, index_col=1)
    param_df = pd.concat([param_df_01, param_df_02])
    param_value = param_df['value']

    energysystem = solph.EnergySystem()
    energysystem.restore(dpath=abs_path + "/results/optimisation_results/dumps",
                         filename=cfg['filename_dumb'] + '_scenario_{0}.oemof'.format(scenario_nr))

    results = energysystem.results['main']

    print('\n *** Analysis of scenario {} *** '.format(scenario_nr))

    electricity_bus = outputlib.views.node(results, 'electricity')
    print('electricity bus: sums in GWh_el')
    print(electricity_bus['sequences'].sum(axis=0)/1e3)

    heat_bus = outputlib.views.node(results, 'heat')
    print('heat bus: sums in GWh_th')
    print(heat_bus['sequences'].sum(axis=0)/1e3)

    string_results = outputlib.views.convert_keys_to_strings(energysystem.results['main'])

    # Collecting results for specific components and flows
    CHP_01_heat = string_results[('CHP_01', 'heat')]['sequences']
    CHP_01_electricity = string_results[('CHP_01', 'electricity')]['sequences']
    boiler = string_results[('boiler', 'heat')]['sequences']
    P2H_th = string_results['P2H', 'heat']['sequences']
    if param_value['nom_capacity_storage_th'] > 0:
        TES_discharge = string_results['storage_th', 'heat']['sequences']
        TES_charge = string_results['heat', 'storage_th']['sequences']
        TES_soc = string_results['storage_th', 'None']['sequences']  # State of charge in [MWh_th]
        TES_soc_rel = string_results['storage_th', 'None']['sequences']/\
                      string_results['storage_th', 'None']['sequences'].max()*100  # State of charge in [%]
    if param_value['nom_capacity_storage_el'] > 0:
        battery_discharge = string_results['storage_el', 'electricity']['sequences']
        battery_charge = string_results['electricity', 'storage_el']['sequences']
        battery_soc = string_results['storage_el', 'None']['sequences']
        battery_soc_rel = string_results['storage_el', 'None']['sequences'] / string_results['storage_el', 'None'][
            'sequences'].max() * 100
    shortage_electricity = string_results['shortage_bel', 'electricity']['sequences']
    shortage_heat = string_results['shortage_bth', 'heat']['sequences']
    excess_electricity = string_results['electricity', 'excess_bel']['sequences']
    excess_heat = string_results['heat', 'excess_bth']['sequences']
    gas_consumption = string_results['rgas', 'natural_gas']['sequences']
    demand_th = string_results['heat', 'demand_th']['sequences']
    demand_el = string_results['electricity', 'demand_el']['sequences']
#
    print('-- Consumption, Shortage and Excess Energy --')
    print("Total shortage electr.: {:.3f}".format(shortage_electricity.flow.sum()/1e3), "GWh_el")
    print("Total shortage heat:    {:.3f}".format(shortage_heat.flow.sum()/1e3), "GWh_el")
    print("Total excess electr.:   {:.2f}".format(excess_electricity.flow.sum()/1e3), "GWh_el")
    print("Total excess heat.:     {:.2f}".format(excess_heat.flow.sum()/1e3), "GWh_el")
    print("Total gas consumption:  {:.2f}".format(gas_consumption.flow.sum()/1e3), "GWh_th")
    print("Total el demand:  {:.2f}".format(demand_el.flow.sum()/1e3), "GWh_th")
    print("Total heat demand:  {:.2f}".format(demand_th.flow.sum()/1e3), "GWh_th")

    gas_consumption_CHP = string_results['natural_gas', 'CHP_01']['sequences']
    eta_el = string_results[('CHP_01', 'electricity')]['sequences']/gas_consumption_CHP
    omega_CHP = (string_results[('CHP_01', 'electricity')]['sequences']
                 + string_results[('CHP_01', 'heat')]['sequences'])/gas_consumption_CHP
    eta_el_sum = string_results[('CHP_01', 'electricity')]['sequences'].sum()/gas_consumption_CHP.sum()
    omega_CHP_sum = (string_results[('CHP_01', 'electricity')]['sequences'].flow.sum()
                  + string_results[('CHP_01', 'heat')]['sequences'].flow.sum())/gas_consumption_CHP.flow.sum()

    print('--- Wirkungsgrad ---')
    print('Elektr. Nettowirkungsgrad des CHP: eta_min= {:2.4f}, eta_max= {:2.4f}'.format(eta_el.flow.min(), eta_el.flow.max()))
    print('Gesamtwirkungsgrad des CHP: omega_min= {:2.4f}, omega_max= {:2.4f}'.format(omega_CHP.flow.min(), omega_CHP.flow.max()))
    print('Jahresnutzungsgrad: {:2.4f}'.format(omega_CHP_sum))
    print('-- Anzahl der Stunden im betrachteten Zeitraum --')
    print(CHP_01_electricity.flow.count(), "h")
    print('-- Stunden mit eingeschränkter Versorgung (Strom) --')
    aux_shortage_df = shortage_heat.add(shortage_electricity)
    print('Hours of shortage:', aux_shortage_df[aux_shortage_df > 0].flow.count(), "h")
    print('-- Betriebsstunden im betrachteten Zeitraum --')
    aux_chp_01_df = CHP_01_heat.add(CHP_01_electricity)
    print('CHP_01:', aux_chp_01_df[aux_chp_01_df > 0].flow.count(), "h")
    print('Boiler:', boiler[boiler > 0].flow.count(), "h")
    print('*** End analysis of scenario {} *** '.format(scenario_nr))

    # Export time series of results for plotting (make_plots) and external analysis (e.g. in Excel)
    zeitreihen = pd.DataFrame()
    zeitreihen['Strombedarf'] = demand_el.flow
    zeitreihen['Waermebedarf'] = demand_th.flow
    zeitreihen['CHP_01_th'] = CHP_01_heat.flow
    zeitreihen['CHPs_th'] = CHP_01_heat
    zeitreihen['CHP_01_el'] = CHP_01_electricity
    zeitreihen['CHPs_el'] = CHP_01_electricity
    zeitreihen['Kessel'] = boiler
    zeitreihen['negative_Residuallast_MW_el'] = P2H_th/param_value['conversion_factor_p2h']
    if scenario_nr == 2:
        zeitreihen['Fuellstand_Waermespeicher_relativ'] = TES_soc_rel
        zeitreihen['Waermespeicher_beladung'] = TES_charge
        zeitreihen['Waermespeicher_entladung'] = TES_discharge
    if scenario_nr == 3:
        zeitreihen['Fuellstand_Batterie_relativ'] = battery_soc_rel
        zeitreihen['batterie_beladen'] = battery_charge
        zeitreihen['batterie_entladen'] = battery_discharge
    zeitreihen.to_csv('../results/data_postprocessed/zeitreihen_A{0}.csv'.format(scenario_nr))


def make_plots():
    # Colors
    beuth_red = (239 / 255, 24 / 255, 30 / 255)
    beuth_col_1 = (190 / 255, 226 / 255, 226 / 255)
    beuth_col_2 = (57 / 255, 183 / 255, 188 / 255)
    beuth_col_3 = (0 / 255, 152 / 255, 161 / 255)

    zeitreihen_a1 = pd.read_csv('../results/data_postprocessed/zeitreihen_A1.csv')
    zeitreihen_a2 = pd.read_csv('../results/data_postprocessed/zeitreihen_A2.csv')
    zeitreihen_a3 = pd.read_csv('../results/data_postprocessed/zeitreihen_A3.csv')

    # Comparision of CHP operation in all three scenarios
    fig3, ax3 = plt.subplots(1, 3, sharey=True, figsize=(12, 6))
    ax3[0].scatter(x=zeitreihen_a1['CHPs_th'],
                   y=zeitreihen_a1['CHPs_el'],
                   marker='.',
                   c=[beuth_col_3],
                   zorder=10,
                   label='ohne Speicher')
    ax3[0].grid(color='grey',  # beuth_col_2,
                linestyle='-',
                linewidth=0.5,
                zorder=1)
    ax3[1].scatter(x=zeitreihen_a2['CHPs_th'],
                   y=zeitreihen_a2['CHPs_el'],
                   marker='.',
                   c=[beuth_col_3],
                   zorder=10,
                   label='mit Wärmespeicher')
    ax3[1].grid(color='grey',  # beuth_col_2,
                linestyle='-',
                linewidth=0.5,
                zorder=1)
    ax3[2].scatter(x=zeitreihen_a3['CHPs_th'],
                   y=zeitreihen_a3['CHPs_el'],
                   marker='.',
                   c=[beuth_col_3],
                   zorder=10,
                   label='mit Stromspeicher')
    ax3[2].grid(color='grey',  # beuth_col_2,
                linestyle='-',
                linewidth=0.5,
                zorder=1)
    ax3[0].set_ylim([-20, 1020])
    ax3[0].tick_params(axis='both', which='major', labelsize=16)
    ax3[1].tick_params(axis='both', which='major', labelsize=16)
    ax3[2].tick_params(axis='both', which='major', labelsize=16)
    ax3[0].set_ylabel('Elektrische Leistung in $\mathrm{MW_{el}}$', fontsize=20)
    ax3[1].set_xlabel('Wärmeleistung in $\mathrm{MW_{th}}$', fontsize=20)
    plt.savefig('../results/plots/scatter_plot_all3scenarios.png', dpi=300)

    # Influence of Thermal Energy Storage (TES) charging
    fig4, ax4 = plt.subplots()
    produktion_el_a1 = zeitreihen_a1['CHPs_el'].add(-1 * zeitreihen_a1['negative_Residuallast_MW_el'])
    produktion_th_a1 = zeitreihen_a1['CHPs_th'].add(zeitreihen_a1['Kessel']).add(
        zeitreihen_a1['negative_Residuallast_MW_el'] * 0.99)
    produktion_el_a2 = zeitreihen_a2['CHPs_el'].add(-1 * zeitreihen_a2['negative_Residuallast_MW_el'])
    produktion_th_a2 = zeitreihen_a2['CHPs_th'].add(zeitreihen_a2['Kessel']).add(
        zeitreihen_a2['negative_Residuallast_MW_el'] * 0.99)
    ax4.scatter(x=produktion_th_a1,
                y=produktion_el_a1,
                marker='o',
                c=[beuth_col_2],
                zorder=1,
                label=None,
                alpha=1)
    ax4.grid(color='grey',
             linestyle='-',
             linewidth=0.5,
             zorder=2)
    ax4.scatter(x=produktion_th_a1[zeitreihen_a2['Waermespeicher_beladung'] > 0][:-10],
                y=produktion_el_a1[zeitreihen_a2['Waermespeicher_beladung'] > 0][:-10],
                marker='|',
                s=20,
                c=[beuth_col_3],
                zorder=10,
                alpha=1,
                label='ohne Speicher')
    ax4.scatter(x=produktion_th_a2[zeitreihen_a2['Waermespeicher_beladung'] > 0][:-10],
                y=produktion_el_a2[zeitreihen_a2['Waermespeicher_beladung'] > 0][:-10],
                marker='|',
                s=20,
                c=[beuth_red],
                zorder=10,
                alpha=1,
                label='mit Wärmespeicher (beladen)')
    ax4.set_ylim([-250, 1050])
    ax4.legend(loc=4, fontsize=12)
    ax4.set_ylabel('Elektrische Leistung in $\mathrm{MW_{el}}$', fontsize=12)
    ax4.set_xlabel('Wärmeleistung in $\mathrm{MW_{th}}$', fontsize=12)
    plt.savefig('../results/plots/scatter_plot_TES_charge_influence.png', dpi=300)

    # Influence of Thermal Energy Storage (TES) discharging
    fig5, ax5 = plt.subplots()
    produktion_el_a1 = zeitreihen_a1['CHPs_el'].add(-1 * zeitreihen_a1['negative_Residuallast_MW_el'])
    produktion_th_a1 = zeitreihen_a1['CHPs_th'].add(zeitreihen_a1['Kessel']).add(
        zeitreihen_a1['negative_Residuallast_MW_el'] * 0.99)
    produktion_el_a2 = zeitreihen_a2['CHPs_el'].add(-1 * zeitreihen_a2['negative_Residuallast_MW_el'])
    produktion_th_a2 = zeitreihen_a2['CHPs_th'].add(zeitreihen_a2['Kessel']).add(
        zeitreihen_a2['negative_Residuallast_MW_el'] * 0.99)
    ax5.scatter(x=produktion_th_a1,
                y=produktion_el_a1,
                marker='o',
                c=[beuth_col_2],
                zorder=1,
                label=None,
                alpha=1)
    ax5.grid(color='grey',
             linestyle='-',
             linewidth=0.5,
             zorder=2)
    ax5.scatter(x=produktion_th_a1[zeitreihen_a2['Waermespeicher_entladung'] > 0][10:],
                y=produktion_el_a1[zeitreihen_a2['Waermespeicher_entladung'] > 0][10:],
                marker='|',
                s=20,
                c=[beuth_col_3],
                zorder=10,
                alpha=1,
                label='ohne Speicher')
    ax5.scatter(x=produktion_th_a2[zeitreihen_a2['Waermespeicher_entladung'] > 0][10:],
                y=produktion_el_a2[zeitreihen_a2['Waermespeicher_entladung'] > 0][10:],
                marker='|',
                s=20,
                c=[beuth_red],
                zorder=10,
                alpha=1,
                label='mit Wärmespeicher (entladen)')
    ax5.set_ylim([-250, 1050])
    ax5.legend(loc=4, fontsize=12)
    ax5.set_ylabel('Elektrische Leistung in $\mathrm{MW_{el}}$', fontsize=12)
    ax5.set_xlabel('Wärmeleistung in $\mathrm{MW_{th}}$', fontsize=12)
    plt.savefig('../results/plots/scatter_plot_TES_discharge_influence.png', dpi=300)

    # Influence of Electrical Energy Storage (EES) charging
    fig6, ax6 = plt.subplots()
    produktion_el_a3 = zeitreihen_a3['CHPs_el'].add(-1 * zeitreihen_a3['negative_Residuallast_MW_el'])
    produktion_th_a3 = zeitreihen_a3['CHPs_th'].add(zeitreihen_a3['Kessel']).add(
        zeitreihen_a3['negative_Residuallast_MW_el'] * 0.99)
    ax6.scatter(x=produktion_th_a1,
                y=produktion_el_a1,
                marker='o',
                c=[beuth_col_2],
                zorder=1,
                label=None,
                alpha=1)
    ax6.grid(color='grey',
             linestyle='-',
             linewidth=0.5,
             zorder=2)
    ax6.scatter(x=produktion_th_a1[zeitreihen_a3['batterie_beladen'] > 0][:-10],
                y=produktion_el_a1[zeitreihen_a3['batterie_beladen'] > 0][:-10],
                marker='_',
                s=20,
                c=[beuth_col_3],
                zorder=10,
                alpha=1,
                label='ohne Speicher')
    ax6.scatter(x=produktion_th_a3[zeitreihen_a3['batterie_beladen'] > 0][:-10],
                y=produktion_el_a3[zeitreihen_a3['batterie_beladen'] > 0][:-10],
                marker='_',
                s=20,
                c=[beuth_red],
                zorder=10,
                alpha=1,
                label='mit Stromspeicher')
    ax6.set_ylim([-250, 1050])
    ax6.legend(loc=4, fontsize=12)
    ax6.set_ylabel('Elektrische Leistung in $\mathrm{MW_{el}}$', fontsize=12)
    ax6.set_xlabel('Wärmeleistung in $\mathrm{MW_{th}}$', fontsize=12)
    plt.savefig('../results/plots/scatter_plot_EES_charge_influence.png', dpi=300)

    # Influence of Electrical Energy Storage (EES) discharging
    fig7, ax7 = plt.subplots()
    ax7.scatter(x=produktion_th_a1,
                y=produktion_el_a1,
                marker='o',
                c=[beuth_col_2],
                zorder=1,
                label=None,
                alpha=1)
    ax7.grid(color='grey',
             linestyle='-',
             linewidth=0.5,
             zorder=2)
    ax7.scatter(x=produktion_th_a1[zeitreihen_a3['batterie_entladen'] > 0][10:],
                y=produktion_el_a1[zeitreihen_a3['batterie_entladen'] > 0][10:],
                marker='_',
                s=20,
                c=[beuth_col_3],
                zorder=10,
                alpha=1,
                label='ohne Speicher')
    ax7.scatter(x=produktion_th_a3[zeitreihen_a3['batterie_entladen'] > 0][10:],
                y=produktion_el_a3[zeitreihen_a3['batterie_entladen'] > 0][10:],
                marker='_',
                s=20,
                c=[beuth_red],
                zorder=10,
                alpha=1,
                label='mit Stromspeicher')
    ax7.set_ylim([-250, 1050])
    ax7.legend(loc=4, fontsize=12)
    ax7.set_ylabel('Elektrische Leistung in $\mathrm{MW_{el}}$', fontsize=12)
    ax7.set_xlabel('Wärmeleistung in $\mathrm{MW_{th}}$', fontsize=12)
    plt.savefig('../results/plots/scatter_plot_EES_discharge_influence.png', dpi=300)

