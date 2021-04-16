inkling "2.0"
using Number
using Math

## define constants, part of sim config 
const number_of_iterations = 1000
## control type: -1: control at fixed time frequency but no downtime event 
## control_type:  0: control at fixed time frequency 
## control type:  1: event driven, i.e. when a downtime occurs
## control type:  2: both at fixed control frequency and downtime
const control_type = -1
## the below control frequency does not apply to control type 1 and will be ignored
const control_frequency = 1 # in seconds (s)

## Downtime event config 
## a random inter_downtime_event is generated in the range [inter_downtime_event_mean - inter_downtime_event_dev, inter_downtime_event_mean + inter_downtime_event_dev]
## a random downtime duration is generated in the range [downtime_event_duration_mean - downtime_event_duration_std, downtime_event_duration_mean + downtime_event_duration_std]
const inter_downtime_event_mean = 100  # seconds (s) 
const inter_downtime_event_dev = 20 #  seconds (s) 
const downtime_event_duration_mean = 10  # seconds (s),  
const downtime_event_duration_dev = 3  # seconds (s)
## The following indicate possibility of multiple machines going down in parallel and at overlapping times
## 1 means 1 machine goes down at a time
const number_parallel_downtime_events = 1

## plant layout
## Currently only 1 configuration exists 
const layout_configuration = 1 


type SimState {
    machines_speed: number[10], 
    machines_state: number[10],
    machines_state_sum: number,
    conveyors_speed: number[9],
    sink_machines_rate_sum: number,
    conveyor_infeed_m1_prox_empty: number[9],
    conveyor_infeed_m2_prox_empty: number[9],
    conveyor_discharge_p1_prox_full: number[9],
    conveyor_discharge_p2_prox_full: number[9],
    illegal_machine_actions: number[10],
    illegal_conveyor_actions: number[9],
    remaining_downtime_machines: number[10],
    control_delta_t: number
}


type ObservationState{
    machines_speed: number[10], 
    machines_state: number[10],
    conveyors_speed: number[9],
    sink_machines_rate_sum: number,
    conveyor_infeed_m1_prox_empty: number[9],
    conveyor_infeed_m2_prox_empty: number[9],
    conveyor_discharge_p1_prox_full: number[9],
    conveyor_discharge_p2_prox_full: number[9], 
    illegal_machine_actions: number[10],
    remaining_downtime_machines: number[10] 
}


# multiarm bandit actions. 
type SimAction{
    machines_speed: number<0,10,20,30,100,>[10],
    conveyors_speed: number<0,10,20,30,100,>[9]
}


type SimConfig {
    control_type : control_type,
    control_frequency : control_frequency, 
    inter_downtime_event_mean : inter_downtime_event_mean,  
    inter_downtime_event_dev : inter_downtime_event_dev,
    downtime_event_duration_mean : downtime_event_duration_mean,   
    downtime_event_duration_dev : downtime_event_duration_dev,  
    number_parallel_downtime_events : number_parallel_downtime_events,
    layout_configuration : layout_configuration, 
}


function Reward(sim_observation: SimState){
    return sim_observation.sink_machines_rate_sum
}

# irrelevant 
function Terminal(sim_obervation: SimState){
    # terminal condition if more than two machine is down or more than 3 machines in idle mode 
    return sim_obervation.machines_state_sum <7
}

simulator Simulator(action: SimAction, config: SimConfig): SimState {
    #package ""
}

graph (input: ObservationState): SimAction {

    concept optimize(input): SimAction {
        curriculum {
            algorithm {
                Algorithm: "PPO",
                #BatchSize: 8000,
                #PolicyLearningRate: 0.001
            }
            training {
                EpisodeIterationLimit: number_of_iterations,
                NoProgressIterationLimit: 500000
            }
            source Simulator
            reward Reward
            

            lesson `learn 1` {
                scenario {
                    control_type : control_type,
                    control_frequency : control_frequency, 
                    inter_downtime_event_mean : inter_downtime_event_mean,  
                    inter_downtime_event_dev : inter_downtime_event_dev,
                    downtime_event_duration_mean : downtime_event_duration_mean,   
                    downtime_event_duration_dev : downtime_event_duration_dev,  
                    number_parallel_downtime_events : number_parallel_downtime_events,
                    layout_configuration : layout_configuration,
                }
            }
        }
    }
    output optimize 
}   
