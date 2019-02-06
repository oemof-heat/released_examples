# -*- coding: utf-8 -*-

"""

Date: 6th of February 2019
Author: Jakob Wolf (jakob.wolf@beuth-hochschule.de)

General description
-------------------

Modeling a combined heat and power (CHP) plant in combination (optional) with an energy storage to
investigate the influence of the storage on the CHP operation.
The system comes with an electric heater, a so called Power-2-Heat (P2H) unit,
to provide electricity consumption as electricity grid service (The grid itself is not modeled!) in times when
negative electricity demand (so called 'negative residual load') occurs.
In some scenarios the system is extended by a thermal energy or an electrical energy storage.

The following energy system is modeled:

                input/output  bgas     bel      bth
                     |          |        |       |
 gas(Commodity)      |--------->|        |       |
                     |          |        |       |
 demand_el(Sink)     |<------------------|       |
                     |          |        |       |
 demand_th(Sink)     |<--------------------------|
                     |          |        |       |
 neg. residual load  |------------------>|       |
                     |          |        |       |
 P2H                 |          |        |------>|
                     |          |        |       |
                     |<---------|        |       |
 CHP(genericCHP)     |------------------>|       |
                     |-------------------------->|
                     |          |        |       |
 storage_th(Storage) |<--------------------------|
                     |-------------------------->|
                     |          |        |       |
 battery (Storage)   |<------------------|       |
                     |------------------>|       |


Installation requirements
-------------------------

This example requires the version v0.2.3 of oemof. Install by:

    pip install 'oemof>=0.2.3,<0.3'

Optional:

    pip install matplotlib

"""

__copyright__ = "Beuth Hochschule für Technik Berlin"
__license__ = "GPLv3"
__author__ = "jakob-wo (jakob.wolf@beuth-hochschule.de)"

###############################################################################
# imports
###############################################################################

# Default logger of oemof
from oemof.tools import logger
from oemof.tools import helpers

import oemof.solph as solph
import oemof.outputlib as outputlib
import oemof.graph as grph
import networkx as nx

import logging
import os
import pandas as pd
import yaml  # pip install pyyaml
import pprint as pp


