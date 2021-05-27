inkling "2.0"
using Number
using Math

## define constants, part of sim config 
const number_of_iterations = 1000
## the below control frequency does not apply to control type 1 and will be ignored
const control_frequency = 1 # in seconds (s)

## Downtime event config 
## a random interval_downtime_event is generated in the range [interval_downtime_event_mean - interval_downtime_event_dev, interval_downtime_event_mean + interval_downtime_event_dev]
## a random downtime duration is generated in the range [downtime_event_duration_mean - downtime_event_duration_std, downtime_event_duration_mean + downtime_event_duration_std]
const interval_downtime_event_mean = 100  # seconds (s) 
const interval_downtime_event_dev = 20 #  seconds (s) 
const downtime_event_duration_mean = 10  # seconds (s),  
const downtime_event_duration_dev = 3  # seconds (s)
## The following indicate possibility of multiple machines going down in parallel and at overlapping times
## 1 means 0 or 1 machine may go down at any point in time
## 2 means: 0, or 1 or 2 machines may go down at any point in time
## n means: 0 upto n machines may go down at any point in time.
const number_parallel_downtime_events = 1

## plant layout
## Currently only 1 configuration exists 
const layout_configuration = 1 


type SimState {
    machines_speed: number[6], 
    machines_state: number[6],
    machines_state_sum: number,
    conveyors_speed: number[5],
    sink_machines_rate_sum: number,  # rate of production in the last simulation step 
    sink_throughput_delta_sum: number,  # amount of product produced between the controls 
    sink_throughput_absolute_sum: number, # absolute sum of all the productions at eny iteration
    conveyor_infeed_m1_prox_empty: number[5],
    conveyor_infeed_m2_prox_empty: number[5],
    conveyor_discharge_p1_prox_full: number[5],
    conveyor_discharge_p2_prox_full: number[5],
    illegal_machine_actions: number[6],
    # [AJ]: Comment the following because brain is not taking action for conveyors
    #illegal_conveyor_actions: number[9],
    remaining_downtime_machines: number[6],
    control_delta_t: number,
    env_time: number,
}


type ObservationState{
    machines_speed: number[6], 
    machines_state: number[6],
    # [AJ]: Comment the following as conveyors's speed is always the same
    #conveyors_speed: number[5],
    sink_machines_rate_sum: number,
    sink_throughput_delta_sum: number,
    conveyor_infeed_m1_prox_empty: number[5],
    conveyor_infeed_m2_prox_empty: number[5],
    conveyor_discharge_p1_prox_full: number[5],
    conveyor_discharge_p2_prox_full: number[5], 
    illegal_machine_actions: number[6],
    remaining_downtime_machines: number[6] 
}


# multiarm bandit actions. 
type SimAction{
    machines_speed: number<0,10,20,30,100,>[6],
    # [AJ]: Comment the following as brain's job is not to decide on conveyors' speeds
    #conveyors_speed: number<0,10,20,30,100,>[5]
}

type MachineAction {
    machines_speed: number<0, 10, 20, 30, 100,>,
}

type SimConfig {
    ## control type: -1: control at fixed time frequency but no downtime event 
    ## control_type:  0: control at fixed time frequency 
    ## control type:  1: event driven, i.e. when a downtime occurs
    ## control type:  2: both at fixed control frequency and downtime
    control_type : number,
    control_frequency : number, 
    interval_downtime_event_mean : number,  
    interval_downtime_event_dev : number,
    downtime_event_duration_mean : number,   
    downtime_event_duration_dev : number,  
    number_parallel_downtime_events : number,
    layout_configuration : number, 
    down_machine_index: number,
}

function ExpertActionExceptMachine6(a: MachineAction): SimAction {
    return {
        machines_speed: [
            100,
            100,
            100,
            100,
            100,
            a.machines_speed,
        ]
    }
}

function ExpertActionExceptMachine5(a: MachineAction): SimAction {
    return {
        machines_speed: [
            100,
            100,
            100,
            100,
            a.machines_speed,
            100,
        ]
    }
}

function ExpertActionExceptMachine4(a: MachineAction): SimAction {
    return {
        machines_speed: [
            100,
            100,
            100,
            a.machines_speed,
            100,
            100,
        ]
    }
}

function ExpertActionExceptMachine3(a: MachineAction): SimAction {
    return {
        machines_speed: [
            100,
            100,
            a.machines_speed,
            100,
            100,
            100,
        ]
    }
}

function ExpertActionExceptMachine2(a: MachineAction): SimAction {
    return {
        machines_speed: [
            100,
            a.machines_speed,
            100,
            100,
            100,
            100,
        ]
    }
}

function ExpertActionExceptMachine1(a: MachineAction): SimAction {
    return {
        machines_speed: [
            a.machines_speed,
            100,
            100,
            100,
            100,
            100,
        ]
    }
}

function Reward(sim_observation: SimState){
    if sim_observation.control_delta_t==0 {
        return  0
    }
    else{
        return sim_observation.sink_throughput_delta_sum/(100*sim_observation.control_delta_t)
    }
}

