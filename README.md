# Train brain for an optimal control of a Manufacturing line 

## Bussiness problem
Train brain to control machine and conveyor speed of a manufacturing line for maximum throughput.
<img src="img\Manufactuing_line_layout.PNG" alt="drawing" width="900"/>

## Objectives
Maximize production in a manufacturing line.  

|                        | Definition                                                   | Notes |
| ---------------------- | ------------------------------------------------------------ | ----- |
| Objective              | maximize product production     |   Example: For a can manufacturing line, the goal is to maximize can production                        |
| Constraints            |   NA |
| Observations           | Conveyors speed, machines speed, infeed and discharge proxes, sink_machines_rate, sink_throughput_delta_sum, illegal_machine_actions, illegal_conveyor_actions, remaining_downtime_machines, control_delta_t | Proxes are sensors that yield a binary value. When product accumulates on the conveyor and covers the location of the prox sensor, its value becomes 1, otherwise it's value is zero, illegal actions happen with machines are in down or idle mode but brain sends a nonzero action, which will be ignored by the simulator but will return a flag to inform brain, remaining_downtime informs brain about remaining downtime for each machine. Active or idle machines yield zero for the their remaining downtime. sink_throughput_delta_sum is the amount of productions(throughput) between control actions|
| Actions                |  Machines and conveyors speed | Speeds are processed in cans/second units|
| Control Frequency      | Fixed, event driven, or mix of both fixed and event driven control  | User can specify control frequency from inkling using |
| Episode configurations | control_type (fixed, event driven, or mix of both), control_frequency (for fixed and mix), inter_downtime_event_mean (average time between downtime events),inter_downtime_event_dev, downtime_event_duration_mean, downtime_event_duration_dev, number_parallel_downtime_events, layout_configuration |Note: currently only one default layout is supported. |

## Solution approach
4 solutions approaches are being tested. 
approach 1: fixed time control frequency with illegal actions. 
approach 2: event driven with no illegal actions.
approach 3: multi concept, equipment down concepts 
approach 4: Action space reduction 


### Detailed overview of the solution

### TODO


## Brain experimental card 
### TO be completed soon 
,
|                        | Definition                                                   | Notes |
| ---------------------- | ------------------------------------------------------------ | ----- |
| State                  |       |
| Terminal               |          |       |
| Action                 |                   |       |
| Reward or Goal         |       |     |
| Episode configurations |                      |       |

*note: Episode configurations are described more in the results section  



## Results of brain training
### Create a new brain on bonsai platfrom  
Use machine_teacher.ink that employs the following example configuration:

|   Episode configuration parameter                     | value                                                 | Notes |
| ---------------------- | ------------------------------------------------------------ | ----- |
|            |      |                        |


### Dockerize Simulator for Scaling and add the sim package

```
docker build -t <IMAGE_NAME> -f Dockerfile .
az acr login --subscription <SUBSCRIPTION_ID> --name <ACR_REGISTRY_NAME
docker tag <IMAGE_NAME> <ACR_REGISTRY_NAME>.azurecr.io/bonsai/<IMAGE_NAME>
docker push <ACR_REGSITRY_NAME>.azurecr.io/bonsai/<IMAGE_NAME>
```
Add the simulator in the Web UI. To scale with multiple simulators, one can select the simulation to scale in two ways:

1) write `package "<SimName>"` in the simulator clause in inkling
2) click the Train button and select the simulator
   
### Train Brain

<!-- <img src="img/.PNG" alt="drawing" width="900"/> -->


### Assess the results
(see assessment section in the appendix for details of the process)

#### Comparison with Benchmark 


<!-- <img src="img/.PNG" alt="drawing" width="900"/> -->



### Assessment

You can use custom assessment found in `assess_configs/myConfig.json`. 


TODO: Run the simulation with rendering using the following flag. If you add the `--test` flag, you will run using an exported brain with `http://localhost:5000`.

```sh
docker run -d -p 5000:5000 <acr_name>.azurecr.io/<workspace_id>/<brain_name>:<version>
python bonsai_integration.py --render --test
```