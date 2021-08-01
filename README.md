# Train brain for an optimal control of a Manufacturing line 

## Bussiness problem
Train brain to control the speeds of the machine in a manufacturing line for maximum throughput.

<img src="img\Manufactuing_line_layout.PNG" alt="drawing" width="900"/>

## Background about manufacturing line

The line consists of a fixed number of machines that are connected through conveyors. The products (i.e., cans) enter the line through the source that is located at the left most side of the line, move from one machine to another machine until they reach the sink at the right most end of the line where all the products would be accumulated. There are sensors (proxes) located at certain points along the conveyor that assess the status of products (i.e., cans) accumulation on the conveyor. Product accumulation on the conveyor happens from **right to left**.

In general, there are two types of proxes. The proxes that are located towards the right end of conveyor (prior to next machine) is called the Infeed proxes and the proxes that are located towards the left end of conveyor (after the previous machine) are called the Discharge prox. The Infeed proxes decide whether there are enough products (i.e., cans) on the conveyor that can be fed into the next machine to determine whether it is worth keeping the machine ON. If there are not enough products (i.e., cans) available that can be fed into the next machine, then the Infeed proxes would decide to shut down the machine simply because the conveyor is under-loaded. In contrary, the Discharge proxes decide whether there are too many products (i.e., cans) on the conveyor such that the previous machine would not find enough space on the conveyor to process new products (i.e., cans). Therefore, the Discharge proxes would decide to shut down the machine simply because the conveyor is over-loaded.

Specifically, on each conveyor, there are two proxes on the Infeed side and there are two proxes on the Discharge side. The two at the discharge are called “Discharge Low” and “Discharge Backup”. The prox that is right adjacent to the previous machine is the “Discharge Backup” prox and the other one is called the “Discharge Low”. If the cans are accumulating, the cans first activate the “Discharge Low” prox and then as more cans are accumulated, they activate the “Discharge Backup” prox. The previous machine will be shut down when it activates the “Discharge Backup” prox. In other words, when the “Discharge Low” prox is activated, it is indicating that there are too many cans on the conveyor and if you keep running the machine, you will start overloading the conveyor which will be causing a lot of problems. That is why we always want to keep the discharge proxes to be empty. The “Discharge Low” prox warns the previous machine that cans are starting to accumulate in order to start slowing down the previous machine at a local level.
For restarting the machine, the number of cans accumulated on the conveyor must fall below a certain threshold and therefore, both “Discharge Backup” prox and “Discharge Low” prox must be deactivated.

Similarly, the two at the Infeed are called “Infeed Prime” and “Infeed Low”. The prox that is adjacent to the machine is the “Infeed Prime” prox and the other one is called the “Infeed Low”. When the conveyor is being depleted, at first the “Infeed Low” prox is activated and then as more cans are processed and the conveyor is further depleted, the “Infeed Prime” prox is activated. The machine is shut down when it activates the “Infeed Prime” prox. In other words, when the “Infeed Low” prox is activated, it is indicating that there are not enough cans on the conveyor and if you keep depleting the conveyor (or run the next machine at high speed), you will start underloading the conveyor. Eventually, the “Infeed Prime” will be activated and the next machine will be shut down. That is why we always want to keep the Infeed proxes to be full. The “Infeed Low” prox warns the machine that conveyor is being depleted and so the next machines need to start slowding down at a local level. For restarting the machine, the number of cans accumulated on the conveyor must exceed a certain threshold and therefore, both “Infeed Prime” prox and “Infeed Low” prox must be deactivated.

To model the conveyor, it is assumed that each conveyor consists of N bins - indexed from 0 to N-1 - and the accumulation of products (i.e., cans) on the conveyor happens from the right end of conveyor (bin index N-1) until it reaches to the left end of conveyor (bin index 0). In the following, the process of how products (i.e., cans) are moved along the conveyor from one machine to another machine is explained.

For sake of explanation, it is assumed that the product of interest is "can" and that the conveyor has a capacity of 1000 and it consists of 10 bins (N = 10) and, therefore, each bin has a maximum capacity of 100. Let's also assume that the each bin initially contains 50 cans. Note that conveyor operates at a much higher speed than the machines, thus the conveyor speed is not a limiting factor in the movement of cans from one machine to another machine. 

|             | Speed | 
| ----------- | ----- | 
| conveyor    | 2000  |
| machine 1   |  100  |
| machine 2   |  40   |

