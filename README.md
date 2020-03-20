# BCore

BCore is a Behavior training library built originally for training rodents but is compatible with training any subject. It was built in MATLab originally but is now compatible with python.

### See [Getting Started guide](https://github.com/balajisriram/BCore/blob/master/Docs/0.GettingStartedWithBCore.md) for details on installing and using BCore

## TODO:
 - [ ] Plot compiled_record. Filter last 10000 trials.
 - [ ] RunForReward trials
 - [ ] Flip trial\_pin on trial\_start in do\_trials
 - [ ] ZMQ output
 - [ ] Is session manager in protocol? Or in subject? Which spot makes the most sense?
 - [ ] Force IP address for a given computer
 - [ ] decide on license and execute
 - [x] make module pip installable
 - [ ] configuration script
     - [x] identify as standalone, client or server
     - [x] save `bcore.config` to `get_config_path`
 - [ ] add $BCOREPATH to path
 - [ ] configuration setup for bserver and bclient
	 - [ ] specify base path. [See here](https://github.com/balajisriram/bcore/blob/master/bcore/docs/1.DataModelForBCore.md#2)
	 - [ ] create .bcore in the basepath to contain relevant cofguration details for the installation
	 - [ ] create bcore data paths as required [See here](https://github.com/balajisriram/bcore/blob/master/bcore/docs/1.DataModelForBCore.md#2)
 - [ ] How are heats implemented?
 - [ ] Trial data - how to operationalize saving previous data and current data: pandas adding records is super slow
 - [ ] setting up paths in BCore
	 - [x] `bcore.get_base_path`: Where `BCoreData` folder is placed. Determined by configuration script. DONE March 17 2020
	 - [x] `bcore.get_config_path`: Always below the bcore code base in a folder called `.bcore` which will contain `bcore.config`. DONE March 17 2020
	 - [ ] `bcore.get_codebase_path`: not sure what the use of this is