inkling "2.0"
using Number
using Math
using Goal

const number_of_iterations = 300

## define constants, part of sim config 
const simulation_time_step = 1 # unitless

## control type: -1: control at fixed time frequency but no downtime event 
## control_type:  0: control at fixed time frequency with downtime event
## control type:  1: event driven, i.e. when a downtime occurs
## control type:  2: both at fixed control frequency and downtime event
const control_type = 0
## the below control frequency does not apply to control type 1 and will be ignored
const control_frequency = 3 # in seconds

## downtime event config
## a random interval_downtime_event is generated in the range [interval_downtime_event_mean - interval_downtime_event_dev, interval_downtime_event_mean + interval_downtime_event_dev]
const interval_first_down_event_min = 5
const interval_first_down_event_max = 100
const interval_downtime_event_mean = 20 # seconds
const interval_downtime_event_dev = 5 #  seconds

## possibility of multiple machines going down in parallel and at overlapping times
const number_parallel_downtime_events = 4
const down_machine_index = -1 # -1 for random machine down or 0 to n for the n-th machine going down

## plant layout
## currently only 1 configuration exists 
const layout_configuration = 1

const min_bin_level = 0 # initial bin minimum level
const max_bin_level = 100 # initial bin maximum level
const bin_maximum_capacity = 100 # maximum bin capacity
const num_conveyor_bins = 10 # number of bins per conveyor
const conveyor_capacity = num_conveyor_bins * bin_maximum_capacity # maximum conveyor capacity
const machine_min_speed = [100, 30, 60, 40, 80, 80, 100, 30, 60, 40, 80, 80]
const machine_max_speed = [170, 190, 180, 180, 180, 300, 170, 190, 180, 180, 180, 300]

const infeed_prox_upper_limit = 50 # threshold for infeed primary prox
const infeed_prox_lower_limit = 50 # threshold for infeed secondary prox
const discharge_prox_upper_limit = 50 # threshold for discharge primary prox
const discharge_prox_lower_limit = 50 # threshold for discharge secondary prox

const infeedProx_index1 = 1 # location of infeed primary prox
const infeedProx_index2 = 4 # location of infeed secondary prox
const dischargeProx_index1 = 0 # location of discharge primary prox
const dischargeProx_index2 = 3 # location of discharge secondary prox

## number of products at primary/secondary infeed/discharge proxes
const num_products_at_infeed_index1 = (infeedProx_index1 - 1) * bin_maximum_capacity + infeed_prox_lower_limit
const num_products_at_infeed_index2 = (infeedProx_index2 - 1) * bin_maximum_capacity + infeed_prox_upper_limit
const num_products_at_discharge_index1 = (num_conveyor_bins - dischargeProx_index1 - 1) * bin_maximum_capacity + discharge_prox_lower_limit
const num_products_at_discharge_index2 = (num_conveyor_bins - dischargeProx_index2 - 1) * bin_maximum_capacity + discharge_prox_upper_limit


type SimState {
    machines_actual_speed: number[12], # actual running speed of the machines
    machines_state: number[12], # status of the machines - down, running, idle, startup
    brain_speed: number[12], # brain choice of speed for the machines
    iteration_count: number, # iteration number
    conveyors_level: number[11], # levels of the conveyors
    mean_downtime_offset: number[12], # offset from mean downtime
    max_downtime_offset: number[12], # offset from maximum downtime
    sink_throughput_absolute_sum: number, # absolute sum of all the productions at any iteration
    conveyor_infeed_m1_prox_empty: number[11], # primary infeed status
    conveyor_infeed_m2_prox_empty: number[11], # secondary infeed status
    conveyor_discharge_p1_prox_full: number[11], # primary discharge status
    conveyor_discharge_p2_prox_full: number[11], # secondary discharge status
    control_delta_t: number,
    env_time: number,
}

type ObservationState {
    machines_state: number[12],
    machines_actual_speed: number[12],
    brain_speed: number[12],
    conveyor_infeed_m1_prox_empty: number[11],
    conveyor_infeed_m2_prox_empty: number[11],
    conveyor_discharge_p1_prox_full: number[11],
    conveyor_discharge_p2_prox_full: number[11],
}