At time 0, the last bin (bin # 9) of machine 1 passes 40 cans out of its current 50 cans to machine 2 because machine 2 can only process 40 cans per minute - it has a speed of 40 cans per minute. Simultaneously, machine 1 processes 100 cans and aims to place them in the last bin (bin # 9) of the conveyor since product accumulation happens from the last bin of the conveyor. However, since bin # 9 already containts 10  cans, it can only take 90 more cans to reach its maximum capacity of 100 cans. Therefore, the remaining 10 cans that have been processed by machine 1 would be placed in bin # 8.

At time 1, the last bin (bin # 9) of machine 1 passes its 10 cans to machine 2. Simultaneously, machine 1 processes another set of 100 cans and places all the 100 cans in its last bin (bin # 9) since it is empty. Therefore, the last bin (bin # 9) contains 100 cans.

At time 2, the last bin (bin # 9) only passes 40 (out of its 100) cans to machine 2 since machine 2 can only process 40 cans at once. Machine 1 processes 100 cans and would like to place them in last bin (bin # 9). However, since last bin (bin # 9) is partially full, machine 1 can only place 40 cans in last bin (bin # 9) and the ramaining 60 cans are placed in bin # 8 which was already carrying 10 cans. Total level of bin # 8 is now increased to 70 cans.

This process will keep running and if can accumulation reaches the first bin (bin # 0), then the Discharge prox after machine 1 will decide to shut down machine 1 since it assumes that the conveyor is over-loaded.


## Objectives

Maximize production in a manufacturing line.  

|                        | Definition                                                   | Notes |
| ---------------------- | ------------------------------------------------------------ | ----- |
| Objective              | maximize product production     |   Example: For a can manufacturing line, the goal is to maximize can production                        |
| Constraints            |   NA |
| Observations           | machines speed, machines_state, brain_speed, machines_state_sum, conveyors_speed, conveyor_buffers, sink_machines_rate_sum, sink_throughput_delta_sum, sink_throughput_absolute_sum, conveyor_infeed_m1_prox_empty, conveyor_infeed_m2_prox_empty, conveyor_discharge_p1_prox_full, conveyor_discharge_p2_prox_full, illegal_machine_actions, remaining_downtime_machines, control_delta_t, env_time | Machines speed is the actual speed that was used by the simulator to run the machine, whereas brain speed is the speed that was decided by the brain. Proxes are sensors that yield a binary value. When product accumulates on the conveyor and covers the location of the prox sensor, its value becomes 1, otherwise it's value is zero. Illegal actions happen when machines are in down or idle mode but brain sends a nonzero action, which will be ignored by the simulator but will return a flag to inform brain. remaining_downtime informs brain about remaining downtime for each machine, and active or idle machines yield zero for the their remaining downtime. sink_throughput_delta_sum is the amount of productions(throughput) between control actions, machine state -1 means down, 0 means idle, 1 means active |
| Actions                | machines_speed | speeds are processed in cans/second units|
| Control Frequency      | fixed, event driven, or mix of both fixed and event driven control  | User can specify control frequency from inkling using |
| Episode configurations | control_type (fixed, event driven, or mix of both), control_frequency (for fixed and mix), inter_downtime_event_mean (average time between downtime events), inter_downtime_event_dev, downtime_event_duration_mean, downtime_event_duration_dev, number_parallel_downtime_events, layout_configuration, down_machine_index, initial_bin_level, bin_maximum_capacity, num_conveyor_bins, conveyor_capacity, machine_min_speed, machine_max_speed, machine_initial_speed, infeed_prox_upper_limit, infeed_prox_lower_limit, discharge_prox_upper_limit, discharge_prox_lower_limit, infeedProx_index1, infeedProx_index2, dischargeProx_index1, dischargeProx_index2 | Note: currently only one default layout is supported. |

Noet that the Bonsai brain has full control of machines speed until the “Discharge Backup” is activated. When the “Discharge Backup” prox is activated, the traditional control system (and not the Bonsai brain) will shut down the machine and put it in idle mode. However, the brain needs to know that when a machine is shut down as a non-ideal condition. Note that since the machine is shut down, the brain is not able to send speed commands to the machine anymore.


## Solution approach
4 solutions approaches are being tested. 
approach 1: fixed time control frequency with illegal actions. 
approach 2: event driven with no illegal actions.
approach 3: multi concept, equipment down concepts 
approach 4: Action space reduction 


<img src="img\Line_Proxes.png" alt="drawing" width="900"/>

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
