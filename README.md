# Train brain for an optimal control of a manufacturing line 

## Bussiness problem

Manufacturing lines operate a series of machines to make specific product. Ocasiaonally, one or multiple machines go down (caused by jamming, hardware issues, etc.) which will not only slow down the production but also will impact the operation of the other machines throughout the line. The aim is to train a brain that learns how to orchestrate the machines in order to maximize the production in face of such down incidents.

<img src="img\mlo-line-basic.png" alt="drawing" width="700"/>

## Background about manufacturing lines

In a manufacturing line, the raw materials enter the line through the source that is located at the left end of the line, move from one machine to another machine through conveyors until they reach the rightmost end of the line where all the final products would be accumulated in the sink. There are proxes (sensors) located at certain points along the conveyor that assess the status of product accumulation on the conveyor. The prox that is located at the right end of conveyor (prior to next machine) is called the infeed prox and the prox that is located at the left end of conveyor (after the previous machine) is called the discharge prox. The infeed prox decides whether there are enough products on the conveyor that can be fed into the next machine to determine whether it is worth keeping the machine ON. If there are not enough products available to be fed into the next machine, then the infeed prox would decide to shut down the machine simply because the conveyor is under-loaded.
In contrary, the discharge prox decides whether there are too many products on the conveyor such that the previous machine would not find enough space on the conveyor to output new products. Therefore, the discharge prox would decide to shut down the machine simply because the conveyor is over-loaded. It is important to mention that there is no knwoledge of exact number of products on the conveyors and status of proxes is the only available information to determine the relative fullness/emptiness of the conveyors.
Train brain to control the speeds of the machine in a manufacturing line for maximum throughput.

<img src="img\Manufactuing_line_layout.PNG" alt="drawing" width="900"/>

## Background about manufacturing line

The line consists of a fixed number of machines that are connected through conveyors. The products (i.e., cans) enter the line through the source that is located at the left most side of the line, move from one machine to another machine until they reach the sink at the right most end of the line where all the products would be accumulated. There are sensors (proxes) located at certain points along the conveyor that assess the status of products (i.e., cans) accumulation on the conveyor. Product accumulation on the conveyor happens from **right to left**.

In general, there are two types of proxes. The proxes that are located towards the right end of conveyor (prior to next machine) is called the Infeed proxes and the proxes that are located towards the left end of conveyor (after the previous machine) are called the Discharge prox. The Infeed proxes decide whether there are enough products (i.e., cans) on the conveyor that can be fed into the next machine to determine whether it is worth keeping the machine ON. If there are not enough products (i.e., cans) available that can be fed into the next machine, then the Infeed proxes would decide to shut down the machine simply because the conveyor is under-loaded. In contrary, the Discharge proxes decide whether there are too many products (i.e., cans) on the conveyor such that the previous machine would not find enough space on the conveyor to process new products (i.e., cans). Therefore, the Discharge proxes would decide to shut down the machine simply because the conveyor is over-loaded.

Specifically, on each conveyor, there are two proxes on the Infeed side and there are two proxes on the Discharge side. The two at the Discharge are called “Discharge Low” and “Discharge Backup”. The prox that is right adjacent to the previous machine is the “Discharge Backup” prox and the other one is called the “Discharge Low”. If the cans are accumulating, the cans first activate the “Discharge Low” prox and then as more cans are accumulated, they activate the “Discharge Backup” prox. The previous machine will be shut down when it activates the “Discharge Backup” prox. In other words, when the “Discharge Low” prox is activated, it is indicating that there are too many cans on the conveyor and if you keep running the machines at the current speeds, you will start overloading the conveyor which will be causing a lot of problems. That is why we always want to keep the Discharge proxes empty. The “Discharge Low” prox warns that cans are starting to accumulate in order to start slowing down/speeding up the previous/next machine at a local level.
For restarting the machine, the number of cans accumulated on the conveyor must fall below a certain threshold and therefore, both “Discharge Backup” prox and “Discharge Low” prox must be deactivated.

Similarly, the two at the Infeed are called “Infeed Prime” and “Infeed Low”. The prox that is adjacent to the machine is the “Infeed Prime” prox and the other one is called the “Infeed Low”. When the conveyor is being depleted, at first the “Infeed Low” prox is activated and then as more cans are processed and the conveyor is further depleted, the “Infeed Prime” prox is activated. The machine is shut down when it activates the “Infeed Prime” prox. In other words, when the “Infeed Low” prox is activated, it is indicating that there are not enough cans on the conveyor and if you keep depleting the conveyor (or running the machines at current speeds), you will start underloading the conveyor. Eventually, the “Infeed Prime” will be activated and the next machine will be shut down. That is why we always want to keep the Infeed proxes full. The “Infeed Low” prox warns the machine that conveyor is being depleted and so the previous/next machines need to start speeding up/slowding down at a local level. For restarting the machine, the number of cans accumulated on the conveyor must exceed a certain threshold and therefore, both “Infeed Prime” prox and “Infeed Low” prox must be deactivated.