type SimAction {
    m0: number<machine_min_speed[0] .. machine_max_speed[0] step 1>,
    m1: number<machine_min_speed[1] .. machine_max_speed[1] step 1>,
    m2: number<machine_min_speed[2] .. machine_max_speed[2] step 1>,
    m3: number<machine_min_speed[3] .. machine_max_speed[3] step 1>,
    m4: number<machine_min_speed[4] .. machine_max_speed[4] step 1>,
    m5: number<machine_min_speed[5] .. machine_max_speed[5] step 1>,
    m6: number<machine_min_speed[6] .. machine_max_speed[6] step 1>,
    m7: number<machine_min_speed[7] .. machine_max_speed[7] step 1>,
    m8: number<machine_min_speed[8] .. machine_max_speed[8] step 1>,
    m9: number<machine_min_speed[9] .. machine_max_speed[9] step 1>,
    m10: number<machine_min_speed[10] .. machine_max_speed[10] step 1>,
    m11: number<machine_min_speed[11] .. machine_max_speed[11] step 1>,
}

type SimConfig {
    simulation_time_step: simulation_time_step,
    control_type: control_type,
    control_frequency: control_frequency,
    interval_first_down_event: number,
    interval_downtime_event_mean: interval_downtime_event_mean,
    interval_downtime_event_dev: interval_downtime_event_dev,
    number_parallel_downtime_events: number,
    layout_configuration: layout_configuration,
    down_machine_index: down_machine_index,
    initial_bin_level: number,
    bin_maximum_capacity: bin_maximum_capacity,
    num_conveyor_bins: num_conveyor_bins,
    conveyor_capacity: conveyor_capacity, 
    machine0_initial_speed: number,
    machine1_initial_speed: number,
    machine2_initial_speed: number,
    machine3_initial_speed: number,
    machine4_initial_speed: number,
    machine5_initial_speed: number,
    machine6_initial_speed: number,
    machine7_initial_speed: number,
    machine8_initial_speed: number,
    machine9_initial_speed: number,
    machine10_initial_speed: number,
    machine11_initial_speed: number,
    infeed_prox_upper_limit: infeed_prox_upper_limit,
    infeed_prox_lower_limit: infeed_prox_lower_limit,
    discharge_prox_upper_limit: discharge_prox_upper_limit,
    discharge_prox_lower_limit: discharge_prox_lower_limit,
    infeedProx_index1: infeedProx_index1,
    infeedProx_index2: infeedProx_index2,
    dischargeProx_index1: dischargeProx_index1,
    dischargeProx_index2: dischargeProx_index2,
    num_products_at_discharge_index1: num_products_at_discharge_index1,
    num_products_at_discharge_index2: num_products_at_discharge_index2,
    num_products_at_infeed_index1: num_products_at_infeed_index1,
    num_products_at_infeed_index2: num_products_at_infeed_index2,
}

# number of products after machine 0
# return 0 if down or idle
function machine0_output(state: SimState) {
    var machine0_throughput_scaled = (state.machines_actual_speed[0] - machine_min_speed[0]) / (machine_max_speed[0] - machine_min_speed[0]) 
    var machine0_throughput = Math.E ** (machine0_throughput_scaled)
    if state.machines_state[0] != -1 and state.machines_actual_speed[0] == 0 {
        return -1
    }
    if state.conveyor_discharge_p2_prox_full[0] == 1 {
        var machine0_reward = machine0_throughput * 0.8
        return  machine0_reward
    }
    return machine0_throughput 
}

# number of products after machine 1
# return 0 if down or idle
function machine1_output(state: SimState) {
    var machine1_throughput_scaled = (state.machines_actual_speed[1] - machine_min_speed[1]) / (machine_max_speed[1] - machine_min_speed[1]) 
    var machine1_throughput = Math.E ** (machine1_throughput_scaled)
    if state.machines_state[1] != -1 and state.machines_actual_speed[1] == 0 {
        return -1
    }
    if state.conveyor_infeed_m2_prox_empty[0] == 1 or state.conveyor_discharge_p2_prox_full[1] == 1 {
        var machine1_reward = machine1_throughput * 0.8
        return  machine1_reward
    }
    return machine1_throughput 
}

# number of products after machine 2
# return 0 if down or idle
function machine2_output(state: SimState) {
    var machine2_throughput_scaled = (state.machines_actual_speed[2] - machine_min_speed[2]) / (machine_max_speed[2] - machine_min_speed[2]) 
    var machine2_throughput = Math.E ** (machine2_throughput_scaled)
    if state.machines_state[2] != -1 and state.machines_actual_speed[2] == 0 {
        return -1
    }
    if state.conveyor_infeed_m2_prox_empty[1] == 1 or state.conveyor_discharge_p2_prox_full[2] == 1 {
        var machine2_reward = machine2_throughput * 0.8
        return  machine2_reward
    }
    return machine2_throughput 
}

