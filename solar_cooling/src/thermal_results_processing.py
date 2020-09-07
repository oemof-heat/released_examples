# -*- coding: utf-8 -*-
"""

Date: 27,05,2020

@author: Franziska Pleissner

System C: concrete example: Plot cooling process with a solar collector
"""

############
# Preamble #
############

# Import packages
import oemof.solph as solph
import oemof.solph.views as views
import oemof_visio as oev

import logging
import os
import yaml
import pandas as pd
from thermal_model import ep_costs_func

# import oemof plots
try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

df_all_var = pd.DataFrame()


def thermal_postprocessing(config_path, var_number):
    global df_all_var

    with open(config_path, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    # define the used directories
    abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))
    results_path = abs_path + '/results'
    csv_path = results_path + '/optimisation_results/'
    plot_path = results_path + '/plots/'

    energysystem = solph.EnergySystem()
    energysystem.restore(dpath=(results_path + '/dumps'),
                         filename='thermal_model_{0}_{1}.oemof'.format(
                             cfg['exp_number'], var_number))

    sp = cfg['start_of_plot']
    ep = cfg['end_of_plot']

    # Look up investment costs. Therefor parameters must read again.
    if type(cfg['parameters_variation']) == list:
        file_path_param_01 = abs_path + '/data/data_public/' + cfg[
            'parameters_system']
        file_path_param_02 = abs_path + '/data/data_public/' + cfg[
            'parameters_variation'][var_number]
    elif type(cfg['parameters_system']) == list:
        file_path_param_01 = abs_path + '/data/data_public/' + cfg[
            'parameters_system'][var_number]
        file_path_param_02 = abs_path + '/data/data_public/' + cfg[
            'parameters_variation']
    else:
        file_path_param_01 = abs_path + '/data/data_public/' + cfg[
            'parameters_system']
        file_path_param_02 = abs_path + '/data/data_public/' + cfg[
            'parameters_variation']
    param_df_01 = pd.read_csv(file_path_param_01, index_col=1)
    param_df_02 = pd.read_csv(file_path_param_02, index_col=1)
    param_df = pd.concat([param_df_01, param_df_02], sort=True)
    param_value = param_df['value']

    logging.info('results received')

    #########################
    # Work with the results #
    #########################

    thermal_bus = views.node(energysystem.results['main'], 'thermal')
    cool_bus = views.node(energysystem.results['main'], 'cool')
    waste_bus = views.node(energysystem.results['main'], 'waste')
    el_bus = views.node(energysystem.results['main'], 'electricity')
    gas_bus = views.node(energysystem.results['main'], 'gas')
    ambient_res = views.node(energysystem.results['main'], 'ambient')
    none_res = views.node(energysystem.results['main'], 'None')

    # sequences:
    thermal_seq = thermal_bus['sequences']
    cool_seq = cool_bus['sequences']
    waste_seq = waste_bus['sequences']
    el_seq = el_bus['sequences']
    gas_seq = gas_bus['sequences']
    ambient_seq = ambient_res['sequences']

    # scalars
    thermal_scal = thermal_bus['scalars']
    cool_scal = cool_bus['scalars']
    waste_scal = waste_bus['scalars']
    el_scal = el_bus['scalars']
    none_scal = none_res['scalars']
    none_scal_given = views.node(
        energysystem.results['param'], 'None')['scalars']
    el_scal[(('pv', 'electricity'), 'invest')] = (
            el_scal[(('pv', 'electricity'), 'invest')]*param_value['size_pv'])
    # Conversion of the pv-investment-size, because Invest-object is normalized
    # at 0.970873786 kWpeak

    # solar fraction

    # thermal
    # control of boiler (No heat must go from boiler to excess)
    df_control_th = pd.DataFrame()
    df_control_th['boiler'] = thermal_seq[(('boiler', 'thermal'), 'flow')]
    df_control_th['excess'] = thermal_seq[
        (('thermal', 'excess_thermal'), 'flow')]
    df_control_th['Product'] = (df_control_th['boiler']
                                * df_control_th['excess'])

    heat_from_boiler = thermal_seq[(('boiler', 'thermal'), 'flow')].sum()
    heat_from_collector = thermal_seq[(('collector', 'thermal'), 'flow')].sum()
    heat_to_excess = thermal_seq[(('thermal', 'excess_thermal'), 'flow')].sum()
    heat_collector_used = heat_from_collector - heat_to_excess
    sol_fraction_th = (heat_collector_used
                       / (heat_collector_used + heat_from_boiler))

    # electric:
    # control_el (No Power must go from grid to excess)
    df_control_el = pd.DataFrame()
    df_control_el['grid_el'] = el_seq[(('grid_el', 'electricity'), 'flow')]
    df_control_el['excess'] = el_seq[(('electricity', 'excess_el'), 'flow')]
    df_control_el['Product'] = (df_control_el['grid_el']
                                * df_control_el['excess'])

    el_from_grid = el_seq[(('grid_el', 'electricity'), 'flow')].sum()
    el_from_pv = el_seq[(('pv', 'electricity'), 'flow')].sum()
    el_to_excess = el_seq[(('electricity', 'excess_el'), 'flow')].sum()
    el_pv_used = el_from_pv - el_to_excess
    sol_fraction_el = el_pv_used / (el_pv_used + el_from_grid)

    # gas usage:
    gas_used = gas_seq[(('naturalgas', 'gas'), 'flow')].sum()

    # Power to the output:
    electricity_output = el_seq[(('electricity', 'excess_el'), 'flow')].sum()
    electricity_output_pv = el_seq[(('pv', 'electricity'), 'flow')].sum()

    # ## Costs ## #

    costs_total = energysystem.results['meta']['objective']

    # storage costs must be subtract for reference scenario or added
    # for the other scenarios.

    # reference scenario:
    if (param_value['nominal_capacitiy_stor_thermal'] == 0 and
            param_value['nominal_capacitiy_stor_cool'] == 0):
        costs_total_wo_stor = (
                costs_total
                - (none_scal[(('storage_thermal', 'None'), 'invest')]
                   * none_scal_given[
                       (('storage_thermal', 'None'), 'investment_ep_costs')])
                - (none_scal[(('storage_cool', 'None'), 'invest')]
                   * none_scal_given[
                       (('storage_cool', 'None'), 'investment_ep_costs')]))

    # other scenarios:
    else:
        # calculation of ep_costs
        ep_costs_th_stor = ep_costs_func(
            param_value['invest_costs_stor_thermal_capacity'],
            param_value['lifetime_stor_thermal'],
            param_value['opex_stor_thermal'],
            param_value['wacc'])
        ep_costs_cool_stor = ep_costs_func(
            param_value['invest_costs_stor_cool_capacity'],
            param_value['lifetime_stor_cool'],
            param_value['opex_stor_cool'],
            param_value['wacc'])
        # calculation of the scenario costs inclusive storage costs
        costs_total_w_stor = (
                costs_total
                + (none_scal_given[
                       (('storage_cool', 'None'), 'nominal_capacity')]
                   * ep_costs_cool_stor)
                + (none_scal_given[
                       (('storage_thermal', 'None'), 'nominal_capacity')]
                   * ep_costs_th_stor))

    ########################
    # Write results in csv #
    ########################

    # ## scalars ## #
    # base scalars:
    scalars_all = thermal_scal\
        .append(cool_scal)\
        .append(waste_scal)\
        .append(none_scal)\
        .append(el_scal)
    for i in range(0, none_scal_given.count()):
        if 'nominal_capacity' in none_scal_given.index[i]:
            scalars_all = pd.concat(
                [scalars_all,
                 pd.Series([none_scal_given[i]],
                           index=[none_scal_given.index[i]])])

    # solar fractions
    scalars_all = pd.concat(
        [scalars_all,
         pd.Series([sol_fraction_th],
                   index=["('solar fraction', 'thermal'), ' ')"])])
    if df_control_th['Product'].sum() != 0:
        scalars_all = pd.concat(
            [scalars_all,
             pd.Series([df_control_th['Product'].sum()],
                       index=["Has to be 0!!!"])])

    scalars_all = pd.concat(
        [scalars_all,
         pd.Series([sol_fraction_el],
                   index=["('solar fraction', 'electric'), ' ')"])])
    if df_control_el['Product'].sum() != 0:
        scalars_all = pd.concat(
            [scalars_all,
             pd.Series([df_control_el['Product'].sum()],
                       index=["Has to be 0!!!"])])

    # various results
    scalars_all = pd.concat(
        [scalars_all,
         pd.Series([gas_used],
                   index=["('natural gas', 'gas'), 'summe')"])])
    scalars_all = pd.concat(
        [scalars_all,
         pd.Series([electricity_output],
                   index=["('electricity', 'output'), 'summe')"])])
    scalars_all = pd.concat(
        [scalars_all,
         pd.Series([electricity_output_pv],
                   index=["('pv', 'electricity'), 'summe')"])])

    # costs with or without storage (depends on reference scenario or not)
    if (param_value['nominal_capacitiy_stor_thermal'] != 0 or
            param_value['nominal_capacitiy_stor_cool'] != 0):
        scalars_all = pd.concat(
            [scalars_all,
             pd.Series([costs_total_w_stor],
                       index=["('costs', 'w_stor'), 'per year')"])])
    scalars_all = pd.concat(
        [scalars_all,
         pd.Series([costs_total],
                   index=["('costs', 'wo_stor'), 'per year')"])])
    if (param_value['nominal_capacitiy_stor_thermal'] == 0 and
            param_value['nominal_capacitiy_stor_cool'] == 0):
        scalars_all = pd.concat(
            [scalars_all,
             pd.Series([costs_total_wo_stor],
                       index=["('costs', 'wo stor'), 'per year')"])])

    # experiment number and variation
    scalars_all = pd.concat(
        [scalars_all,
         pd.Series(['{0}_{1}'.format(cfg['exp_number'], var_number)],
                   index=["('Exp', 'Var'), 'number')"])])

    # write scalars into csv for this experiment and variation
    scalars_all.to_csv(
        csv_path + 'thermal_model_{0}_{1}_scalars.csv'.format(
            cfg['exp_number'], var_number))

    # write scalars for all variations of the experiment into csv
    df_all_var = pd.concat([df_all_var, scalars_all], axis=1, sort=True)
    if var_number == (cfg['number_of_variations']-1):
        df_all_var.to_csv(
            csv_path
            + 'thermal_model_{0}_scalars_all_variations.csv'.format(
                cfg['exp_number']))
        logging.info('Writing DF_all_variations into csv')

    # ## sequences ## #
    sequences_df = pd.merge(ambient_seq, waste_seq, left_index=True,
                            right_index=True)
    sequences_df = pd.merge(sequences_df,  el_seq, left_index=True,
                            right_index=True)
    sequences_df = pd.merge(sequences_df,  cool_seq, left_index=True,
                            right_index=True)
    sequences_df = pd.merge(sequences_df, thermal_seq, left_index=True,
                            right_index=True)

    sequences_df[('storage_thermal', 'None'), 'storage_content'] = (none_res[
        'sequences'][(('storage_thermal', 'None'), 'storage_content')])
    sequences_df[('storage_cool', 'None'), 'storage_content'] = (none_res[
        'sequences'][(('storage_cool', 'None'), 'storage_content')])

    sequences_df.to_csv(
        csv_path + 'thermal_model_{0}_{1}_sequences.csv'.format(
            cfg['exp_number'], var_number))

    ########################
    # Plotting the results #  # to adapt for the use case
    ########################

    cool_seq_resample = cool_seq.iloc[sp:ep]
    thermal_seq_resample = thermal_seq.iloc[sp:ep]
    waste_seq_resample = waste_seq.iloc[sp:ep]
    el_seq_resample = el_seq.iloc[sp:ep]
    gas_seq_resample = gas_seq.iloc[sp:ep]
    ambient_seq_resample = ambient_seq.iloc[sp:ep]

    def shape_legend(node, reverse=False, **kwargs):  # just copied
        handels = kwargs['handles']
        labels = kwargs['labels']
        axes = kwargs['ax']
        parameter = {}

        new_labels = []
        for label in labels:
            label = label.replace('(', '')
            label = label.replace('), flow)', '')
            label = label.replace(node, '')
            label = label.replace(',', '')
            label = label.replace(' ', '')
            new_labels.append(label)
        labels = new_labels

        parameter['bbox_to_anchor'] = kwargs.get('bbox_to_anchor', (1, 1))
        parameter['loc'] = kwargs.get('loc', 'upper left')
        parameter['ncol'] = kwargs.get('ncol', 1)
        plotshare = kwargs.get('plotshare', 0.9)

        if reverse:
            handels = handels.reverse()
            labels = labels.reverse()

        box = axes.get_position()
        axes.set_position([box.x0, box.y0, box.width * plotshare, box.height])

        parameter['handles'] = handels
        parameter['labels'] = labels
        axes.legend(**parameter)
        return axes

    cdict = {
        (('collector', 'thermal'), 'flow'): '#ffde32',
        (('boiler', 'thermal'), 'flow'): '#ff0000',
        (('storage_thermal', 'thermal'), 'flow'): '#9acd32',
        (('thermal', 'storage_thermal'), 'flow'): '#9acd32',
        (('thermal', 'absorption_chiller'), 'flow'): '#4682b4',
        (('thermal', 'excess_thermal'), 'flow'): '#4682b4',
        (('absorption_chiller', 'cool'), 'flow'): '#4682b4',
        (('storage_cool', 'cool'), 'flow'): '#555555',
        (('cool', 'storage_cool'), 'flow'): '#9acd32',
        (('cool', 'demand'), 'flow'): '#cd0000',
        (('el_grid', 'electricity'), 'flow'): '#999999',
        (('pv', 'electricity'), 'flow'): '#ffde32',
        (('storage_el', 'electricity'), 'flow'): '#9acd32',
        (('electricity', 'storage_el'), 'flow'): '#9acd32',
        (('electricity', 'cooling_tower'), 'flow'): '#ff0000',
        (('electricity', 'aquifer'), 'flow'): '#555555',
        (('storage_cool', 'None'), 'capacity'): '#555555',
        (('storage_cool', 'cool'), 'flow'): '#9acd32',
        (('absorpion_chiller', 'waste'), 'flow'): '#4682b4',
        (('waste', 'cool_tower'), 'flow'): '#42c77a'}

    # define order of inputs and outputs
    inorderthermal = [(('collector', 'thermal'), 'flow'),
                      (('storage_thermal', 'thermal'), 'flow'),
                      (('boiler', 'thermal'), 'flow')]
    outorderthermal = [(('thermal', 'absorption_chiller'), 'flow'),
                       (('thermal', 'storage_thermal'), 'flow'),
                       (('thermal', 'excess_thermal'), 'flow')]
    inordercool = [(('absorption_chiller', 'cool'), 'flow'),
                   (('storage_cool', 'cool'), 'flow')]
    outordercool = [(('cool', 'demand'), 'flow'),
                    (('cool', 'storage_cool'), 'flow')]
    inorderel = [(('pv', 'electricity'), 'flow'),
                 (('storage_electricity', 'electricity'), 'flow'),
                 (('grid_el', 'electricity'), 'flow')]
    outorderel = [(('electricity', 'cooling_tower'), 'flow'),
                  (('electricity', 'storage_electricity'), 'flow')]
    # inorderstor = [(('cool', 'storage_cool'), 'flow')]
    # outorderstor = [(('storage_cool', 'cool'), 'flow'),
    #                 (('storage_cool', 'None'), 'capacity')]

    fig = plt.figure(figsize=(15, 15))

    # plot thermal energy
    my_plot_thermal = oev.plot.io_plot(
        'thermal', thermal_seq_resample, cdict=cdict,
        inorder=inorderthermal, outorder=outorderthermal,
        ax=fig.add_subplot(2, 2, 2), smooth=False)

    ax_thermal = shape_legend('thermal', **my_plot_thermal)

    ax_thermal.set_ylabel('Power in kW')
    ax_thermal.set_xlabel('time')
    ax_thermal.set_title("thermal")

    # plot cooling energy
    my_plot_cool = oev.plot.io_plot(
        'cool', cool_seq_resample, cdict=cdict,
        inorder=inordercool, outorder=outordercool,
        ax=fig.add_subplot(2, 2, 1), smooth=False)

    ax_cool = shape_legend('cool', **my_plot_cool)

    ax_cool.set_ylabel('Power in kW')
    ax_cool.set_xlabel('time')
    ax_cool.set_title("cool")

    # plot electrical energy
    my_plot_el = oev.plot.io_plot(
        'electricity', el_seq_resample, cdict=cdict,
        inorder=inorderel, outorder=outorderel,
        ax=fig.add_subplot(2, 2, 3), smooth=False)

    ax_el = shape_legend('electricity', **my_plot_el)

    ax_el.set_ylabel('Power in kW')
    ax_el.set_xlabel('time')
    ax_el.set_title("electricity")

    plt.savefig(
        plot_path + 'thermal_model_{0}_{1}.png'.format(
            cfg['exp_number'], var_number))
    csv_plot = pd.merge(thermal_seq_resample, cool_seq_resample,
                        left_index=True, right_index=True)
    csv_plot = pd.merge(csv_plot, el_seq_resample,
                        left_index=True, right_index=True)
    csv_plot.to_csv(
        plot_path + 'thermal_model_plot_{0}_{1}.csv'.format(
            cfg['exp_number'], var_number))

    return df_all_var
