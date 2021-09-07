inkling "2.0"
using Number
using Math
using Goal

## define constants, part of sim config 
const number_of_iterations = 100
const simulation_time_step = 1 # unitless

## control type: -1: control at fixed time frequency but no downtime event 
## control_type:  0: control at fixed time frequency 
## control type:  1: event driven, i.e. when a downtime occurs
## control type:  2: both at fixed control frequency and downtime
const control_type = 0 # 0 or -1 for this project
## the below control frequency does not apply to control type 1 and will be ignored
const control_frequency = 1 # in seconds (s)

## Downtime event config 
## a random interval_downtime_event is generated in the range [interval_downtime_event_mean - interval_downtime_event_dev, interval_downtime_event_mean + interval_downtime_event_dev]
## a random downtime duration is generated in the range [downtime_event_duration_mean - downtime_event_duration_std, downtime_event_duration_mean + downtime_event_duration_std]
const interval_downtime_event_mean = 15 # seconds (s) 
const interval_downtime_event_dev = 10 #  seconds (s) 
const downtime_event_duration_mean = 4 # seconds (s),  
const downtime_event_duration_dev = 3 # seconds (s)
## The following indicate possibility of multiple machines going down in parallel and at overlapping times
## 1 means 0 or 1 machine may go down at any point in time
## 2 means: 0, or 1 or 2 machines may go down at any point in time
## n means: 0 upto n machines may go down at any point in time.
const number_parallel_downtime_events = 3

## plant layout
## Currently only 1 configuration exists 
const layout_configuration = 1

const down_machine_index = -1 # It can be from -1 for random machine down or 0 to 5 for specific down machine

const bin_maximum_capacity = 100
const num_conveyor_bins = 10
const conveyor_capacity = num_conveyor_bins * bin_maximum_capacity
const machine_min_speed = [1, 2, 3, 4, 5, 6]
const machine_max_speed = [10, 20, 30, 40, 50, 60]

const infeed_prox_upper_limit = 50
const infeed_prox_lower_limit = 50
const discharge_prox_upper_limit = 50
const discharge_prox_lower_limit = 50

const infeedProx_index1 = 1
const infeedProx_index2 = 4
const dischargeProx_index1 = 0
const dischargeProx_index2 = 3

const num_cans_at_discharge_index1 = (num_conveyor_bins - dischargeProx_index1 - 1) * bin_maximum_capacity + discharge_prox_lower_limit
const num_cans_at_discharge_index2 = (num_conveyor_bins - dischargeProx_index2 - 1) * bin_maximum_capacity + discharge_prox_upper_limit

const num_cans_at_infeed_index1 = (infeedProx_index1 - 1) * bin_maximum_capacity + infeed_prox_lower_limit
const num_cans_at_infeed_index2 = (infeedProx_index2 - 1) * bin_maximum_capacity + infeed_prox_upper_limit

type SimState {
    machines_actual_speed: number[6], # actual running speed of the machines
    machines_state: number[6], # status of the machines - down, running, idle
    brain_speed: number[6], # brain choice of speed for the machines
    machines_state_sum: number,
    iteration_count: number, # iteration number
    conveyors_level: number[5],
    all_conveyor_levels_estimate: number[5], # estimates number of cans on the conveyor
    mean_downtime_offset: number[6], # offset from mean downtime
    max_downtime_offset: number[6], # offset from maximum downtime
    sink_throughput_absolute_sum: number, # absolute sum of all the productions at eny iteration
    conveyor_infeed_m1_prox_empty: number[5],
    conveyor_infeed_m2_prox_empty: number[5],
    conveyor_discharge_p1_prox_full: number[5],
    conveyor_discharge_p2_prox_full: number[5],
    control_delta_t: number,
    env_time: number,
}

type ObservationState {
    machines_state: number[6], # status of the machines - down, running, idle
    machines_actual_speed: number[6], # actual running speed of the machines
    brain_speed: number[6], # brain choice of speed for the machines
    # mean_downtime_offset: number[6], # offset from mean downtime
    # max_downtime_offset: number[6], # offset from maximum downtime
    conveyor_infeed_m1_prox_empty: number[5],
    conveyor_infeed_m2_prox_empty: number[5],
    conveyor_discharge_p1_prox_full: number[5],
    conveyor_discharge_p2_prox_full: number[5],
}