def run_model_flexchp(config_path, scenario_nr):

    with open(config_path, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    if cfg['debug']:
        number_of_time_steps = 3
    else:
        number_of_time_steps = 8760

    solver = cfg['solver']
    debug = cfg['debug']
    periods = number_of_time_steps
    solver_verbose = cfg['solver_verbose']

    abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))

    logger.define_logging(logpath=abs_path+'/results/optimisation_results/log/',
                          logfile=cfg['filename_logfile']+'_scenario_{0}.log'.format(scenario_nr),
                          screen_level=logging.INFO,
                          file_level=logging.DEBUG)

    logging.info('Use parameters for scenario {0}'.format(scenario_nr))
    logging.info('Initialize the energy system')
    date_time_index = pd.date_range(cfg['start_date'], periods=number_of_time_steps,
                                    freq=cfg['frequency'])

    energysystem = solph.EnergySystem(timeindex=date_time_index)

    ##########################################################################
    # Read time series and parameter values from data files
    ##########################################################################

    file_path_demand_ts = abs_path + cfg['demand_time_series']
    data = pd.read_csv(file_path_demand_ts)

    file_path_param_01 = abs_path + cfg['parameters_energy_system'][scenario_nr-1]
    file_path_param_02 = abs_path + cfg['parameters_all_energy_systems']
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
    bth = solph.Bus(label='heat')

    energysystem.add(bgas, bel, bth)

    # Sources and sinks
    energysystem.add(solph.Sink(
        label='excess_bel',
        inputs={bel: solph.Flow(variable_costs=param_value['var_costs_excess_bel'])}))
    energysystem.add(solph.Sink(
        label='excess_bth',
        inputs={bth: solph.Flow(variable_costs=param_value['var_costs_excess_bth'])}))
    energysystem.add(solph.Source(
        label='shortage_bel',
        outputs={bel: solph.Flow(variable_costs=param_value['var_costs_shortage_bel'])}))
    energysystem.add(solph.Source(
        label='shortage_bth',
        outputs={bth: solph.Flow(variable_costs=param_value['var_costs_shortage_bth'])}))
    energysystem.add(solph.Source(
        label='rgas',
        outputs={bgas: solph.Flow(nominal_value=param_value['nom_val_gas'],
                                  summed_max=param_value['sum_max_gas'],
                                  variable_costs=param_value['var_costs_gas'])}))
    energysystem.add(solph.Source(
        label='P2H',
        outputs={bth: solph.Flow(actual_value=data['neg_residual_el'],
                                 nominal_value=param_value['nom_val_neg_residual']*param_value['conversion_factor_p2h'],
                                 fixed=True)}))
    energysystem.add(solph.Sink(
        label='demand_el',
        inputs={bel: solph.Flow(actual_value=data['demand_el'],
                                nominal_value=param_value['nom_val_demand_el'],
                                fixed=True)}))
    energysystem.add(solph.Sink(
        label='demand_th',
        inputs={bth: solph.Flow(actual_value=data['demand_th'],
                                nominal_value=param_value['nom_val_demand_th'],
                                fixed=True)}))

    energysystem.add(solph.components.GenericCHP(
        label='CHP_01',
        fuel_input={bgas: solph.Flow(
            H_L_FG_share_max=[param_value['H_L_FG_share_max'] for p in range(0, periods)])},
        electrical_output={bel: solph.Flow(
            P_max_woDH=[param_value['P_max_woDH'] for p in range(0, periods)],
            P_min_woDH=[param_value['P_min_woDH'] for p in range(0, periods)],
            Eta_el_max_woDH=[param_value['Eta_el_max_woDH'] for p in range(0, periods)],
            Eta_el_min_woDH=[param_value['Eta_el_min_woDH'] for p in range(0, periods)])},
        heat_output={bth: solph.Flow(
            Q_CW_min=[param_value['Q_CW_min_chp'] for p in range(0, periods)])},
        Beta=[param_value['Beta_chp'] for p in range(0, periods)],
        back_pressure=False))

    energysystem.add(solph.Transformer(
        label='boiler',
        inputs={bgas: solph.Flow()},
        outputs={bth: solph.Flow(nominal_value=param_value['nom_val_out_boiler'],
                                 variable_costs=param_value['var_costs_boiler'])},
        conversion_factors={bth: param_value['conversion_factor_boiler']}))

    if param_value['nom_capacity_storage_th'] > 0:
        storage_th = solph.components.GenericStorage(
            nominal_capacity=param_value['nom_capacity_storage_th'],
            label='storage_th',
            inputs={bth: solph.Flow(nominal_value=param_value['nom_val_input_bth_storage_th'],
                                    variable_costs=param_value['var_costs_input_bth_storage_th'])},
            outputs={bth: solph.Flow(nominal_value=param_value['nom_val_output_bth_storage_th'],
                                     variable_costs=param_value['var_costs_output_bth_storage_th'])},
            capacity_loss=param_value['capacity_loss_storage_th'],
            initial_capacity=param_value['init_capacity_storage_th'],
            inflow_conversion_factor=param_value['inflow_conv_factor_storage_th'],
            outflow_conversion_factor=param_value['outflow_conv_factor_storage_th'])
        energysystem.add(storage_th)

    if param_value['nom_capacity_storage_el'] > 0:
        storage_el = solph.components.GenericStorage(
            nominal_capacity=param_value['nom_capacity_storage_el'],
            label='storage_el',
            inputs={bel: solph.Flow(nominal_value=param_value['nom_val_input_bel_storage_el'],
                                    variable_costs=param_value['var_costs_input_bel_storage_el'])},
            outputs={bel: solph.Flow(nominal_value=param_value['nom_val_output_bel_storage_el'],
                                     variable_costs=param_value['var_costs_output_bel_storage_el'])},
            capacity_loss=param_value['capacity_loss_storage_el'],
            initial_capacity=param_value['init_capacity_storage_el'],
            inflow_conversion_factor=param_value['inflow_conv_factor_storage_el'],
            outflow_conversion_factor=param_value['outflow_conv_factor_storage_el'])
        energysystem.add(storage_el)

    ##########################################################################
    # Optimise the energy system and plot the results
    ##########################################################################

    logging.info('Optimise the energy system')

    model = solph.Model(energysystem)

    if debug:
        lpfile_name = 'flexCHP_scenario_{0}.lp'.format(scenario_nr)
        filename = os.path.join(
            helpers.extend_basic_path('lp_files'), lpfile_name)
        logging.info('Store lp-file in {0}.'.format(filename))
        model.write(filename, io_options={'symbolic_solver_labels': True})

    logging.info('Solve the optimization problem')
    model.solve(solver=solver, solve_kwargs={'tee': solver_verbose})

    logging.info('Store the energy system with the results.')

    energysystem.results['main'] = outputlib.processing.results(model)
    energysystem.results['meta'] = outputlib.processing.meta_results(model)

    energysystem.dump(dpath=abs_path + "/results/optimisation_results/dumps",
                      filename=cfg['filename_dumb']+'_scenario_{0}.oemof'.format(scenario_nr))