# number of products after machine 3
# return 0 if down or idle
function machine3_output(state: SimState) {
    var machine3_throughput_scaled = (state.machines_actual_speed[3] - machine_min_speed[3]) / (machine_max_speed[3] - machine_min_speed[3]) 
    var machine3_throughput = Math.E ** (machine3_throughput_scaled)
    if state.machines_state[3] != -1 and state.machines_actual_speed[3] == 0 {
        return -1
    }
    if state.conveyor_infeed_m2_prox_empty[2] == 1 or state.conveyor_discharge_p2_prox_full[3] == 1 {
        var machine3_reward = machine3_throughput * 0.8
        return  machine3_reward
    }
    return machine3_throughput 
}

# number of products after machine 4
# return 0 if down or idle
function machine4_output(state: SimState) {
    var machine4_throughput_scaled = (state.machines_actual_speed[4] - machine_min_speed[4]) / (machine_max_speed[4] - machine_min_speed[4]) 
    var machine4_throughput = Math.E ** (machine4_throughput_scaled)
    if state.machines_state[4] != -1 and state.machines_actual_speed[4] == 0 {
        return -1
    }
    if state.conveyor_infeed_m2_prox_empty[3] == 1 or state.conveyor_discharge_p2_prox_full[4] == 1 {
        var machine4_reward = machine4_throughput * 0.8
        return  machine4_reward
    }
    return machine4_throughput 
}

# number of products after machine 5
# return 0 if down or idle
function machine5_output(state: SimState) {
    var machine5_throughput_scaled = (state.machines_actual_speed[5] - machine_min_speed[5]) / (machine_max_speed[5] - machine_min_speed[5]) 
    var machine5_throughput = Math.E ** (machine5_throughput_scaled)
    if state.machines_state[5] != -1 and state.machines_actual_speed[5] == 0 {
        return -1
    }
    if state.conveyor_infeed_m2_prox_empty[4] == 1 or state.conveyor_discharge_p2_prox_full[5] == 1 {
        var machine5_reward = machine5_throughput * 0.8
        return  machine5_reward
    }
    return machine5_throughput 
}

# number of products after machine 6
# return 0 if down or idle
function machine6_output(state: SimState) {
    var machine6_throughput_scaled = (state.machines_actual_speed[6] - machine_min_speed[6]) / (machine_max_speed[6] - machine_min_speed[6]) 
    var machine6_throughput = Math.E ** (machine6_throughput_scaled)
    if state.machines_state[6] != -1 and state.machines_actual_speed[6] == 0 {
        return -1
    }
    if state.conveyor_infeed_m2_prox_empty[5] == 1 or state.conveyor_discharge_p2_prox_full[6] == 1 {
        var machine6_reward = machine6_throughput * 0.8
        return  machine6_reward
    }
    return machine6_throughput 
}

# number of products after machine 7
# return 0 if down or idle
function machine7_output(state: SimState) {
    var machine7_throughput_scaled = (state.machines_actual_speed[7] - machine_min_speed[7]) / (machine_max_speed[7] - machine_min_speed[7]) 
    var machine7_throughput = Math.E ** (machine7_throughput_scaled)
    if state.machines_state[7] != -1 and state.machines_actual_speed[7] == 0 {
        return -1
    }
    if state.conveyor_infeed_m2_prox_empty[6] == 1 or state.conveyor_discharge_p2_prox_full[7] == 1 {
        var machine7_reward = machine7_throughput * 0.8
        return  machine7_reward
    }
    return machine7_throughput 
}

# number of products after machine 8
# return 0 if down or idle
function machine8_output(state: SimState) {
    var machine8_throughput_scaled = (state.machines_actual_speed[8] - machine_min_speed[8]) / (machine_max_speed[8] - machine_min_speed[8]) 
    var machine8_throughput = Math.E ** (machine8_throughput_scaled)
    if state.machines_state[8] != -1 and state.machines_actual_speed[8] == 0 {
        return -1
    }
    if state.conveyor_infeed_m2_prox_empty[7] == 1 or state.conveyor_discharge_p2_prox_full[8] == 1 {
        var machine8_reward = machine8_throughput * 0.8
        return  machine8_reward
    }
    return machine8_throughput 
}

# number of products after machine 9
# return 0 if down or idle
function machine9_output(state: SimState) {
    var machine9_throughput_scaled = (state.machines_actual_speed[9] - machine_min_speed[9]) / (machine_max_speed[9] - machine_min_speed[9]) 
    var machine9_throughput = Math.E ** (machine9_throughput_scaled)
    if state.machines_state[9] != -1 and state.machines_actual_speed[9] == 0 {
        return -1
    }
    if state.conveyor_infeed_m2_prox_empty[8] == 1 or state.conveyor_discharge_p2_prox_full[9] == 1 {
        var machine9_reward = machine9_throughput * 0.8
        return  machine9_reward
    }
    return machine9_throughput 
}

