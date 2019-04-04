# -*- coding: utf-8 -*-


__copyright__ = "Beuth Hochschule für Technik Berlin, Reiner Lemoine Institut"
__license__ = "GPLv3"
__author__ = "jakob-wo (jakob.wolf@beuth-hochschule.de)"

import pandas as pd
import os
import yaml
import matplotlib.pyplot as plt
import numpy as np


def preprocess_timeseries(config_path):

    with open(config_path, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))

    # Assumptions for load profile projections
    file_name_param = cfg['parameters_load_profile']
    file_path_param = abs_path + file_name_param

    # Technical and economical specifications
    param_df = pd.read_csv(file_path_param, index_col=1)
    param_value = param_df['value']

    # Electricity generation and demand
    file_path_ts_loads_el = abs_path + cfg['time_series_loads_el']
    data = pd.read_csv(file_path_ts_loads_el, parse_dates=['utc_timestamp'])

    # District heating demand
    file_path_ts_loads_heat = abs_path + cfg['time_series_loads_heat']
    xls = pd.ExcelFile(file_path_ts_loads_heat)
    data_heat = pd.read_excel(
        xls, 'Daten', header=None, usecols='E',
        names=['district_heating_profile_2012'])  # Load in %

    load_and_profiles = pd.DataFrame()
    demand_profiles = pd.DataFrame()

    load_and_profiles_szenario2040 = pd.DataFrame()
    coln_time = ['utc_timestamp']
    load_and_profiles[coln_time] = (data[coln_time])
    coln = [
        'utc_timestamp', 'DE_load_entsoe_power_statistics',
        'DE_solar_profile', 'DE_wind_profile',
        'DE_solar_generation_actual', 'DE_wind_generation_actual'
            ]
    load_and_profiles[coln] = data[coln]  # Load in MW
    load_and_profiles_2011 = (
        load_and_profiles[(load_and_profiles['utc_timestamp']
                          > '2010-12-31 23:00:00')
                          & (load_and_profiles['utc_timestamp']
                             < '2012-01-01 00:00:00')])

    load_and_profiles_2012 = (
        load_and_profiles[(load_and_profiles['utc_timestamp']
                          > '2011-12-31 23:00:00')
                          & (load_and_profiles['utc_timestamp']
                              < '2013-01-01 00:00:00')])

    load_and_profiles_2011.reset_index(inplace=True)
    load_and_profiles_2012.reset_index(inplace=True)

    load_and_profiles_szenario2040['utc_timestamp'] = load_and_profiles_2012[
        'utc_timestamp']
    load_and_profiles_szenario2040['load_MW'] = \
        load_and_profiles_2012['DE_load_entsoe_power_statistics']
    load_and_profiles_szenario2040['solar_generation_MW'] = \
        load_and_profiles_2012['DE_solar_profile']\
        * param_value['cap_inst_PV_2040']*1000
    load_and_profiles_szenario2040['wind_generation_MW'] = \
        load_and_profiles_2012['DE_wind_profile'] \
        * (param_value['cap_inst_wind_onshore_2040']
           + param_value['cap_inst_wind_offshore_2040'])*1000
    load_and_profiles_szenario2040['EE_generation_MW'] = \
        load_and_profiles_szenario2040['solar_generation_MW'] \
        + load_and_profiles_szenario2040['wind_generation_MW']
    load_and_profiles_szenario2040['residual_load_MW'] = \
        load_and_profiles_szenario2040['load_MW'] \
        - load_and_profiles_szenario2040['EE_generation_MW']

    print("")
    print("***Characteristics of the created residual load profile "
          "(projection for 2040)***")
    print("Hours of negative residual load:",
          load_and_profiles_szenario2040['residual_load_MW'][(
                  load_and_profiles_szenario2040['residual_load_MW'] < 0)].count(), " h")
    hours_of_pos_resload = load_and_profiles_szenario2040['residual_load_MW'][(
            load_and_profiles_szenario2040['residual_load_MW'] > 0)].count()
    print("Hours of positive residual load:", hours_of_pos_resload, "h")
    print("Hours of residual load equal zero:",
          load_and_profiles_szenario2040['residual_load_MW'][(
                  load_and_profiles_szenario2040['residual_load_MW'] == 0)].
          count(), " h")
    print("PV power generation (whole year): ", load_and_profiles_szenario2040[
        'solar_generation_MW'].sum()/1e6, " TWh")
    water_and_biomass_TWh = (param_value['misc_renewables_gen_2040_TWh']
                             + param_value['biomass_gen_2040_TWh']
                             + param_value['biomass_CHP_gen_2040_TWh'])
    print("Power generation all renewable energies (RE) in whole year: ",
          load_and_profiles_szenario2040['EE_generation_MW'].sum()/1e6
          + water_and_biomass_TWh, " TWh")
    print("Load Germany (electr. power comsumption whole year): ",
          load_and_profiles_szenario2040['load_MW'].sum()/1e6, " TWh")
    print("Share of RE in power generation ",
          (load_and_profiles_szenario2040['EE_generation_MW'].sum()
           + water_and_biomass_TWh*1e6)
          / load_and_profiles_szenario2040['load_MW'].sum())

    # Relative heat demand (range from 0 to 1)
    demand_profiles["demand_th"] = (
            data_heat['district_heating_profile_2012']/100)

    # Relative electricity demand (only positive share of residual load)
    demand_el_max = load_and_profiles_szenario2040['residual_load_MW'].max()

    demand_profiles['demand_el'] = (
            load_and_profiles_szenario2040['residual_load_MW'].
            clip(lower=0)/demand_el_max)

    # Relative negative residual load (only negative share of residual load).
    # Values are turned positive and will be used as positive "source" in the
    # oemof application.
    demand_el_min = load_and_profiles_szenario2040['residual_load_MW'].min()

    demand_profiles['neg_residual_el'] = (
            load_and_profiles_szenario2040['residual_load_MW'].clip(upper=0)
            / demand_el_min)
    average_el_pice_lin = (
            demand_profiles['demand_el'][(demand_profiles['demand_el'] > 0)].
            sum()/hours_of_pos_resload)
    print("Average electricity price (lin) =", average_el_pice_lin,
          "*P_el_max_lin")
    price_sqr = (demand_profiles['demand_el']
                 [(demand_profiles['demand_el'] > 0)]**2)
    print("Max electricity price (quadratic) to receive same average price as "
          "in linear model:",
          demand_profiles['demand_el'][(demand_profiles['demand_el'] > 0)].
          sum()/price_sqr[price_sqr > 0].sum(), "*P_el_max_lin")

