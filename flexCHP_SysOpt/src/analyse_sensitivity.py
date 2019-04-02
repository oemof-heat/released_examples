'''
Analyse results of the parameter variation and make plots.
'''

__copyright__ = "Beuth Hochschule für Technik Berlin, Reiner Lemoine Institut"
__license__ = "GPLv3"
__author__ = "jakob-wo (jakob.wolf@beuth-hochschule.de)"

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import yaml
import os


def analyse_sensitivity(config_path):

    with open(config_path, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    data = pd.DataFrame()

    # Read and join invest results (system designs) from parameter variations
    for i in range(17):
        variation_nr = i
        if not cfg['price_el_quadratic']:
            filepath = '../results/optimisation_results/data/' \
                       'linear_price_relationship/invest_results_' \
                       + str(variation_nr) + '.csv'
        if cfg['price_el_quadratic']:
            filepath = '../results/optimisation_results/data/' \
                       'quadratic_price_relationship/invest_results_' \
                       + str(variation_nr) + '.csv'
        if i == 0:
            data = pd.read_csv(filepath)
        else:
            data = pd.concat([data, pd.read_csv(filepath)], ignore_index=False)

    # Display invest results
    print("")
    print("Results of all parameter variations:")
    print(data)

    # Save invest results
    if cfg['price_el_quadratic'] == False:
        data.to_csv('../results/data_postprocessed/'
                    'linear_price_relationship/'
                    'sensitivity_results_linear.csv')
    if cfg['price_el_quadratic'] == True:
        data.to_csv('../results/data_postprocessed/'
                    'quadratic_price_relationship/'
                    'sensitivity_results_quad.csv')

    ##########################################################################
    # Collect and join values for plotting
    ##########################################################################

    # Variation of EES CAPEX
    y_EES_capex_1 = [data.iloc[1]['EES_cap_MWh'],
                     data.iloc[2]['EES_cap_MWh'],
                     data.iloc[0]['EES_cap_MWh'],
                     data.iloc[3]['EES_cap_MWh'],
                     data.iloc[4]['EES_cap_MWh']]
    y_EES_capex_2 = [data.iloc[1]['TES_cap_MWh'],
                     data.iloc[2]['TES_cap_MWh'],
                     data.iloc[0]['TES_cap_MWh'],
                     data.iloc[3]['TES_cap_MWh'],
                     data.iloc[4]['TES_cap_MWh']]
    y_EES_capex_3 = [data.iloc[1]['CHP_cap_MW_el'],
                     data.iloc[2]['CHP_cap_MW_el'],
                     data.iloc[0]['CHP_cap_MW_el'],
                     data.iloc[3]['CHP_cap_MW_el'],
                     data.iloc[4]['CHP_cap_MW_el']]
    y_EES_capex_4 = [data.iloc[1]['Boiler_cap_MW_th'],
                     data.iloc[2]['Boiler_cap_MW_th'],
                     data.iloc[0]['Boiler_cap_MW_th'],
                     data.iloc[3]['Boiler_cap_MW_th'],
                     data.iloc[4]['Boiler_cap_MW_th']]
    y_EES_capex_5 = [data.iloc[1]['P2H_cap_MW_th'],
                     data.iloc[2]['P2H_cap_MW_th'],
                     data.iloc[0]['P2H_cap_MW_th'],
                     data.iloc[3]['P2H_cap_MW_th'],
                     data.iloc[4]['P2H_cap_MW_th']]
    y_EES_capex_6 = [data.iloc[1]['gas_comsumption_MWh']/1e3,
                     data.iloc[2]['gas_comsumption_MWh']/1e3,
                     data.iloc[0]['gas_comsumption_MWh']/1e3,
                     data.iloc[3]['gas_comsumption_MWh']/1e3,
                     data.iloc[4]['gas_comsumption_MWh']/1e3]

    # Variation of TES CAPEX
    i_01 = 13
    i_02 = 14
    i_03 = 15
    i_04 = 16
    y_TES_capex_1 = [data.iloc[i_01]['EES_cap_MWh'],
                     data.iloc[i_02]['EES_cap_MWh'],
                     data.iloc[0]['EES_cap_MWh'],
                     data.iloc[i_03]['EES_cap_MWh'],
                     data.iloc[i_04]['EES_cap_MWh']]
    y_TES_capex_2 = [data.iloc[i_01]['TES_cap_MWh'],
                     data.iloc[i_02]['TES_cap_MWh'],
                     data.iloc[0]['TES_cap_MWh'],
                     data.iloc[i_03]['TES_cap_MWh'],
                     data.iloc[i_04]['TES_cap_MWh']]
    y_TES_capex_3 = [data.iloc[i_01]['CHP_cap_MW_el'],
                     data.iloc[i_02]['CHP_cap_MW_el'],
                     data.iloc[0]['CHP_cap_MW_el'],
                     data.iloc[i_03]['CHP_cap_MW_el'],
                     data.iloc[i_04]['CHP_cap_MW_el']]
    y_TES_capex_4 = [data.iloc[i_01]['Boiler_cap_MW_th'],
                     data.iloc[i_02]['Boiler_cap_MW_th'],
                     data.iloc[0]['Boiler_cap_MW_th'],
                     data.iloc[i_03]['Boiler_cap_MW_th'],
                     data.iloc[i_04]['Boiler_cap_MW_th']]
    y_TES_capex_5 = [data.iloc[i_01]['P2H_cap_MW_th'],
                     data.iloc[i_02]['P2H_cap_MW_th'],
                     data.iloc[0]['P2H_cap_MW_th'],
                     data.iloc[i_03]['P2H_cap_MW_th'],
                     data.iloc[i_04]['P2H_cap_MW_th']]
    y_TES_capex_6 = [data.iloc[i_01]['gas_comsumption_MWh']/1e3,
                     data.iloc[i_02]['gas_comsumption_MWh']/1e3,
                     data.iloc[0]['gas_comsumption_MWh']/1e3,
                     data.iloc[i_03]['gas_comsumption_MWh']/1e3,
                     data.iloc[i_04]['gas_comsumption_MWh']/1e3]

    # Variation of electricity price
    n_01 = 5
    n_02 = 6
    n_03 = 7
    n_04 = 8
    y_el_price_1 = [data.iloc[n_01]['EES_cap_MWh'],
                    data.iloc[n_02]['EES_cap_MWh'],
                    data.iloc[0]['EES_cap_MWh'],
                    data.iloc[n_03]['EES_cap_MWh'],
                    data.iloc[n_04]['EES_cap_MWh']]
    y_el_price_2 = [data.iloc[n_01]['TES_cap_MWh'],
                    data.iloc[n_02]['TES_cap_MWh'],
                    data.iloc[0]['TES_cap_MWh'],
                    data.iloc[n_03]['TES_cap_MWh'],
                    data.iloc[n_04]['TES_cap_MWh']]
    y_el_price_3 = [data.iloc[n_01]['CHP_cap_MW_el'],
                    data.iloc[n_02]['CHP_cap_MW_el'],
                    data.iloc[0]['CHP_cap_MW_el'],
                    data.iloc[n_03]['CHP_cap_MW_el'],
                    data.iloc[n_04]['CHP_cap_MW_el']]
    y_el_price_4 = [data.iloc[n_01]['Boiler_cap_MW_th'],
                    data.iloc[n_02]['Boiler_cap_MW_th'],
                    data.iloc[0]['Boiler_cap_MW_th'],
                    data.iloc[n_03]['Boiler_cap_MW_th'],
                    data.iloc[n_04]['Boiler_cap_MW_th']]
    y_el_price_5 = [data.iloc[n_01]['P2H_cap_MW_th'],
                    data.iloc[n_02]['P2H_cap_MW_th'],
                    data.iloc[0]['P2H_cap_MW_th'],
                    data.iloc[n_03]['P2H_cap_MW_th'],
                    data.iloc[n_04]['P2H_cap_MW_th']]
    y_el_price_6 = [data.iloc[n_01]['gas_comsumption_MWh']/1e3,
                    data.iloc[n_02]['gas_comsumption_MWh']/1e3,
                    data.iloc[0]['gas_comsumption_MWh']/1e3,
                    data.iloc[n_03]['gas_comsumption_MWh']/1e3,
                    data.iloc[n_04]['gas_comsumption_MWh']/1e3]

    # Variation of gas price
    k_01 = 9
    k_02 = 10
    k_03 = 11
    k_04 = 12
    y_gas_price_1 = [data.iloc[k_01]['EES_cap_MWh'],
                     data.iloc[k_02]['EES_cap_MWh'],
                     data.iloc[0]['EES_cap_MWh'],
                     data.iloc[k_03]['EES_cap_MWh'],
                     data.iloc[k_04]['EES_cap_MWh']]
    y_gas_price_2 = [data.iloc[k_01]['TES_cap_MWh'],
                     data.iloc[k_02]['TES_cap_MWh'],
                     data.iloc[0]['TES_cap_MWh'],
                     data.iloc[k_03]['TES_cap_MWh'],
                     data.iloc[k_04]['TES_cap_MWh']]
    y_gas_price_3 = [data.iloc[k_01]['CHP_cap_MW_el'],
                     data.iloc[k_02]['CHP_cap_MW_el'],
                     data.iloc[0]['CHP_cap_MW_el'],
                     data.iloc[k_03]['CHP_cap_MW_el'],
                     data.iloc[k_04]['CHP_cap_MW_el']]
    y_gas_price_4 = [data.iloc[k_01]['Boiler_cap_MW_th'],
                     data.iloc[k_02]['Boiler_cap_MW_th'],
                     data.iloc[0]['Boiler_cap_MW_th'],
                     data.iloc[k_03]['Boiler_cap_MW_th'],
                     data.iloc[k_04]['Boiler_cap_MW_th']]
    y_gas_price_5 = [data.iloc[k_01]['P2H_cap_MW_th'],
                     data.iloc[k_02]['P2H_cap_MW_th'],
                     data.iloc[0]['P2H_cap_MW_th'],
                     data.iloc[k_03]['P2H_cap_MW_th'],
                     data.iloc[k_04]['P2H_cap_MW_th']]
    y_gas_price_6 = [data.iloc[k_01]['gas_comsumption_MWh']/1e3,
                     data.iloc[k_02]['gas_comsumption_MWh']/1e3,
                     data.iloc[0]['gas_comsumption_MWh']/1e3,
                     data.iloc[k_03]['gas_comsumption_MWh']/1e3,
                     data.iloc[k_04]['gas_comsumption_MWh']/1e3]

    ###########################################################################
    # Plots
    ###########################################################################

    # Colors
    beuth_red = (239/255, 24/255, 30/255)
    beuth_col_1 = (190/255, 226/255, 226/255)
    beuth_col_2 = (57/255, 183/255, 188/255)
    beuth_col_3 = (0/255, 152/255, 161/255)
    col_red = '#e41a1c'
    col_blue = '#377eb8'
    col_green = '#4daf4a'
    col_violet = '#984ea3'
    col_orange = '#ff7f00'

    plt.style.use('ggplot')
    x = np.linspace(0.8, 1.2, 5, endpoint=True)
    markersize_all = 9
    ylabel_all = ('Installed Capacity ($\mathrm{MWh}$) \n '
                  'Installed Power ($\mathrm{MW}$)')

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(
        x,
        y_TES_capex_2,
        '-',
        marker='d',
        markersize=markersize_all,
        label='TES')
    ax.plot(
        x,
        y_TES_capex_3,
        '-',
        marker='p',
        markersize=markersize_all,
        label='CHP')
    ax.plot(
        x,
        y_TES_capex_4,
        '-',
        marker='x',
        markersize=markersize_all,
        label='Boiler')
    ax.plot(
        x,
        y_TES_capex_1,
        '-',
        marker='o',
        markersize=markersize_all,
        label='EES')
    ax.plot(
        x,
        y_TES_capex_5,
        '-',
        marker='^',
        markersize=markersize_all,
        label='P2H')
    ax.set_ylabel(ylabel_all)
    ax.set_xlabel('TES CAPEX Variation')
    ax.grid(zorder=1)
    ax.legend(
        bbox_to_anchor=(0., 1.02, 1., .102),
        loc=3,
        ncol=2,
        mode="expand",
        borderaxespad=0.)

    if not cfg['price_el_quadratic']:
        plt.savefig('../results/plots/linear_price_relationship/'
                    'parameter_variation_TES_capex.png', dpi=300)
    if cfg['price_el_quadratic']:
        plt.savefig('../results/plots/quadratic_price_relationship/'
                    'parameter_variation_TES_capex.png', dpi=300)

    fig1, ax1 = plt.subplots(figsize=(8, 6))
    ax1.plot(
        x,
        y_EES_capex_2,
        marker='d',
        markersize=markersize_all,
        label='TES')
    ax1.plot(
        x,
        y_EES_capex_3,
        marker='p',
        markersize=markersize_all,
        label='CHP')
    ax1.plot(
        x,
        y_EES_capex_4,
        marker='x',
        markersize=markersize_all,
        label='Boiler')
    ax1.plot(
        x,
        y_EES_capex_1,
        marker='o',
        markersize=markersize_all,
        label='EES')
    ax1.plot(
        x,
        y_EES_capex_5,
        marker='^',
        markersize=markersize_all,
        label='P2H')
    ax1.set_ylabel(ylabel_all)
    ax1.set_xlabel('EES CAPEX Variation')
    ax1.grid(zorder=1)
    ax1.legend(
        bbox_to_anchor=(0., 1.02, 1., .102),
        loc=3,
        ncol=2,
        mode="expand",
        borderaxespad=0.)

    if not cfg['price_el_quadratic']:
        plt.savefig('../results/plots/linear_price_relationship/'
                    'parameter_variation_EES_capex.png', dpi=300)
    if cfg['price_el_quadratic']:
        plt.savefig('../results/plots/quadratic_price_relationship/'
                    'parameter_variation_EES_capex.png', dpi=300)

    fig2, ax2 = plt.subplots(figsize=(8, 6))
    ax2.plot(
        x,
        y_gas_price_2,
        '-',
        marker='d',
        markersize=markersize_all,
        label='TES')
    ax2.plot(
        x,
        y_gas_price_3,
        '-',
        marker='p',
        markersize=markersize_all,
        label='CHP')
    ax2.plot(
        x,
        y_gas_price_4,
        '-',
        marker='x',
        markersize=markersize_all,
        label='Boiler')
    ax2.plot(
        x,
        y_gas_price_1,
        '-',
        marker='o',
        markersize=markersize_all,
        label='EES')
    ax2.plot(
        x,
        y_gas_price_5,
        '-',
        marker='^',
        markersize=markersize_all,
        label='P2H')
    ax2.set_ylabel(ylabel_all)
    ax2.set_xlabel('Natural Gas Price Variation')
    ax2.grid(zorder=1)
    ax2.legend(
        bbox_to_anchor=(0., 1.02, 1., .102),
        loc=3,
        ncol=2,
        mode="expand",
        borderaxespad=0.)
    if not cfg['price_el_quadratic']:
        plt.savefig('../results/plots/linear_price_relationship/'
                    'parameter_variation_gas_price.png', dpi=300)
    if cfg['price_el_quadratic']:
        plt.savefig('../results/plots/quadratic_price_relationship/'
                    'parameter_variation_gas_price.png', dpi=300)

    fig3, ax3 = plt.subplots(figsize=(8, 6))
    ax3.plot(
        x,
        y_el_price_2,
        '-',
        marker='d',
        markersize=markersize_all,
        label='TES')
    ax3.plot(
        x,
        y_el_price_3,
        '-', marker='p',
        markersize=markersize_all,
        label='CHP')
    ax3.plot(
        x,
        y_el_price_4,
        '-',
        marker='x',
        markersize=markersize_all,
        label='Boiler')
    ax3.plot(
        x,
        y_el_price_1,
        '-',
        marker='o',
        markersize=markersize_all,
        label='EES')
    ax3.plot(
        x,
        y_el_price_5,
        '-',
        marker='^',
        markersize=markersize_all,
        label='P2H')
    ax3.set_ylabel(ylabel_all)
    ax3.set_xlabel('Electricity Price Variation')
    ax3.grid(zorder=1)
    ax3.legend(
        bbox_to_anchor=(0., 1.02, 1., .102),
        loc=3,
        ncol=2,
        mode="expand",
        borderaxespad=0.)
    if not cfg['price_el_quadratic']:
        plt.savefig('../results/plots/linear_price_relationship/'
                    'parameter_variation_el_price.png', dpi=300)
    if cfg['price_el_quadratic']:
        plt.savefig('../results/plots/quadratic_price_relationship/'
                    'parameter_variation_el_price.png', dpi=300)