Note that we don't have access to the exact number of products (i.e., cans) on the conveyor and the proxes are used to estimate the approximate number of products (i.e., cans) that exist on the conveyor.

## Accumulation of products on the conveyor

## Conveyor model

To model the conveyor, it is assumed that each conveyor consists of N consecutive bins - indexed from 0 to N-1 - where each bin has a maximum capacity (i.e., 100 products) and the accumulation of products on the conveyor happens from the right end of conveyor (bin index N-1) until it reaches to the left end of conveyor (bin index 0). Note that the conveyors operate at a much higher speed than the machines, thus the conveyors do not pose a practical limitation on the ability of the machines to process products at their respective highest operating speeds.

<img src="img\mlo-line-prox.png" alt="drawing" width="700"/>

## Objectives

Maximize the production in a manufacturing line.  


|                        | Definition                                                   | Notes |
| ---------------------- | ------------------------------------------------------------ | ----- |
| Objective              | maximize the production     |   example: for a can manufacturing line, the goal is to maximize the can production                        |
| Constraints            |   NA |
| Observations           | machines actual running speed, brain choice of machines speed, status of the machines, status of infeed and discharge proxes | simulator can overwite the controller choice of speed based on product availabiloty and conveyor remaining empty space |
| Actions                | machine speeds | speeds are processed in products/time unit |
| Control Frequency      | fixed, event driven, or mix of both fixed and event driven control  | user can specify control frequency from Inkling |
| Episode Configurations | control type (fixed, event driven, or mix of both), control frequency (for fixed and mix), average and standard deviation of time between downtime events, average and standard deviation of duration of downtime events, duration of startup time, number of parallel down machines, layout configuration, location of infeed and discharge proxes, activation threshold for infeed and discharge proxes, initial level of conveyor bins, intial speed of the machines | Note: currently only one default layout is supported |

## Solution approach

## Challenges with current solutions

<img src="img\Line_Proxes.png" alt="drawing" width="600"/>

Current solutions suffer from the fact that they are too local which means that in case of a down incident they only try to control the immediately neighboring machines and they lack a global view of the entire manufacturing line. As a result, they would lead to more overloading / underloading of conveyors which in turn results in more machines going idle which eventually increases the chances of machines going down.

## Brain experimental card 

We assume there are six (or twelve for a more challenging sceanrio) machines that are located periodically along a manufacturing line that perform various types of operations (packaging, labeling, cleaning, filling, washing, etc.) on the products that being manufactured.

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

### Detailed overview of the solution


## Brain experimental card 

|                        | Definition                                                   | Notes |
| ---------------------- | ------------------------------------------------------------ | ----- |
| State                  | machines_state: number [6], machines_actual_speed: number[6], brain_speed: number[6], conveyor_infeed_m1_prox_empty: number[5], conveyor_infeed_m2_prox_empty[5]: number, conveyor_discharge_p1_prox_full[5]: number, conveyor_discharge_p2_prox_full: number[5] | number of conveyors is one less than number of machines, simulator can overwite the brain choice of speed so machine_actual_speed can be different from brain_speed
| Terminal               |  NA       |   -   |
| Action                 |  m0: number<machine_min_speed[0] .. machine_max_speed[0]>, m1: number<machine_min_speed[1] .. machine_max_speed[1]>, m2: number<machine_min_speed[2] .. machine_max_speed[2]>, m3: number<machine_min_speed[3] .. machine_max_speed[3]>, m4: number<machine_min_speed[4] .. machine_max_speed[4]>, m5: number<machine_min_speed[5] .. machine_max_speed[5]> | machines are not identical and each machine has its corresponding speed operating range |
| Reward or Goal         |  described below     |  -  |
| Episode configurations | interval_downtime_event_mean = 15, interval_downtime_event_dev = 10, downtime_event_duration_mean = 4, downtime_event_duration_dev = 3, idletime_duration_min = 2, idletime_duration_max = 12, number_parallel_downtime_events = 3, down_machine_index = -1, const min_bin_level = 0, max_bin_level = 100, num_conveyor_bins = 10, machine_min_speed = [100, 30, 60, 40, 80, 80], machine_max_speed = [170, 190, 180, 180, 180, 300], infeed_limit = 50, discharge_limit = 50, infeedProx_index1 = 1, infeedProx_index2 = 4, dischargeProx_index1 = 0, dischargeProx_index2 = 3, alpha = 0.3, conveyor_penalty = 1, idle_penalty = -1                     | the initial speed of each machine is randomly selected between its corresponding minimum and maximum operating speed  |

