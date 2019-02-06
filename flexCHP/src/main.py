
"""

Date: 6th of February 2019
Author: Jakob Wolf (jakob.wolf@beuth-hochschule.de)

"""


import os
from model_flex_chp import run_model_flexchp
from analyse import analyse_and_print
from analyse import make_plots
import yaml

def main():

    # Configuration file to run model with
    exp_cfg_file_name = 'experiment_1.yml'
    config_file_path = os.path.abspath('../experiment_config/' + exp_cfg_file_name)
    with open(config_file_path, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    run_single_scenario = cfg['run_single_scenario']
    if run_single_scenario:
        if cfg['run_model']:
            run_model_flexchp(config_path=config_file_path, scenario_nr=cfg['scenario_number'])
        if cfg['run_postprocessing']:
            analyse_and_print(config_path=config_file_path, scenario_nr=cfg['scenario_number'])
    else:
        scenarios = [1, 2, 3]
        for scenario in scenarios:
            if cfg['run_model']:
                print('\n*** Scenario {0}***'.format(scenario))
                run_model_flexchp(config_path=config_file_path, scenario_nr=scenario)
            if cfg['run_postprocessing']:
                analyse_and_print(config_path=config_file_path, scenario_nr=scenario)
                print('')
        if cfg['make_plots']:
                make_plots()

main()
