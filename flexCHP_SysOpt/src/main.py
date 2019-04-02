
"""

    The following directories are going to be created if not already existing.

    .
    |-data_preprocessed
    |-data_raw
    |   |-data_confidential
    |   |-data_public
    |-data_preprocessed
    |-src
    |-experiment_config
    |-results
    |   |-optimisation_results
    |   |   |-data
    |   |   |   |-linear_price_relationship
    |   |   |   |-quadratic_price_relationship
    |   |   |-dumps
    |   |   |   |-linear_price_relationship
    |   |   |   |-quadratic_price_relationship
    |   |   |-log
    |   |-data_postprocessed
    |   |   |-linear_price_relationship
    |   |   |-quadratic_price_relationship
    |   |-plots


"""

__copyright__ = "Beuth Hochschule für Technik Berlin, Reiner Lemoine Institut"
__license__ = "GPLv3"
__author__ = "jakob-wo (jakob.wolf@beuth-hochschule.de)"

import os
from model_flex_chp import run_model_flexchp
from preprocessing import preprocess_timeseries
from analyse import analyse_energy_system
from analyse_sensitivity import analyse_sensitivity
import yaml
import os


def main():

    abs_path = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))

    # Select the configuration file
    exp_cfg_file_name = 'experiment.yml'
    config_file_path = os.path.abspath('../experiment_config/'
                                       + exp_cfg_file_name)
    with open(config_file_path, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    # Directory structure that ist needed to run model and pre- and
    # postprocessing scripts
    data_prepr_dir = (abs_path + '/data_preprocessed/')
    data_confident_dir = (abs_path + '/data_raw/data_confidential/')
    data_public_dir = (abs_path + '/data_raw/data_public/')
    results_data_lin_dir = (abs_path + '/results/optimisation_results/data/'
                                       'linear_price_relationship/')
    results_data_quad_dir = (abs_path + '/results/optimisation_results/data/'
                                        'quadratic_price_relationship/')
    results_dumps_lin_dir = (abs_path + '/results/optimisation_results/dumps/'
                                        'linear_price_relationship/')
    results_dumps_quad_dir = (abs_path + '/results/optimisation_results/dumps/'
                                         'quadratic_price_relationship/')
    results_log_dir = (abs_path + '/results/optimisation_results/log/')
    results_postprocess_lin_dir = (abs_path + '/results/data_postprocessed/'
                                              'linear_price_relationship/')
    results_postprocess_quad_dir = (abs_path + '/results/data_postprocessed/'
                                               'quadratic_price_relationship/')
    results_plots_lin_dir = (abs_path + '/results/plots/'
                                        'linear_price_relationship/')
    results_plots_quad_dir = (abs_path + '/results/plots/'
                                         'quadratic_price_relationship/')
    directories_list = [data_prepr_dir,
                        data_confident_dir,
                        data_public_dir,
                        results_data_lin_dir,
                        results_data_quad_dir,
                        results_dumps_lin_dir,
                        results_dumps_quad_dir,
                        results_log_dir,
                        results_postprocess_lin_dir,
                        results_postprocess_quad_dir,
                        results_plots_lin_dir,
                        results_plots_quad_dir]

    # Create directories if not already existing
    for d in directories_list:
        if not os.path.exists(d):
            print("Directory <<", d, ">> does not exist and will be created.")
            os.makedirs(d)
        if os.path.exists(d):
            print("Directory <<", d, ">> exists already.")

    print("***Directory structure checked and fully established.***\n")

    # Depending on the settings made in the config-file a single scenario will
    # be solved (which one has to be selected in the config-file as well) or
    # the full range of parameter variations will be solved.
    if cfg['run_single_scenario']:
        if cfg['run_preprocessing']:
            preprocess_timeseries(config_path=config_file_path)
        if cfg['run_model']:
            run_model_flexchp(
                config_path=config_file_path,
                variation_nr=cfg['variation_number'])
        if cfg['run_postprocessing']:
            analyse_energy_system(
                config_path=config_file_path,
                variation_nr=cfg['variation_number'])
    else:
        scenarios = range(len(cfg['parameter_variation']))
        for scenario in scenarios:
            if cfg['run_preprocessing']:
                preprocess_timeseries(config_path=config_file_path)
            if cfg['run_model']:
                print('\n*** Scenario {0}***'.format(scenario))
                run_model_flexchp(
                    config_path=config_file_path,
                    variation_nr=scenario)
            if cfg['run_postprocessing']:
                analyse_energy_system(
                    config_path=config_file_path,
                    variation_nr=scenario)
            print('')
        if cfg['run_postprocessing']:
            analyse_sensitivity(config_path=config_file_path)


main()
