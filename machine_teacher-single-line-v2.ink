inkling "2.0"
using Number
using Math
using Goal

## define constants, part of sim config 
const number_of_iterations = 25
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
const interval_downtime_event_mean = 100 # seconds (s) 
const interval_downtime_event_dev = 20 #  seconds (s) 
const downtime_event_duration_mean = 15 # seconds (s),  
const downtime_event_duration_dev = 5 # seconds (s)
## The following indicate possibility of multiple machines going down in parallel and at overlapping times
## 1 means 0 or 1 machine may go down at any point in time
## 2 means: 0, or 1 or 2 machines may go down at any point in time
## n means: 0 upto n machines may go down at any point in time.
const number_parallel_downtime_events = 1

## plant layout
## Currently only 1 configuration exists 
const layout_configuration = 1

const down_machine_index = 3 # It can be from -1 for random machine down or 0 to 5 for specific down machine
const initial_bin_level = 40
const bin_maximum_capacity = 100
const num_conveyor_bins = 10
const conveyor_capacity = num_conveyor_bins * bin_maximum_capacity
const machine_min_speed = 1
const machine_max_speed = 100
const machine_initial_speed = 100

const infeed_prox_upper_limit = 10
const infeed_prox_lower_limit = 10
const discharge_prox_upper_limit = 10
const discharge_prox_lower_limit = 10

const infeedProx_index1 = 1
const infeedProx_index2 = 3
const dischargeProx_index1 = 0
const dischargeProx_index2 = 2

const num_cans_at_discharge_index1 = (num_conveyor_bins - dischargeProx_index1 - 1) * bin_maximum_capacity + discharge_prox_lower_limit
const num_cans_at_discharge_index2 = (num_conveyor_bins - dischargeProx_index2 - 1) * bin_maximum_capacity + discharge_prox_upper_limit

const num_cans_at_infeed_index1 = (infeedProx_index1 - 1) * bin_maximum_capacity + infeed_prox_lower_limit
const num_cans_at_infeed_index2 = (infeedProx_index2 - 1) * bin_maximum_capacity + infeed_prox_upper_limit

const num_machines = 6
const lambda_num_cans = 0
const iteration_penalty = 0
const lambda_ss_speed = 0.5
const lambda_ss_buffer = 0.5

type SimState {
    machines_actual_speed: number[6], 
    machines_state: number[6],
    brain_speed: number[6],
    machines_state_sum: number,
    iteration_count: number,
    down_duration: number,
    all_conveyor_levels_estimate: number[5],
    mean_downtime_offset: number[6],
    max_downtime_offset: number[6],
    sink_throughput_absolute_sum: number, # absolute sum of all the productions at eny iteration
    conveyor_infeed_m1_prox_empty: number[5],
    conveyor_infeed_m2_prox_empty: number[5],
    conveyor_discharge_p1_prox_full: number[5],
    conveyor_discharge_p2_prox_full: number[5],
    control_delta_t: number,
    env_time: number,
}

type ObservationState {
    machines_actual_speed: number[6],
    brain_speed: number[6],
    conveyor_infeed_m1_prox_empty: number[5],
    conveyor_infeed_m2_prox_empty: number[5],
    conveyor_discharge_p1_prox_full: number[5],
    conveyor_discharge_p2_prox_full: number[5],
}

# multiarm bandit actions. 
type SimAction {
    machines_speed: number<machine_min_speed .. machine_max_speed step 1>[6],
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
    initial_bin_level: initial_bin_level,
    bin_maximum_capacity: bin_maximum_capacity,
    num_conveyor_bins: num_conveyor_bins,
    conveyor_capacity: conveyor_capacity,
    machine_min_speed: machine_min_speed,
    machine_max_speed: machine_max_speed,
    machine_initial_speed: machine_initial_speed,
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

function Reward(sim_observation: SimState) {
    var num_cans_norm:number = 0  # Number of cans per sec
    if sim_observation.control_delta_t == 0 {
        num_cans_norm = 0
    } else {
        num_cans_norm =  sim_observation.machines_actual_speed[5] / (machine_max_speed)
    }

    var ss_buffer_reached_infeed: number = 1 - (sim_observation.conveyor_infeed_m2_prox_empty[0] + sim_observation.conveyor_infeed_m2_prox_empty[1]+ sim_observation.conveyor_infeed_m2_prox_empty[2] + sim_observation.conveyor_infeed_m2_prox_empty[3] + sim_observation.conveyor_infeed_m2_prox_empty[4] )/ (num_machines - 1)
    var ss_buffer_reached_dischrg: number = 1 - (sim_observation.conveyor_discharge_p2_prox_full[0] + sim_observation.conveyor_discharge_p2_prox_full[1]+ sim_observation.conveyor_discharge_p2_prox_full[2] + sim_observation.conveyor_discharge_p2_prox_full[3] + sim_observation.conveyor_discharge_p2_prox_full[4] )/ (num_machines - 1)
    var ss_buffer_reached: number = (ss_buffer_reached_infeed + ss_buffer_reached_dischrg)/2

    var ss_speed_reached = (sim_observation.machines_actual_speed[0] + sim_observation.machines_actual_speed[1] + sim_observation.machines_actual_speed[2] + sim_observation.machines_actual_speed[3] + sim_observation.machines_actual_speed[4] + sim_observation.machines_actual_speed[5])/ (num_machines*machine_max_speed)
    # var ss_reached = (ss_buffer_reached + ss_speed_reached)/2

    return lambda_num_cans*num_cans_norm + lambda_ss_speed*ss_speed_reached + lambda_ss_buffer*ss_buffer_reached - iteration_penalty

}

# irrelevant 
function Terminal(sim_obervation: SimState) {    
        
    # terminal condition if more than two machine is down or more than 3 machines in idle mode 
    return (sim_obervation.conveyor_infeed_m1_prox_empty[0] == 1) or 
        (sim_obervation.conveyor_infeed_m1_prox_empty[1] == 1) or 
        (sim_obervation.conveyor_infeed_m1_prox_empty[2] == 1) or
        (sim_obervation.conveyor_infeed_m1_prox_empty[3] == 1) or
        (sim_obervation.conveyor_infeed_m1_prox_empty[4] == 1) or        
        (sim_obervation.conveyor_discharge_p1_prox_full[0] == 1) or
        (sim_obervation.conveyor_discharge_p1_prox_full[1] == 1) or
        (sim_obervation.conveyor_discharge_p1_prox_full[2] == 1) or
        (sim_obervation.conveyor_discharge_p1_prox_full[3] == 1) or
        (sim_obervation.conveyor_discharge_p1_prox_full[4] == 1)
        
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
            terminal Terminal
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
                    initial_bin_level: initial_bin_level,
                    bin_maximum_capacity: bin_maximum_capacity,
                    num_conveyor_bins: num_conveyor_bins,
                    conveyor_capacity: conveyor_capacity,
                    machine_min_speed: machine_min_speed,
                    machine_max_speed: machine_max_speed,
                    machine_initial_speed: machine_initial_speed,
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