# number of products after machine 10
# return 0 if down or idle
function machine10_output(state: SimState) {
    var machine10_throughput_scaled = (state.machines_actual_speed[10] - machine_min_speed[10]) / (machine_max_speed[10] - machine_min_speed[10]) 
    var machine10_throughput = Math.E ** (machine10_throughput_scaled)
    if state.machines_state[10] != -1 and state.machines_actual_speed[10] == 0 {
        return -1
    }
    if state.conveyor_infeed_m2_prox_empty[9] == 1 or state.conveyor_discharge_p2_prox_full[10] == 1 {
        var machine10_reward = machine10_throughput * 0.8
        return  machine10_reward
    }
    return machine10_throughput 
}

# number of products after machine 11
# return 0 if down or idle
function machine11_output(state: SimState) {
    var machine11_throughput_scaled = (state.machines_actual_speed[11] - machine_min_speed[11]) / (machine_max_speed[11] - machine_min_speed[11]) 
    var machine11_throughput = Math.E ** (machine11_throughput_scaled)
    if state.machines_state[11] != -1 and state.machines_actual_speed[11] == 0 {
        return -1
    }
    if state.conveyor_infeed_m2_prox_empty[10] == 1 {
        var machine11_reward = machine11_throughput * 0.8
        return  machine11_reward
    }
    return machine11_throughput 
}

function Reward(state: SimState) {

    var reward_machine0 = machine0_output(state)
    var reward_machine1 = machine1_output(state)
    var reward_machine2 = machine2_output(state)
    var reward_machine3 = machine3_output(state)
    var reward_machine4 = machine4_output(state)
    var reward_machine5 = machine5_output(state)
    var reward_machine6 = machine6_output(state)
    var reward_machine7 = machine7_output(state)
    var reward_machine8 = machine8_output(state)
    var reward_machine9 = machine9_output(state)
    var reward_machine10 = machine10_output(state)
    var reward_machine11 = machine11_output(state)

    var reward_total = reward_machine0 + reward_machine1 + reward_machine2 + reward_machine3 + reward_machine4 + reward_machine5 +
    reward_machine6 + reward_machine7 + reward_machine8 + reward_machine9 + reward_machine10 + reward_machine11
    return reward_total
}

function Terminal(state: SimState) {
    return false
}

simulator Simulator(action: SimAction, config: SimConfig): SimState {
}

graph (input: ObservationState): SimAction {

    concept optimize(input): SimAction {
        curriculum {
            algorithm {
                Algorithm: "SAC",
                MemoryMode: "none",
            }
            source Simulator
            reward Reward
            terminal Terminal
            training {
                EpisodeIterationLimit: number_of_iterations,
                NoProgressIterationLimit: 10000000,
            }
            lesson `learn 1` {
                scenario {
                    simulation_time_step: simulation_time_step,
                    control_type: control_type,
                    control_frequency: control_frequency,
                    interval_first_down_event: number<interval_first_down_event_min .. interval_first_down_event_max>,
                    interval_downtime_event_mean: interval_downtime_event_mean,
                    interval_downtime_event_dev: interval_downtime_event_dev,
                    number_parallel_downtime_events: number_parallel_downtime_events,
                    layout_configuration: layout_configuration,
                    down_machine_index: down_machine_index,
                    initial_bin_level: 50,
                    bin_maximum_capacity: bin_maximum_capacity,
                    num_conveyor_bins: num_conveyor_bins,
                    conveyor_capacity: conveyor_capacity,
                    machine0_initial_speed: 110,
                    machine1_initial_speed: 50,
                    machine2_initial_speed: 70,
                    machine3_initial_speed: 70,
                    machine4_initial_speed: 100,
                    machine5_initial_speed: 120,
                    machine6_initial_speed: 110,
                    machine7_initial_speed: 50,
                    machine8_initial_speed: 70,
                    machine9_initial_speed: 70,
                    machine10_initial_speed: 100,
                    machine11_initial_speed: 120,
                    infeed_prox_upper_limit: infeed_prox_upper_limit,
                    infeed_prox_lower_limit: infeed_prox_lower_limit,
                    discharge_prox_upper_limit: discharge_prox_upper_limit,
                    discharge_prox_lower_limit: discharge_prox_lower_limit,
                    infeedProx_index1: infeedProx_index1,
                    infeedProx_index2: infeedProx_index2,
                    dischargeProx_index1: dischargeProx_index1,
                    dischargeProx_index2: dischargeProx_index2,
                    num_products_at_discharge_index1: num_products_at_discharge_index1,
                    num_products_at_discharge_index2: num_products_at_discharge_index2,
                    num_products_at_infeed_index1: num_products_at_infeed_index1,
                    num_products_at_infeed_index2: num_products_at_infeed_index2,
                }
            }
        }
    }
    output optimize
}
