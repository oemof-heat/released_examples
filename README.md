# Released Examples

Welcome to the released examples section of the project *oemof_heat*. 
Here you find models and applications that were used in published research of 
the project.
We apply the Open Energy Modelling Framework *oemof* in 
energy system analysis for dispatch and system optimizations.
Our work focuses on modelling heat components with linear programming, 
e.g., combined heat and power plants (CHP), heat pumps, 
district heating networks and solar thermal collectors.

List of currently available models:
- Highly flexible Combined Heat and Power Production (*flexCHP*)
- Highly flexible Combined Heat and Power Production - System Optimization (*flexCHP_SysOpt*)

Please contact us if you have any questions regarding the models or 
the input data, if you are struggling with the installation or if you have 
ideas for enhancements or further research.  
Contact: jakob-wo (jakob.wolf@beuth-hochschule.de)

## Model description

### flexCHP
Dispatch optimization. Scenario comparison.  
Published research:  
J. Wolf, C. Pels Leusden, S. Köhler, and J. Launer, “Flexibilisierung
von KWK-Anlagen für wachsende herausforderungen einer
sicheren strom- und wärmeversorgung,” in *Regenerative-Energietechnik-
Konferenz RET.Con 2019*, Nordhausen, 2019.

### flexCHP_SysOpt
System and dispatch optimization. Sensitivity analysis.  
Published research:  
J. Wolf, C. Pels Leusden, S. Köhler, and J. Launer, “Optimization of Extended 
CHP Plants with Energy Storages – an Open-Source Approach,” in *International 
Renewable Storage 
Conference (IRES 2019)*, Düsseldorf, 2019.

## How to download and run a model?
In the following steps we describe how you get from here to running the script,
 solving the optimization program yourself and finally looking at the results. 
We assume that you have python installed already and that you are familiar with 
the basic use of a terminal (e.g., enter a command or navigate to a directory).

Preparation steps:
* **Download or clone this repo.**
Download the repository from this page (our GitHub repository) and unzip it to 
a local directory of your choice or use Git to clone this repository.
* **Install required packages.** You can use the `requirements.txt` file and pip 
or install the packages listed in the `requirements.txt` file in any other way 
you are familiar with. If you want to use pip open a terminal, navigate to the 
downloaded directory and enter `pip install -r requirements.txt`.
* **Download and install Cbc (an open-source mixed integer linear programming solver).** 
For instructions have a look at the 
[oemof-documentation](https://oemof.readthedocs.io/en/stable/installation_and_setup.html) 
and scroll down to the section *Solver*, for Linux distributions, or
 *Solver for Windows*.
* **Run installation test (optional).** 
By now you should have installed two essential requirements: 
oemof and the Cbc-solver.
You can check whether both were installed successfully with 
the installation test provided by the oemof developer team. 
Simply run `oemof_installation_test` in your terminal.
If you are using virtual environments (recommended but not necessary) make 
sure your run the test in the environment where oemof is installed.
If the installation was successful, the following message will be displayed:


    `*****************************`   
    `Solver installed with oemof:`   
    
    `cbc: working`  
    `glpk: not working`  
    `gurobi: not working`  
    `cplex: not working`  
    
    `*****************************`  
    `oemof successfully installed.`  
    `*****************************`  
    
    
* **Provide input data.** 
The input data that needs to be provided differ from one model to another. 
How to handle the input data and how you can run the model with your 
own data is therefore described in the models individual readme-file.
* **Check settings in configuration file.** 
You find a configuration file (\*.yml) in the 
directory ./experiment_config/. 
It holds information and settings that are needed to run the program and 
solve the optimizations problem 
(e.g., solver settings, paths and file names of input data).
The config file specifies your experiment. 
Its structure and content differs for each model and is therefore described 
individually in each model file.
* **Run the program.**
 Open a terminal. 
 Navigate to the source code directory (/src/) of the model you like to run 
 (e.g., my-computer/path-to-downloaded-file/released_examples/flexCHP_SysOpt/src/). 
 Enter `python main.py`.
* **Get the results.**
See description in the models individual readme-file.
* **Find out what else can be modelled with *oemof*!**
The oemof-developer team provides several examples for applications on there 
GitHub repository: 
[github.com/oemof/oemof-examples](https://github.com/oemof/oemof-examples). 



## License

 Copyright (C) 2017 Beuth Hochschule für Technik Berlin and Reiner Lemoine Institut gGmbH
 
 This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as  published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
 
 This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License along with this program. If not, see http://www.gnu.org/licenses/.
