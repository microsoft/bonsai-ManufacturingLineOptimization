# Train brain for an optimal control of a manufacturing line 

## Bussiness problem

Manufacturing lines operate a series of machines to make specific product. Ocasiaonally, one or multiple machines go down (caused by jamming, hardware issues, etc.) which will not only slow down the production but also will impact the operation of the other machines throughout the line. The aim is to train a brain that learns how to orchestrate the machines in order to maximize the production in face of such down incidents.

<img src="img\mlo-line-basic.png" alt="drawing" width="700"/>

## Background about manufacturing lines

In a manufacturing line, the raw materials enter the line through the source that is located at the left end of the line, move from one machine to another machine through conveyors until they reach the rightmost end of the line where all the final products would be accumulated in the sink. There are proxes (sensors) located at certain points along the conveyor that assess the status of product accumulation on the conveyor. The prox that is located at the right end of conveyor (prior to next machine) is called the infeed prox and the prox that is located at the left end of conveyor (after the previous machine) is called the discharge prox. The infeed prox decides whether there are enough products on the conveyor that can be fed into the next machine to determine whether it is worth keeping the machine ON. If there are not enough products available to be fed into the next machine, then the infeed prox would decide to shut down the machine simply because the conveyor is under-loaded.
In contrary, the discharge prox decides whether there are too many products on the conveyor such that the previous machine would not find enough space on the conveyor to output new products. Therefore, the discharge prox would decide to shut down the machine simply because the conveyor is over-loaded. It is important to mention that there is no knwoledge of exact number of products on the conveyors and status of proxes is the only available information to determine the relative fullness/emptiness of the conveyors.

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

Current solutions suffer from the fact that they are too local which means that in case of a down incident they only try to control the immediately neighboring machines and they lack a global view of the entire manufacturing line. As a result, they would lead to more overloading / underloading of conveyors which in turn results in more machines going idle which eventually increases the chances of machines going down.

## Brain experimental card 

We assume there are six	machines that are located periodically along a manufacturing line that perform various types of operations (packaging, labeling, cleaning, filling, washing, etc.) on the products that being manufactured.


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

function machine_output(state: SimState) {
    # if the machine is down or idle
    if state.machines_actual_speed == 0 {
        return 0
    }
    # otheriwse
    var machine_throughput_scaled = (state.machines_actual_speed - machine_min_speed) / (machine_max_speed - machine_min_speed) 
    var machine_throughput = machine_throughput_scaled ** 2
    return machine_throughput 
}
```

```
# Penalize the machine when goes into idle mode

function machine_status(state: SimState) {
    var machine_throughput = machine_output(state)
    # neither of primary infeed and promary discharge are activated
    if state.conveyor_infeed_m1_prox_empty == 0 and state.conveyor_discharge_p1_prox_full == 0 {
        # either of secondary infeed or secondary discharge is activated
        if state.conveyor_infeed_m2_prox_empty == 1 or state.conveyor_discharge_p2_prox_full == 1 {
            var machine_reward = machine_throughput - alpha * conveyor_penalty
            return  machine_reward
        }
        else {
            return machine2_throughput
        }
    }
    # if machine is down
    else if state.machines_state == -1 {
        return 0
    }
    # if machine is idle
    else {
        return idle_penalty
    }
}
```

## Brain training


### Before you start 

- Create a conda environment using the environment.yml file.
```bash
conda env update -f environment.yml 
```
The sim folder contains two main simulator scripts. 
- The line_config.py script that is used to set up the configiration of the manufacturing line. The parameter K determines the number of machines on the line and you could change it to setup a line with your desirable number of machines.
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

(1) Create a custom assessment session from the Web UI. (2) Query the assessment results and compare it with heuristics based benchmarks. Note that you can use custom assessment found in `assess_config_speed.json`. For details about query assessment, refer to the "assessment and benchmark comparison.ipynb" notebook located in bonsai-log-tools folder.

#### Comparison with Benchmark 

In this section, we will use a heuristic as benchmark where each machine runs at its own maximum operating speed in order to maximize the line production. Since the current euristic solutions aim to run the machines at max speed, it would cause the machines to go into idle mode (speed of 0) more frequently due to underloading/overloading of the conveyors. Note that more idle instances would also lead to more startup instances because any disruption in line operation propagates from one machine to another machine and hence would reduce the overal throughput of the line.

<img src="img\mlo-1.png" alt="drawing" width="350"/>

<img src="img\mlo-2.png" alt="drawing" width="350"/>

On the other hand, brain learns to react to machine down events (i.e., jamming) by intelligently adjust the speed of the machines. Such adjustment of speed by the brain would avoid underloading/overloading the conveyors. Therefore, the proxes wouldn't need to shut down the machines as often and so the number of idle instances would drastically decrease. Machines would remian in active mode for much longer duration, thus, the brain is able to increase the total production by 8.49%.


<img src="img\histogram.png" alt="drawing" width="350"/>

<img src="img\histogram_speed.png" alt="drawing" width="350"/>

