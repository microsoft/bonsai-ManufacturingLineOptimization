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
| Observations           | Conveyors speed, machines speed, machines_state infeed and discharge proxes, sink_machines_rate, sink_throughput_delta_sum, illegal_machine_actions, illegal_conveyor_actions, remaining_downtime_machines, control_delta_t | Proxes are sensors that yield a binary value. When product accumulates on the conveyor and covers the location of the prox sensor, its value becomes 1, otherwise it's value is zero, illegal actions happen with machines are in down or idle mode but brain sends a nonzero action, which will be ignored by the simulator but will return a flag to inform brain, remaining_downtime informs brain about remaining downtime for each machine. Active or idle machines yield zero for the their remaining downtime. sink_throughput_delta_sum is the amount of productions(throughput) between control actions, machine state -1 means down, 0 means idle, 1 means active|
| Actions                |  Machines | Speeds are processed in cans/second units|
| Control Frequency      | Fixed, event driven, or mix of both fixed and event driven control  | User can specify control frequency from inkling using |
| Episode configurations | control_type (fixed, event driven, or mix of both), control_frequency (for fixed and mix), inter_downtime_event_mean (average time between downtime events),inter_downtime_event_dev, downtime_event_duration_mean, downtime_event_duration_dev, number_parallel_downtime_events, layout_configuration |Note: currently only one default layout is supported. |

## Solution approach
4 solutions approaches are being tested. 
approach 1: fixed time control frequency with illegal actions. 
approach 2: event driven with no illegal actions.
approach 3: multi concept, equipment down concepts 
approach 4: Action space reduction 

## Background about manufacturing line

The line consists of a fixed number of machines that are connected through conveyors. The products (i.e., cans) enter the line through the source that is located at the left most side of the line, move from one machine to another machine until they reach the sink at the rightmost end of the line where all the product would be accumulated. There are sensors (proxes) located at certain points along the conveyor that assess the status of products (i.e., cans) accumulation on the conveyor. The prox that is located at the right end of conveyor (prior to next machine) is called the Infeed prox and the prox that is located at the left end of conveyor (after the previous machine) is called the Discharge prox. The Infeed prox decides whether there are enough products (i.e., cans) on the conveyor that can be fed into the next machine to determine whether it is worth keeping the machine ON. If there are not enough products (i.e., cans) available that can be fed into the next machine, then the Infeed prox would decide to shut down the machine simply because the conveyor is under-loaded.
In contrary, the Discharge prox decides whether there are too many products (i.e., cans) on the conveyor such that the previous machine would not find enough space on the conveyor to generate new products (i.e., cans). Therefore, the Discharge prox would decide to shut down the machine simply because the conveyor is over-loaded.

Each conveyor consists of 10 bins - indexed from 0 to 9 - and the products (i.e., cans) are accumulated from the right end of conveyor (bin index 9) until it reaches to the left end of conveyor (bin index 0). In the following, the process of how products (i.e., cans) are moved from one machine to another machine is explained.


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