# multiarm bandit actions. 
type SimAction {
    m0: number<machine_min_speed[0] .. machine_max_speed[0] step 1>,
    m1: number<machine_min_speed[1] .. machine_max_speed[1] step 1>,
    m2: number<machine_min_speed[2] .. machine_max_speed[2] step 1>,
    m3: number<machine_min_speed[3] .. machine_max_speed[3] step 1>,
    m4: number<machine_min_speed[4] .. machine_max_speed[4] step 1>,
    m5: number<machine_min_speed[5] .. machine_max_speed[5] step 1>,
}

type SimConfig {
    simulation_time_step: simulation_time_step,
    control_type: control_type,
    control_frequency: control_frequency, 
    interval_downtime_event_mean: interval_downtime_event_mean,  
    interval_downtime_event_dev: interval_downtime_event_dev,
    downtime_event_duration_mean: downtime_event_duration_mean,   
    downtime_event_duration_dev: downtime_event_duration_dev,  
    number_parallel_downtime_events: number_parallel_downtime_events,
    layout_configuration: layout_configuration, 
    down_machine_index: down_machine_index,
    initial_bin_level: number,
    bin_maximum_capacity: bin_maximum_capacity,
    num_conveyor_bins: num_conveyor_bins,
    conveyor_capacity: conveyor_capacity,
    machine0_min_speed: number,
    machine1_min_speed: number,
    machine2_min_speed: number,
    machine3_min_speed: number,
    machine4_min_speed: number,
    machine5_min_speed: number,
    machine0_max_speed: number,
    machine1_max_speed: number,
    machine2_max_speed: number,
    machine3_max_speed: number,
    machine4_max_speed: number,
    machine5_max_speed: number,
    machine0_initial_speed: number,
    machine1_initial_speed: number,
    machine2_initial_speed: number,
    machine3_initial_speed: number,
    machine4_initial_speed: number,
    machine5_initial_speed: number,
    infeed_prox_upper_limit: infeed_prox_upper_limit,
    infeed_prox_lower_limit: infeed_prox_lower_limit,
    discharge_prox_upper_limit: discharge_prox_upper_limit,
    discharge_prox_lower_limit: discharge_prox_lower_limit,
    infeedProx_index1: infeedProx_index1,
    infeedProx_index2: infeedProx_index2, 
    dischargeProx_index1: dischargeProx_index1, 
    dischargeProx_index2: dischargeProx_index2,
    num_cans_at_discharge_index1: num_cans_at_discharge_index1,
    num_cans_at_discharge_index2: num_cans_at_discharge_index2,
    num_cans_at_infeed_index1: num_cans_at_infeed_index1,
    num_cans_at_infeed_index2:num_cans_at_infeed_index2,
}

# number of cans after machine 0
# return 0 if down or idle
function machine0_output(state: SimState) {
    var machine0_throughput_scaled = state.machines_actual_speed[0] / machine_max_speed[0] # normalized number of cans processed by the machine 0
    var machine0_throughput = machine0_throughput_scaled ** 10
    return machine0_throughput
}

# number of cans after machine 1
# return 0 if down or idle
function machine1_output(state: SimState) {
    var machine1_throughput_scaled = state.machines_actual_speed[1] / machine_max_speed[1] # normalized number of cans processed by the machine 1
    var machine1_throughput = machine1_throughput_scaled ** 10
    return machine1_throughput
}

# number of cans after machine 2
# return 0 if down or idle
function machine2_output(state: SimState) {
    var machine2_throughput_scaled = state.machines_actual_speed[2] / machine_max_speed[2] # normalized number of cans processed by the machine 2
    var machine2_throughput = machine2_throughput_scaled ** 10
    return machine2_throughput
}

# number of cans after machine 3
# return 0 if down or idle
function machine3_output(state: SimState) {
    var machine3_throughput_scaled = state.machines_actual_speed[3] / machine_max_speed[3] # normalized number of cans processed by the machine 3
    var machine3_throughput = machine3_throughput_scaled ** 10
    return machine3_throughput
}

# number of cans after machine 4
# return 0 if down or idle
function machine4_output(state: SimState) {
    var machine4_throughput_scaled = state.machines_actual_speed[4] / machine_max_speed[4] # normalized number of cans processed by the machine 4
    var machine4_throughput = machine4_throughput_scaled ** 10
    return machine4_throughput
}

# number of cans after machine 5
# return 0 if down or idle
function machine5_output(state: SimState) {
    var machine5_throughput_scaled = state.machines_actual_speed[5] / machine_max_speed[5] # normalized number of cans processed by the machine 5
    var machine5_throughput = machine5_throughput_scaled ** 10
    return machine5_throughput
}