# ****************************************************************************
# ********Save preprocessed data (input data for optimization)****************
# ****************************************************************************

    demand_profiles.to_csv(
        abs_path + cfg['demand_time_series'],
        encoding='utf-8',
        index=False)

    print("")
    print("Saved csv-file with time series for domestic heating and "
          "electricity demand to folder", cfg['demand_time_series'])

# ****************************************************************************
# ************************** Plots *******************************************
# ****************************************************************************

    # Colors
    beuth_red = (227/255, 35/255, 37/255)
    beuth_col_1 = (223/255, 242/255, 243/255)
    beuth_col_2 = (178/255, 225/255, 227/255)
    beuth_col_3 = (0/255, 152/255, 161/255)

    plt.plot(
        load_and_profiles_szenario2040['utc_timestamp'],
        load_and_profiles_szenario2040['residual_load_MW']
    )
    plt.xlabel('Zeit')
    plt.ylabel('Leistung in MW')
    plt.title('Residuallastverlauf (installierte Kapazitaeten nach '
              'Basisszenario 2040)')
    plt.suptitle('53,7% EE-Strom, 439h negative Residuallast')
    plt.savefig("../results/plots/Residuallastverlauf.png", dpi=300)

    fig, ax = plt.subplots()
    plt.grid(color='grey' ,
             linestyle='-',
             linewidth=0.5,
             zorder=1)
    ax.scatter(
        x=demand_profiles['demand_th']*1000,
        y=(demand_profiles['demand_el']*1000).
        add(demand_profiles['neg_residual_el']*-150),
        marker='.',
        c=[beuth_col_3],
        zorder=10
    )
    ax.set_ylabel('Strombedarf in $\mathrm{MW_{el}}$', fontsize=12)
    ax.set_xlabel('Wärmebedarf in $\mathrm{MW_{th}}$', fontsize=12)
    ax.set_ylim([-250, 1050])
    plt.savefig(cfg['demand_scatter_plot'], dpi=300)

    fig2, ax2 = plt.subplots()
    residual_2012 = (load_and_profiles_2012['DE_load_entsoe_power_statistics']
                     - load_and_profiles_2012['DE_solar_generation_actual']
                     - load_and_profiles_2012['DE_wind_generation_actual'])

    # negative residual load
    ax2.plot(
        load_and_profiles_szenario2040['residual_load_MW'][72:72+24*7],
        color=beuth_red
)
    ax2.plot(
        residual_2012[72:72+24*7],
        color=beuth_col_3
    )
    ax2.grid()
    plt.savefig("../results/plots/Vergleich2012_2040.png", dpi=300)

    fig3, ax3 = plt.subplots()
    start_b = 24*3
    delta_time = 24*7
    ymax = 70000
    ymin = -30000
    ax3.vlines(x=np.arange(start_b, start_b+delta_time, 24),
               ymin=ymin, ymax=ymax, linewidth=1, color=beuth_col_2)
    ax3.plot(
        load_and_profiles_szenario2040['residual_load_MW'][
            start_b:start_b+delta_time]/1e3,
        color=beuth_red
    )
    ax3.plot(
        residual_2012[start_b:start_b+delta_time]/1e3,
        color=beuth_col_3
    )
    ax3.set_ylabel('Residual Load ($\mathrm{GW_{el}}$)')
    ax3.set_xlabel('Time (h)')
    ax3.set_ylim([ymin/1e3, ymax/(1e3)])
    ax3.set_xlim([start_b, start_b+delta_time])
    ax3.hlines(
        y=0,
        xmin=start_b,
        xmax=start_b+delta_time,
        linewidth=2,
        color='k'
    )
    plt.savefig("../results/plots/RL_Comparison_2012_2040.png", dpi=300)

    fig4, ax4 = plt.subplots()

    ax4.plot(residual_2012[start_b:start_b+delta_time], color=beuth_col_3)
    ax4.vlines(
        x=np.arange(start_b, start_b+delta_time, 24),
        ymin=ymin,
        ymax=ymax,
        linewidth=1,
        color=beuth_col_2
    )
    ax4.set_ylim([ymin, ymax])
    ax4.set_xlim([start_b, start_b+delta_time])
    ax4.hlines(
        y=0,
        xmin=start_b,
        xmax=start_b+delta_time,
        linewidth=2,
        color='k'
    )
    plt.savefig("../results/plots/Residuallast2012.png", dpi=300)

    fig5, ax5 = plt.subplots()
    ax5.vlines(
        x=np.arange(start_b, start_b+delta_time, 24),
        ymin=ymin,
        ymax=ymax,
        linewidth=1,
        color=beuth_col_2
    )
    ax5.hlines(
        y=0,
        xmin=start_b,
        xmax=start_b+delta_time,
        linewidth=2,
        color='k'
    )
    ax5.plot(
        load_and_profiles_szenario2040['residual_load_MW'][
            start_b:start_b+delta_time],
        color=beuth_red)
    ax5.set_ylim([ymin, ymax])
    ax5.set_xlim([start_b, start_b+delta_time])
    plt.savefig("../results/plots/Residuallast2040.png", dpi=300)

    plt.style.use('ggplot')
    x = np.linspace(0, 8784, 8784, endpoint=True)
    fig6, ax6 = plt.subplots()
    ax6.plot(
        demand_profiles["demand_th"]*100,
        color=beuth_col_3,
        label="Thermal Energy Demand Profile"
    )
    ax6.plot(
        x,
        demand_profiles["demand_th"].sort_values(ascending=False)*100,
        color=beuth_red,
        label="Load Duration Curve"
    )
    ax6.legend(
        bbox_to_anchor=(0., 1.02, 1., .102),
        loc=3,
        ncol=2,
        mode="expand",
        borderaxespad=0.
    )
    ax6.set_xlim(0, 8760)
    ax6.set_ylabel("Thermal Energy Demand (%)")
    ax6.set_xlabel("Time (h)")
    plt.savefig("../results/plots/Thermal_load_DH.png", dpi=300)

    fig7, ax7 = plt.subplots()
    ax7.hlines(y=0, xmin=0, xmax=8760, linewidth=1, color='k')
    ax7.plot(
        load_and_profiles_szenario2040['residual_load_MW']/1e3,
        color=beuth_col_3,
        label="Residual Load Germany (Future)"
    )
    ax7.plot(
        x,
        load_and_profiles_szenario2040['residual_load_MW'].
        sort_values(ascending=False)/1e3,
        color=beuth_red,
        label="Load Duration Curve"
    )
    ax7.set_ylabel("Residual Load ($\mathrm{GW_{el}}$)")
    ax7.set_xlabel("Time (h)")
    ax7.legend(
        bbox_to_anchor=(0., 1.02, 1., .102),
        loc=3,
        ncol=2,
        mode="expand",
        borderaxespad=0.
    )
    ax7.set_xlim([0, 8760])
    plt.savefig("../results/plots/Residuallast2040_entireYear.png", dpi=300)

    print("")
    print("***Precrocessing: Finish!***")