# irrelevant 
function Terminal(sim_obervation: SimState){
    # terminal condition if more than two machine is down or more than 3 machines in idle mode 
    return sim_obervation.machines_state_sum <7
}

simulator Simulator(action: SimAction, config: SimConfig): SimState {
    #package "MfgLineSingle"
}

function aggregate(a: MachineAction, b: MachineAction, c: MachineAction, d: MachineAction, e: MachineAction, f: MachineAction): SimAction {
    return {
        machines_speed: [
            a.machines_speed,
            b.machines_speed,
            c.machines_speed,
            d.machines_speed,
            e.machines_speed,
            f.machines_speed,
        ]
    }

}

graph (input: ObservationState): SimAction {

    concept Machine1(input): MachineAction {
        curriculum {
            algorithm {
                Algorithm: "SAC",
                #BatchSize: 8000,
                #PolicyLearningRate: 0.001
            }
            training {
                EpisodeIterationLimit: number_of_iterations,
                NoProgressIterationLimit: 500000
            }
            source Simulator
            reward Reward
            action ExpertActionExceptMachine1

            lesson `No machines down` {
                scenario {
                    control_type : -1,
                    control_frequency : control_frequency, 
                    interval_downtime_event_mean : interval_downtime_event_mean,  
                    interval_downtime_event_dev : interval_downtime_event_dev,
                    downtime_event_duration_mean : downtime_event_duration_mean,   
                    downtime_event_duration_dev : downtime_event_duration_dev,  
                    number_parallel_downtime_events : number_parallel_downtime_events,
                    layout_configuration : layout_configuration,
                    down_machine_index: -1,
                }
            }
            
            lesson `Randomize 1 Machine down` {
                scenario {
                    control_type : 1,
                    control_frequency : control_frequency, 
                    interval_downtime_event_mean : interval_downtime_event_mean,  
                    interval_downtime_event_dev : interval_downtime_event_dev,
                    downtime_event_duration_mean : downtime_event_duration_mean,   
                    downtime_event_duration_dev : downtime_event_duration_dev,  
                    number_parallel_downtime_events : number_parallel_downtime_events,
                    layout_configuration : layout_configuration,
                    down_machine_index: -1,
                }
            }
        }
    }
    
     concept Machine2(input): MachineAction {
        curriculum {
            algorithm {
                Algorithm: "SAC",
                #BatchSize: 8000,
                #PolicyLearningRate: 0.001
            }
            training {
                EpisodeIterationLimit: number_of_iterations,
                NoProgressIterationLimit: 500000
            }
            source Simulator
            reward Reward
            action ExpertActionExceptMachine2
            
            lesson `No machines down` {
                scenario {
                    control_type : -1,
                    control_frequency : control_frequency, 
                    interval_downtime_event_mean : interval_downtime_event_mean,  
                    interval_downtime_event_dev : interval_downtime_event_dev,
                    downtime_event_duration_mean : downtime_event_duration_mean,   
                    downtime_event_duration_dev : downtime_event_duration_dev,  
                    number_parallel_downtime_events : number_parallel_downtime_events,
                    layout_configuration : layout_configuration,
                    down_machine_index: -1,
                }
            }
            
            lesson `Randomize 1 Machine down` {
                scenario {
                    control_type : 1,
                    control_frequency : control_frequency, 
                    interval_downtime_event_mean : interval_downtime_event_mean,  
                    interval_downtime_event_dev : interval_downtime_event_dev,
                    downtime_event_duration_mean : downtime_event_duration_mean,   
                    downtime_event_duration_dev : downtime_event_duration_dev,  
                    number_parallel_downtime_events : number_parallel_downtime_events,
                    layout_configuration : layout_configuration,
                    down_machine_index: -1,
                }
            }
        }
    }

    concept Machine3(input): MachineAction {
        curriculum {
            algorithm {
                Algorithm: "SAC",
                #BatchSize: 8000,
                #PolicyLearningRate: 0.001
            }
            training {
                EpisodeIterationLimit: number_of_iterations,
                NoProgressIterationLimit: 500000
            }
            source Simulator
            reward Reward
            action ExpertActionExceptMachine3
            
            lesson `No machines down` {
                scenario {
                    control_type : -1,
                    control_frequency : control_frequency, 
                    interval_downtime_event_mean : interval_downtime_event_mean,  
                    interval_downtime_event_dev : interval_downtime_event_dev,
                    downtime_event_duration_mean : downtime_event_duration_mean,   
                    downtime_event_duration_dev : downtime_event_duration_dev,  
                    number_parallel_downtime_events : number_parallel_downtime_events,
                    layout_configuration : layout_configuration,
                    down_machine_index: -1,
                }
            }
            
            lesson `Randomize 1 Machine down` {
                scenario {
                    control_type : 1,
                    control_frequency : control_frequency, 
                    interval_downtime_event_mean : interval_downtime_event_mean,  
                    interval_downtime_event_dev : interval_downtime_event_dev,
                    downtime_event_duration_mean : downtime_event_duration_mean,   
                    downtime_event_duration_dev : downtime_event_duration_dev,  
                    number_parallel_downtime_events : number_parallel_downtime_events,
                    layout_configuration : layout_configuration,
                    down_machine_index: -1,
                }
            }
        }
    }

    concept Machine4(input): MachineAction {
        curriculum {
            algorithm {
                Algorithm: "SAC",
                #BatchSize: 8000,
                #PolicyLearningRate: 0.001
            }
            training {
                EpisodeIterationLimit: number_of_iterations,
                NoProgressIterationLimit: 500000
            }
            source Simulator
            reward Reward
            action ExpertActionExceptMachine4
            
            lesson `No machines down` {
                scenario {
                    control_type : -1,
                    control_frequency : control_frequency, 
                    interval_downtime_event_mean : interval_downtime_event_mean,  
                    interval_downtime_event_dev : interval_downtime_event_dev,
                    downtime_event_duration_mean : downtime_event_duration_mean,   
                    downtime_event_duration_dev : downtime_event_duration_dev,  
                    number_parallel_downtime_events : number_parallel_downtime_events,
                    layout_configuration : layout_configuration,
                    down_machine_index: -1,
                }
            }
            
            lesson `Randomize 1 Machine down` {
                scenario {
                    control_type : 1,
                    control_frequency : control_frequency, 
                    interval_downtime_event_mean : interval_downtime_event_mean,  
                    interval_downtime_event_dev : interval_downtime_event_dev,
                    downtime_event_duration_mean : downtime_event_duration_mean,   
                    downtime_event_duration_dev : downtime_event_duration_dev,  
                    number_parallel_downtime_events : number_parallel_downtime_events,
                    layout_configuration : layout_configuration,
                    down_machine_index: -1,
                }
            }
        }
    }

    concept Machine5(input): MachineAction {
        curriculum {
            algorithm {
                Algorithm: "SAC",
                #BatchSize: 8000,
                #PolicyLearningRate: 0.001
            }
            training {
                EpisodeIterationLimit: number_of_iterations,
                NoProgressIterationLimit: 500000
            }
            source Simulator
            reward Reward
            action ExpertActionExceptMachine5
            
            lesson `No machines down` {
                scenario {
                    control_type : -1,
                    control_frequency : control_frequency, 
                    interval_downtime_event_mean : interval_downtime_event_mean,  
                    interval_downtime_event_dev : interval_downtime_event_dev,
                    downtime_event_duration_mean : downtime_event_duration_mean,   
                    downtime_event_duration_dev : downtime_event_duration_dev,  
                    number_parallel_downtime_events : number_parallel_downtime_events,
                    layout_configuration : layout_configuration,
                    down_machine_index: -1,
                }
            }
            
            lesson `Randomize 1 Machine down` {
                scenario {
                    control_type : 1,
                    control_frequency : control_frequency, 
                    interval_downtime_event_mean : interval_downtime_event_mean,  
                    interval_downtime_event_dev : interval_downtime_event_dev,
                    downtime_event_duration_mean : downtime_event_duration_mean,   
                    downtime_event_duration_dev : downtime_event_duration_dev,  
                    number_parallel_downtime_events : number_parallel_downtime_events,
                    layout_configuration : layout_configuration,
                    down_machine_index: -1,
                }
            }
        }
    }

    concept Machine6(input): MachineAction {
        curriculum {
            algorithm {
                Algorithm: "SAC",
                #BatchSize: 8000,
                #PolicyLearningRate: 0.001
            }
            training {
                EpisodeIterationLimit: number_of_iterations,
                NoProgressIterationLimit: 500000
            }
            source Simulator
            reward Reward
            action ExpertActionExceptMachine6

            lesson `No machines down` {
                scenario {
                    control_type : -1,
                    control_frequency : control_frequency, 
                    interval_downtime_event_mean : interval_downtime_event_mean,  
                    interval_downtime_event_dev : interval_downtime_event_dev,
                    downtime_event_duration_mean : downtime_event_duration_mean,   
                    downtime_event_duration_dev : downtime_event_duration_dev,  
                    number_parallel_downtime_events : number_parallel_downtime_events,
                    layout_configuration : layout_configuration,
                    down_machine_index: -1,
                }
            }
            
            lesson `Randomize 1 Machine down` {
                scenario {
                    control_type : 1,
                    control_frequency : control_frequency, 
                    interval_downtime_event_mean : interval_downtime_event_mean,  
                    interval_downtime_event_dev : interval_downtime_event_dev,
                    downtime_event_duration_mean : downtime_event_duration_mean,   
                    downtime_event_duration_dev : downtime_event_duration_dev,  
                    number_parallel_downtime_events : number_parallel_downtime_events,
                    layout_configuration : layout_configuration,
                    down_machine_index: -1,
                }
            }
        }
    }

    concept Aggregate(Machine1, Machine2, Machine3, Machine4, Machine5, Machine6): SimAction {
        programmed aggregate
    }

    output Aggregate
}