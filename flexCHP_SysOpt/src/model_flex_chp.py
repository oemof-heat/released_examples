# -*- coding: utf-8 -*-

"""

Date: 7th of January 2019
Author: Jakob Wolf (jakob.wolf@beuth-hochschule.de)

General description
-------------------


The following energy system is modeled:

                input/output  bgas     bel      bth
                            |          |        |       |
 gas(Commodity)             |--------->|        |       |
                            |          |        |       |
 demand_el(Sink)            |<------------------|       |
                            |          |        |       |
 demand_th(Sink)            |<--------------------------|
                            |          |        |       |
 neg. residual load         |------------------>|       |
                            |          |        |       |
 P2H                        |          |        |------>|
                            |          |        |       |
                            |<---------|        |       |
 CHP(ExtractionTurbineCHP)  |------------------>|       |
                            |-------------------------->|
                            |          |        |       |
 storage_th(Storage)        |<--------------------------|
                            |-------------------------->|
                            |          |        |       |
 battery (Storage)          |<------------------|       |
                            |------------------>|       |


Data
----
demand_profile_A_nominal.20180912.csv


Installation requirements
-------------------------

This example requires the version v0.2.3 of oemof. Install by:

    pip install 'oemof>=0.2.3,<0.3'

Optional:

    pip install matplotlib

"""

__copyright__ = "Beuth Hochschule für Technik Berlin, Reiner Lemoine Institut"
__license__ = "GPLv3"
__author__ = "jakob-wo (jakob.wolf@beuth-hochschule.de)"

###############################################################################
# imports
###############################################################################

from oemof.tools import logger
from oemof.tools import helpers

import oemof.solph as solph
from oemof.solph.components import ExtractionTurbineCHP
import oemof.outputlib as outputlib
import oemof.tools.economics as economics

import logging
import os
import pandas as pd
import yaml  # pip install pyyaml