function Reward(state: SimState) {

    var reward_machine0 = machine0_output(state)
    var reward_machine1 = machine1_output(state)
    var reward_machine2 = machine2_output(state)
    var reward_machine3 = machine3_output(state)
    var reward_machine4 = machine4_output(state)
    var reward_machine5 = machine5_output(state)

    var reward_total = reward_machine0 + reward_machine1 + reward_machine2 + reward_machine3 + reward_machine4 + reward_machine5
    return reward_total
}

simulator Simulator(action: SimAction, config: SimConfig): SimState {
    # package "MLO0420"
}

graph (input: ObservationState): SimAction {

    concept optimize(input): SimAction {
        curriculum {
            algorithm {
                Algorithm: "SAC",
                #BatchSize: 8000,
                #PolicyLearningRate: 0.001
            }
            source Simulator
            reward Reward
            # terminal Terminal
            training {
                EpisodeIterationLimit: number_of_iterations,
                NoProgressIterationLimit: 500000
            }
            lesson `learn 1` {
                scenario {
                    simulation_time_step: simulation_time_step,
                    control_type: control_type,
                    control_frequency: control_frequency,
                    interval_downtime_event_mean: interval_downtime_event_mean,
                    interval_downtime_event_dev: interval_downtime_event_dev,
                    downtime_event_duration_mean: downtime_event_duration_mean,
                    downtime_event_duration_dev: downtime_event_duration_dev,
                    number_parallel_downtime_events: number_parallel_downtime_events,
                    layout_configuration: layout_configuration,
                    down_machine_index: down_machine_index,
                    initial_bin_level: number< 1 .. 100 step 1>,
                    bin_maximum_capacity: bin_maximum_capacity,
                    num_conveyor_bins: num_conveyor_bins,
                    conveyor_capacity: conveyor_capacity,

                    machine0_min_speed: number<machine_min_speed[0] .. machine_min_speed[0] step 1>,
                    machine1_min_speed: number<machine_min_speed[1] .. machine_min_speed[1] step 1>,
                    machine2_min_speed: number<machine_min_speed[2] .. machine_min_speed[2] step 1>,
                    machine3_min_speed: number<machine_min_speed[3] .. machine_min_speed[3] step 1>,
                    machine4_min_speed: number<machine_min_speed[4] .. machine_min_speed[4] step 1>,
                    machine5_min_speed: number<machine_min_speed[5] .. machine_min_speed[5] step 1>,
                    
                    machine0_max_speed: number<machine_max_speed[0] .. machine_max_speed[0] step 1>,
                    machine1_max_speed: number<machine_max_speed[1] .. machine_max_speed[1] step 1>,
                    machine2_max_speed: number<machine_max_speed[2] .. machine_max_speed[2] step 1>,
                    machine3_max_speed: number<machine_max_speed[3] .. machine_max_speed[3] step 1>,
                    machine4_max_speed: number<machine_max_speed[4] .. machine_max_speed[4] step 1>,
                    machine5_max_speed: number<machine_max_speed[5] .. machine_max_speed[5] step 1>,
                    
                    machine0_initial_speed: number<machine_min_speed[0] .. machine_max_speed[0] step 1>,
                    machine1_initial_speed: number<machine_min_speed[1] .. machine_max_speed[1] step 1>,
                    machine2_initial_speed: number<machine_min_speed[2] .. machine_max_speed[2] step 1>,
                    machine3_initial_speed: number<machine_min_speed[3] .. machine_max_speed[3] step 1>,
                    machine4_initial_speed: number<machine_min_speed[4] .. machine_max_speed[4] step 1>,
                    machine5_initial_speed: number<machine_min_speed[5] .. machine_max_speed[5] step 1>,

                    infeed_prox_upper_limit: infeed_prox_upper_limit,
                    infeed_prox_lower_limit: infeed_prox_lower_limit,
                    discharge_prox_upper_limit: discharge_prox_upper_limit,
                    discharge_prox_lower_limit: discharge_prox_lower_limit,
                    infeedProx_index1: infeedProx_index1,
                    infeedProx_index2: infeedProx_index2,
                    dischargeProx_index1: dischargeProx_index1,
                    dischargeProx_index2: dischargeProx_index2,
                    num_cans_at_discharge_index1: num_cans_at_discharge_index1,
                    num_cans_at_discharge_index2: num_cans_at_discharge_index2,
                    num_cans_at_infeed_index1: num_cans_at_infeed_index1,
                    num_cans_at_infeed_index2:num_cans_at_infeed_index2,
                }
            }
        }
    }
    output optimize
}