## Reward function

To maximize the total production at the sink, we aim to maximize the number of products processed by each machine as that would eventually lead to maximum number of final products at the sink. Maximization of the number of products processed by each machine is directly related to the operating speed of the machine, hence, the higher the operating speed, the larger the number of products that are manufactured by the machine. However, operating at a higher speed comes at the cost of over-loading / under-loading the neighboring conveyors and can lead to frequent machine shut-downs by the infeed/discharge proxes. Therefore, the optimization problem can be formulated as the maximization of operating speed of each machie subject to minimization of instants that the machine is shut down (goes idle).

```
# Machine receives higher reward when operates at higher speed


# number of products after each machine
# return 0 if down or idle
function machine_output(state: SimState) {
    var machine_throughput_scaled = (state.machines_actual_speed - machine_min_speed) / (machine_max_speed - machine_min_speed) 
    var machine_throughput = Math.E ** (machine_throughput_scaled)
    if state.machines_actual_speed[8] == 0 {
        return 0
    }
    if state.conveyor_infeed_m2_prox_empty == 1 or state.conveyor_discharge_p2_prox_full == 1 {
        var machine_reward = machine_throughput - alpha * conveyor_penalty
        return  machine_reward
    }
    return machine8_throughput 
}

```

## Brain training
## Results of brain training

### Create a new brain on bonsai platfrom  
Use machine_teacher.ink that employs the following example configuration.


### Before you start 

- Create a conda environment using the environment.yml file.
```bash
conda env update -f environment.yml 
```
The sim folder contains two main simulator scripts. 
- The line_config.py script that is used to set up the configiration of the manufacturing line. The parameter K determines the number of machines on the line and you could change it to setup a line with your desirable number of machines (i.e., 6 or 12).
- The manufacturing_env.py script that calls the line_config.py and then adds the specificities of manufacturing lines.

### Dockerize Simulator for Scaling and add the sim package

Sim integration with bonsai platform requires you to change directory to the parent directory, where docker file Dockerfile is located.

```
docker build -t <IMAGE_NAME> -f Dockerfile-tsp .
az acr login --subscription <SUBSCRIPTION_ID> --name <ACR_REGISTRY_NAME
docker tag <IMAGE_NAME> <ACR_REGISTRY_NAME>.azurecr.io/bonsai/<IMAGE_NAME>
docker push <ACR_REGSITRY_NAME>.azurecr.io/bonsai/<IMAGE_NAME>
```
Note: if you don't have docker installed in your local machine, you may use "az acr build" command to build the docker image. 

### Create a new brain on bonsai platfrom  

After you created a brain, use machine_teacher.ink and make sure to use the following values for the configuration parameters.

| Episode configuration parameter  | value |
| ---------------------- |----- |
| simulation_time_step   |  1 |
| control_type           |  0 |
| control_frequency      |  1 |
| number_of_iterations   |  100 |     


Once pushed, you must add the simulator in the Web UI. After added, to scale with multiple simulators, one can select the simulation to scale in two ways:

1) write `package "<SimName>"` in the simulator clause in inkling.
2) click the Train button and select the simulator from the dropdown list.
   
### Train Brain

<img src="img/learning-curve.png" alt="drawing" width="700"/> 

### Asses the results and comparison with benchmark 

### Assessment


To assess the trained brain:

(1) Create a custom assessment session from the Web UI. (2) Query the assessment results and compare it with heuristics based benchmarks. Note that you can use custom assessment found in `assessments` folder for various down events scenarios.

#### Comparison with Benchmark 

In this section, we will use a heuristic as benchmark where each machine runs at its own maximum operating speed in order to maximize the line production. Since the current euristic solutions aim to run the machines at max speed, it would cause the machines to go into idle mode (speed of 0) more frequently due to underloading/overloading of the conveyors. Note that more idle instances would also lead to more startup instances because any disruption in line operation propagates from one machine to another machine and hence would reduce the overal throughput of the line.

<img src="img\mlo-1.png" alt="drawing" width="350"/>
### Comparison with Benchmark 

<img src="img\mlo-2.png" alt="drawing" width="350"/>

On the other hand, brain learns to react to machine down events (i.e., jamming) by intelligently adjust the speed of the machines. Such adjustment of speed by the brain would avoid underloading/overloading the conveyors. Therefore, the proxes wouldn't need to shut down the machines as often and so the number of idle instances would drastically decrease. Machines would remian in active mode for much longer duration, thus, the brain is able to increase the total production by 8.49%.


<img src="img\histogram.png" alt="drawing" width="350"/>

<img src="img\histogram_speed.png" alt="drawing" width="350"/>

```sh
docker run -d -p 5000:5000 <acr_name>.azurecr.io/<workspace_id>/<brain_name>:<version>
python bonsai_integration.py --render --test
```