def run_model_flexchp(config_path, variation_nr):

    with open(config_path, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    if cfg['debug']:
        number_of_time_steps = 3
    else:
        number_of_time_steps = 8760

    solver = cfg['solver']
    debug = cfg['debug']
    solver_verbose = cfg['solver_verbose']  # show/hide solver output

    abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))

    # initiate the logger (see the API docs for more information)
    logger.define_logging(logpath=(abs_path
                                   + '/results/optimisation_results/log/'),
                          logfile=(cfg['filename_logfile']+'_scenario_{0}.log'.
                                   format(variation_nr)),
                          screen_level=logging.INFO,
                          file_level=logging.DEBUG)

    logging.info('Use parameters for scenario {0}'.format(variation_nr))
    logging.info('Initialize the energy system')
    date_time_index = pd.date_range(cfg['start_date'],
                                    periods=number_of_time_steps,
                                    freq=cfg['frequency'])

    energysystem = solph.EnergySystem(timeindex=date_time_index)

    ##########################################################################
    # Read time series and parameter values from data files
    ##########################################################################

    file_path_demand_ts = abs_path + cfg['demand_time_series']
    data = pd.read_csv(file_path_demand_ts)

    file_path_param_01 = abs_path + cfg['parameters_energy_system']
    file_path_param_02 = abs_path + cfg['parameter_variation'][variation_nr]
    param_df_01 = pd.read_csv(file_path_param_01, index_col=1)
    param_df_02 = pd.read_csv(file_path_param_02, index_col=1)
    param_df = pd.concat([param_df_01, param_df_02], sort=True)
    param_value = param_df['value']

    ##########################################################################
    # Create oemof object
    ##########################################################################

    logging.info('Create oemof objects')

    bgas = solph.Bus(label="natural_gas")
    bel = solph.Bus(label="electricity")
    bel_residual = solph.Bus(label="residual")
    bth = solph.Bus(label='heat')

    energysystem.add(bgas, bel, bel_residual, bth)

    # Sources and sinks
    energysystem.add(solph.Sink(
        label='excess_bel',
        inputs={bel: solph.Flow(
            variable_costs=param_value['var_costs_excess_bel'])}))

    energysystem.add(solph.Sink(
        label='excess_bth',
        inputs={bth: solph.Flow(
            variable_costs=param_value['var_costs_excess_bth'])}))

    energysystem.add(solph.Source(
        label='shortage_bel',
        outputs={bel: solph.Flow(
            variable_costs=param_value['var_costs_shortage_bel'])}))

    energysystem.add(solph.Source(
        label='shortage_bth',
        outputs={bth: solph.Flow(
            variable_costs=param_value['var_costs_shortage_bth'])}))

    energysystem.add(solph.Source(
         label='rgas',
         outputs={bgas: solph.Flow(
             nominal_value=param_value['nom_val_gas'],
             summed_max=param_value['sum_max_gas'],
             variable_costs=(param_value['var_costs_gas']
                             * param_value['gas_price_variation']))}))

    energysystem.add(solph.Source(
        label='residual_el',
        outputs={bel_residual: solph.Flow(
            actual_value=data['neg_residual_el'],
            nominal_value=param_value['nom_val_neg_residual'],
            fixed=True)}))

    if cfg['price_el_quadratic'] == True:
        energysystem.add(solph.Sink(
            label='demand_el',
            inputs={bel: solph.Flow(
                variable_costs=(param_value['el_price']
                                * param_value['price_factor_sqr']
                                * param_value['el_price_variation']
                                * data['demand_el']**2),
                nominal_value=8000)}))

    if cfg['price_el_quadratic'] == False:
        energysystem.add(solph.Sink(
            label='demand_el',
            inputs={bel: solph.Flow(
                variable_costs=(param_value['el_price']
                                * param_value['el_price_variation']
                                * data['demand_el']),
                nominal_value=8000)}))

    energysystem.add(solph.Sink(
        label='demand_th',
        inputs={bth: solph.Flow(
            actual_value=data['demand_th'],
            nominal_value=param_value['nom_val_demand_th'],
            fixed=True,
            variable_costs=(- param_value['var_costs_gas']
                            / param_value['conversion_factor_boiler']))}))

    # Auxiliary component to prevent CHP electricity being used in P2H (not
    # representing a physical component!)
    energysystem.add(solph.Transformer(
        label='oneway',
        inputs={bel_residual: solph.Flow(
            nominal_value=param_value['nom_val_neg_residual'])},
        outputs={bel: solph.Flow()},
        conversion_factors={bel: 1}))

    # Combined Heat and Power Plant (CHP)
    # Calculate annuity per installed unit of power [€/MW]
    ep_costs_CHP = economics.annuity(
        capex=param_value['capex_CHP'],
        n=param_value['lifetime_CHP'],
        wacc=param_value['wacc_CHP'])

    # Add CHP with its technical specifications to the energy system
    energysystem.add(ExtractionTurbineCHP(
        label='CHP_01',
        inputs={bgas: solph.Flow(
            investment=solph.Investment(
                ep_costs=(ep_costs_CHP*param_value['conv_factor_full_cond']),
                maximum=1667))},
        outputs={
            bel: solph.Flow(),
            bth: solph.Flow()},
        conversion_factors={
            bel: param_value['conv_factor_bel_CHP'],
            bth: param_value['conv_factor_bth_CHP']},
        conversion_factor_full_condensation={
            bel: param_value['conv_factor_full_cond']}))

    # Peak load gas boiler
    # Calculate annuity per installed unit of power [€/MW]
    ep_costs_boiler = economics.annuity(
        capex=param_value['capex_boiler'],
        n=param_value['lifetime_boiler'],
        wacc=param_value['wacc_boiler'])

    # Add boiler with its technical specifications to the energy system
    energysystem.add(solph.Transformer(
        label='boiler',
        inputs={bgas: solph.Flow()},
        outputs={bth: solph.Flow(investment=solph.Investment(
            ep_costs=ep_costs_boiler))},
        conversion_factors={bth: param_value['conversion_factor_boiler']}))

    ep_costs_p2h = economics.annuity(
        capex=param_value['capex_p2h'],
        n=param_value['lifetime_p2h'],
        wacc=param_value['wacc_p2h'])

    energysystem.add(solph.Transformer(
        label='P2H',
        inputs={bel_residual: solph.Flow()},
        outputs={bth: solph.Flow(investment=solph.Investment(
            ep_costs=ep_costs_p2h))},
        conversion_factors={bth: param_value['conversion_factor_p2h']}))

    ep_costs_TES = economics.annuity(
        capex=(param_value['capex_TES']*param_value['TES_capex_variation']),
        n=param_value['lifetime_TES'],
        wacc=param_value['wacc_TES'])
    storage_th = solph.components.GenericStorage(
        label='storage_th',
        inputs={bth: solph.Flow()},
        outputs={bth: solph.Flow()},
        capacity_loss=param_value['capacity_loss_storage_th'],
        initial_capacity=param_value['init_capacity_storage_th'],
        inflow_conversion_factor=param_value['inflow_conv_factor_storage_th'],
        outflow_conversion_factor=param_value[
            'outflow_conv_factor_storage_th'],
        invest_relation_input_capacity=1/param_value[
            'charging_time_storage_th'],
        invest_relation_output_capacity=1/param_value[
            'charging_time_storage_th'],
        investment=solph.Investment(ep_costs=ep_costs_TES))
    energysystem.add(storage_th)

    ep_costs_EES = economics.annuity(
        capex=param_value['capex_EES']*param_value['EES_capex_variation'],
        n=param_value['lifetime_EES'],
        wacc=param_value['wacc_EES'])

    storage_el = solph.components.GenericStorage(
        label='storage_el',
        inputs={bel: solph.Flow()},
        outputs={bel: solph.Flow()},
        capacity_loss=param_value['capacity_loss_storage_el'],
        initial_capacity=param_value['init_capacity_storage_el'],
        inflow_conversion_factor=param_value['inflow_conv_factor_storage_el'],
        outflow_conversion_factor=param_value[
            'outflow_conv_factor_storage_el'],
        invest_relation_input_capacity=1 / param_value[
            'charging_time_storage_el'],
        invest_relation_output_capacity=1 / param_value[
            'charging_time_storage_el'],
        investment=solph.Investment(ep_costs=ep_costs_EES))
    energysystem.add(storage_el)

    ##########################################################################
    # Optimise the energy system and store the results
    ##########################################################################

    logging.info('Optimise the energy system')

    model = solph.Model(energysystem)

    if debug:
        lpfile_name = 'flexCHP_scenario_{0}.lp'.format(variation_nr)
        filename = os.path.join(
            helpers.extend_basic_path('lp_files'), lpfile_name)
        logging.info('Store lp-file in {0}.'.format(filename))
        model.write(filename, io_options={'symbolic_solver_labels': True})

    logging.info('Solve the optimization problem')
    model.solve(solver=solver, solve_kwargs={'tee': solver_verbose})

    logging.info('Store the energy system with the results.')

    energysystem.results['main'] = outputlib.processing.results(model)
    energysystem.results['meta'] = outputlib.processing.meta_results(model)
    if cfg['price_el_quadratic']:
        energysystem.dump(
            dpath=(abs_path + "/results/optimisation_results/dumps/"
                              "quadratic_price_relationship"),
            filename=(cfg['filename_dumb']+'_scenario_{0}.oemof'.
                      format(variation_nr)))
    if cfg['price_el_quadratic'] == False:
        energysystem.dump(
            dpath=(abs_path + "/results/optimisation_results/dumps/"
                              "linear_price_relationship"),
            filename=(cfg['filename_dumb']+'_scenario_{0}.oemof'.format(
                variation_nr)))
