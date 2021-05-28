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
    machines_speed: number[10], 
    machines_state: number[10],
    machines_state_sum: number,
    conveyors_speed: number[9],
    sink_machines_rate_sum: number,  # rate of production in the last simulation step 
    sink_throughput_delta_sum: number,  # amount of product produced between the controls 
    sink_throughput_absolute_sum: number, # absolute sum of all the productions at eny iteration
    conveyor_infeed_m1_prox_empty: number[9],
    conveyor_infeed_m2_prox_empty: number[9],
    conveyor_discharge_p1_prox_full: number[9],
    conveyor_discharge_p2_prox_full: number[9],
    illegal_machine_actions: number[10],
    # [AJ]: Comment the following because brain is not taking action for conveyors
    #illegal_conveyor_actions: number[9],
    remaining_downtime_machines: number[10],
    control_delta_t: number,
    env_time: number,
}


type ObservationState{
    machines_speed: number[10], 
    machines_state: number[10],
    # [AJ]: Comment the following as conveyors's speed is always the same
    #conveyors_speed: number[9],
    sink_machines_rate_sum: number,
    sink_throughput_delta_sum: number,
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
    # [AJ]: Comment the following as brain's job is not to decide on conveyors' speeds
    #conveyors_speed: number<0,10,20,30,100,>[5]
}

type MachineActionMinusOne {
    machines_speed: number<0, 10, 20, 30, 100>[9],
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
    # 0 to 9 for machine index, -1 for no downtime/random number parallel downtime
    down_machine_index: number,
}

function TransformAction10Down(a: MachineActionMinusOne): SimAction {
    return {
        machines_speed: [
            a.machines_speed[0],
            a.machines_speed[1],
            a.machines_speed[2],
            a.machines_speed[3],
            a.machines_speed[4],
            a.machines_speed[5],
            a.machines_speed[6],
            a.machines_speed[7],
            a.machines_speed[8],
            0
        ]
    }
}

function TransformAction9Down(a: MachineActionMinusOne): SimAction {
    return {
        machines_speed: [
            a.machines_speed[0],
            a.machines_speed[1],
            a.machines_speed[2],
            a.machines_speed[3],
            a.machines_speed[4],
            a.machines_speed[5],
            a.machines_speed[6],
            a.machines_speed[7],
            0,
            a.machines_speed[8]
        ]
    }
}

function TransformAction8Down(a: MachineActionMinusOne): SimAction {
    return {
        machines_speed: [
            a.machines_speed[0],
            a.machines_speed[1],
            a.machines_speed[2],
            a.machines_speed[3],
            a.machines_speed[4],
            a.machines_speed[5],
            a.machines_speed[6],
            0,
            a.machines_speed[7],
            a.machines_speed[8]
        ]
    }
}

function TransformAction7Down(a: MachineActionMinusOne): SimAction {
    return {
        machines_speed: [
            a.machines_speed[0],
            a.machines_speed[1],
            a.machines_speed[2],
            a.machines_speed[3],
            a.machines_speed[4],
            a.machines_speed[5],
            0,
            a.machines_speed[6],
            a.machines_speed[7],
            a.machines_speed[8]
        ]
    }
}

function TransformAction6Down(a: MachineActionMinusOne): SimAction {
    return {
        machines_speed: [
            a.machines_speed[0],
            a.machines_speed[1],
            a.machines_speed[2],
            a.machines_speed[3],
            a.machines_speed[4],
            0,
            a.machines_speed[5],
            a.machines_speed[6],
            a.machines_speed[7],
            a.machines_speed[8]
        ]
    }
}

function TransformAction5Down(a: MachineActionMinusOne): SimAction {
    return {
        machines_speed: [
            a.machines_speed[0],
            a.machines_speed[1],
            a.machines_speed[2],
            a.machines_speed[3],
            0,
            a.machines_speed[4],
            a.machines_speed[5],
            a.machines_speed[6],
            a.machines_speed[7],
            a.machines_speed[8]
        ]
    }
}

function TransformAction4Down(a: MachineActionMinusOne): SimAction {
    return {
        machines_speed: [
            a.machines_speed[0],
            a.machines_speed[1],
            a.machines_speed[2],
            0,
            a.machines_speed[3],
            a.machines_speed[4],
            a.machines_speed[5],
            a.machines_speed[6],
            a.machines_speed[7],
            a.machines_speed[8]
        ]
    }
}

function TransformAction3Down(a: MachineActionMinusOne): SimAction {
    return {
        machines_speed: [
            a.machines_speed[0],
            a.machines_speed[1],
            0,
            a.machines_speed[2],
            a.machines_speed[3],
            a.machines_speed[4],
            a.machines_speed[5],
            a.machines_speed[6],
            a.machines_speed[7],
            a.machines_speed[8]
        ]
    }
}

function TransformAction2Down(a: MachineActionMinusOne): SimAction {
    return {
        machines_speed: [
            a.machines_speed[0],
            0,
            a.machines_speed[1],
            a.machines_speed[2],
            a.machines_speed[3],
            a.machines_speed[4],
            a.machines_speed[5],
            a.machines_speed[6],
            a.machines_speed[7],
            a.machines_speed[8]
        ]
    }
}

function TransformAction1Down(a: MachineActionMinusOne): SimAction {
    return {
        machines_speed: [
            0,
            a.machines_speed[0],
            a.machines_speed[1],
            a.machines_speed[2],
            a.machines_speed[3],
            a.machines_speed[4],
            a.machines_speed[5],
            a.machines_speed[6],
            a.machines_speed[7],
            a.machines_speed[8]
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
    #package "MFGlinedouble"
}

function pad(s: ObservationState, a: SimAction, b: MachineActionMinusOne): SimAction {
    
    if s.machines_state[9] == -1 {
        return {
            machines_speed: [
                b.machines_speed[0],
                b.machines_speed[1],
                b.machines_speed[2],
                b.machines_speed[3],
                b.machines_speed[4],
                a.machines_speed[5],
                a.machines_speed[6],
                a.machines_speed[7],
                a.machines_speed[8],
                0,
            ],
        }
    }
    
    else if s.machines_state[8] == -1 {
        return {
            machines_speed: [
                b.machines_speed[0],
                b.machines_speed[1],
                b.machines_speed[2],
                b.machines_speed[3],
                b.machines_speed[4],
                b.machines_speed[5],
                b.machines_speed[6],
                b.machines_speed[7],
                0,
                b.machines_speed[8],

            ],
        }
    }
    
    else if s.machines_state[7] == -1 {
        return {
            machines_speed: [
                b.machines_speed[0],
                b.machines_speed[1],
                b.machines_speed[2],
                b.machines_speed[3],
                b.machines_speed[4],
                b.machines_speed[5],
                b.machines_speed[6],
                0,
                b.machines_speed[7],
                b.machines_speed[8],
            ],
        }
    }
    
    else if s.machines_state[6] == -1 {
        return {
            machines_speed: [
                b.machines_speed[0],
                b.machines_speed[1],
                b.machines_speed[2],
                b.machines_speed[3],
                b.machines_speed[4],
                b.machines_speed[5],
                0,
                b.machines_speed[6],
                b.machines_speed[7],
                b.machines_speed[8],
            ],
        }
    }
    
    else if s.machines_state[5] == -1 {
        return {
            machines_speed: [
                b.machines_speed[0],
                b.machines_speed[1],
                b.machines_speed[2],
                b.machines_speed[3],
                b.machines_speed[4],
                0,
                b.machines_speed[5],
                b.machines_speed[6],
                b.machines_speed[7],
                b.machines_speed[8],
            ],
        }
    }

    
    else if s.machines_state[4] == -1 {
        return {
            machines_speed: [
                b.machines_speed[0],
                b.machines_speed[1],
                b.machines_speed[2],
                b.machines_speed[3],
                0,
                b.machines_speed[4],
                b.machines_speed[5],
                b.machines_speed[6],
                b.machines_speed[7],
                b.machines_speed[8],
            ],
        }
    }

    else if s.machines_state[3] == -1 {
        return {
            machines_speed: [
                b.machines_speed[0],
                b.machines_speed[1],
                b.machines_speed[2],
                0,
                b.machines_speed[3],
                b.machines_speed[4],
                b.machines_speed[5],
                b.machines_speed[6],
                b.machines_speed[7],
                b.machines_speed[8],
            ],
        }
    }

    else if s.machines_state[2] == -1 {
        return {
            machines_speed: [
                b.machines_speed[0],
                b.machines_speed[1],
                0,
                b.machines_speed[2],
                b.machines_speed[3],
                b.machines_speed[4],
                b.machines_speed[5],
                b.machines_speed[6],
                b.machines_speed[7],
                b.machines_speed[8],
            ],
        }
    }

    else if s.machines_state[1] == -1 {
        return {
            machines_speed: [
                b.machines_speed[0],
                0,
                b.machines_speed[1],
                b.machines_speed[2],
                b.machines_speed[3],
                b.machines_speed[4],
                b.machines_speed[5],
                b.machines_speed[6],
                b.machines_speed[7],
                b.machines_speed[8],
            ],
        }
    }

    else if s.machines_state[0] == -1 {
        return {
            machines_speed: [
                0,
                b.machines_speed[0],
                b.machines_speed[1],
                b.machines_speed[2],
                b.machines_speed[3],
                b.machines_speed[4],
                b.machines_speed[5],
                b.machines_speed[6],
                b.machines_speed[7],
                b.machines_speed[8],
            ],
        }
    }

    else {
        return {
            machines_speed: [
                a.machines_speed[0],
                a.machines_speed[1],
                a.machines_speed[2],
                a.machines_speed[3],
                a.machines_speed[4],
                a.machines_speed[5],
                a.machines_speed[6],
                a.machines_speed[7],
                a.machines_speed[8],
                a.machines_speed[9],
                
            ],
        }        
    }

}

graph (input: ObservationState): SimAction {

    concept AllMachines(input): SimAction {
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
            

            lesson `No Machines Down` {
                scenario {
                    control_type : -1, # must change to -1
                    control_frequency : control_frequency, 
                    interval_downtime_event_mean : interval_downtime_event_mean,  
                    interval_downtime_event_dev : interval_downtime_event_dev,
                    downtime_event_duration_mean : downtime_event_duration_mean,   
                    downtime_event_duration_dev : downtime_event_duration_dev,  
                    number_parallel_downtime_events : number_parallel_downtime_events,
                    layout_configuration : layout_configuration,
                    down_machine_index: -1 # allows parallel downtime events
                }
            }
        }
    }

    concept Machine10Down(input): MachineActionMinusOne {
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
            action TransformAction10Down

            lesson `Take Machine 10 Out` {
                scenario {
                    control_type : 1, # control type allows downtime
                    control_frequency : control_frequency, 
                    interval_downtime_event_mean : interval_downtime_event_mean,  
                    interval_downtime_event_dev : interval_downtime_event_dev,
                    downtime_event_duration_mean : downtime_event_duration_mean,   
                    downtime_event_duration_dev : downtime_event_duration_dev,  
                    number_parallel_downtime_events : number_parallel_downtime_events,
                    layout_configuration : layout_configuration,
                    down_machine_index: 9, # zero index machine
                }
            }
        }
    }
    
    concept Machine9Down(input): MachineActionMinusOne {
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
            action TransformAction9Down

            lesson `Take Machine 9 Out` {
                scenario {
                    control_type : 1,
                    control_frequency : control_frequency, 
                    interval_downtime_event_mean : interval_downtime_event_mean,  
                    interval_downtime_event_dev : interval_downtime_event_dev,
                    downtime_event_duration_mean : downtime_event_duration_mean,   
                    downtime_event_duration_dev : downtime_event_duration_dev,  
                    number_parallel_downtime_events : number_parallel_downtime_events,
                    layout_configuration : layout_configuration,
                    down_machine_index: 8,
                }
            }
        }
    }
    
    concept Machine8Down(input): MachineActionMinusOne {
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
            action TransformAction8Down

            lesson `Take Machine 8 Out` {
                scenario {
                    control_type : 1,
                    control_frequency : control_frequency, 
                    interval_downtime_event_mean : interval_downtime_event_mean,  
                    interval_downtime_event_dev : interval_downtime_event_dev,
                    downtime_event_duration_mean : downtime_event_duration_mean,   
                    downtime_event_duration_dev : downtime_event_duration_dev,  
                    number_parallel_downtime_events : number_parallel_downtime_events,
                    layout_configuration : layout_configuration,
                    down_machine_index: 7,
                }
            }
        }
    }
    
    concept Machine7Down(input): MachineActionMinusOne {
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
            action TransformAction7Down

            lesson `Take Machine 7 Out` {
                scenario {
                    control_type : 1,
                    control_frequency : control_frequency, 
                    interval_downtime_event_mean : interval_downtime_event_mean,  
                    interval_downtime_event_dev : interval_downtime_event_dev,
                    downtime_event_duration_mean : downtime_event_duration_mean,   
                    downtime_event_duration_dev : downtime_event_duration_dev,  
                    number_parallel_downtime_events : number_parallel_downtime_events,
                    layout_configuration : layout_configuration,
                    down_machine_index: 6,
                }
            }
        }
    }
    
    concept Machine6Down(input): MachineActionMinusOne {
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
            action TransformAction6Down

            lesson `Take Machine 6 Out` {
                scenario {
                    control_type : 1,
                    control_frequency : control_frequency, 
                    interval_downtime_event_mean : interval_downtime_event_mean,  
                    interval_downtime_event_dev : interval_downtime_event_dev,
                    downtime_event_duration_mean : downtime_event_duration_mean,   
                    downtime_event_duration_dev : downtime_event_duration_dev,  
                    number_parallel_downtime_events : number_parallel_downtime_events,
                    layout_configuration : layout_configuration,
                    down_machine_index: 5,
                }
            }
        }
    }
    
    concept Machine5Down(input): MachineActionMinusOne {
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
            action TransformAction5Down

            lesson `Take Machine 5 Out` {
                scenario {
                    control_type : 1,
                    control_frequency : control_frequency, 
                    interval_downtime_event_mean : interval_downtime_event_mean,  
                    interval_downtime_event_dev : interval_downtime_event_dev,
                    downtime_event_duration_mean : downtime_event_duration_mean,   
                    downtime_event_duration_dev : downtime_event_duration_dev,  
                    number_parallel_downtime_events : number_parallel_downtime_events,
                    layout_configuration : layout_configuration,
                    down_machine_index: 4,
                }
            }
        }
    }

    concept Machine4Down(input): MachineActionMinusOne {
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
            action TransformAction4Down

            lesson `Take Machine 4 Out` {
                scenario {
                    control_type : 1,
                    control_frequency : control_frequency, 
                    interval_downtime_event_mean : interval_downtime_event_mean,  
                    interval_downtime_event_dev : interval_downtime_event_dev,
                    downtime_event_duration_mean : downtime_event_duration_mean,   
                    downtime_event_duration_dev : downtime_event_duration_dev,  
                    number_parallel_downtime_events : number_parallel_downtime_events,
                    layout_configuration : layout_configuration,
                    down_machine_index: 3,
                }
            }
        }
    }
    
    concept Machine3Down(input): MachineActionMinusOne {
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
            action TransformAction3Down

            lesson `Take Machine 3 Out` {
                scenario {
                    control_type : 1,
                    control_frequency : control_frequency, 
                    interval_downtime_event_mean : interval_downtime_event_mean,  
                    interval_downtime_event_dev : interval_downtime_event_dev,
                    downtime_event_duration_mean : downtime_event_duration_mean,   
                    downtime_event_duration_dev : downtime_event_duration_dev,  
                    number_parallel_downtime_events : number_parallel_downtime_events,
                    layout_configuration : layout_configuration,
                    down_machine_index: 2,
                }
            }
        }
    }

    concept Machine2Down(input): MachineActionMinusOne {
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
            action TransformAction2Down

            lesson `Take Machine 2 Out` {
                scenario {
                    control_type : 1,
                    control_frequency : control_frequency, 
                    interval_downtime_event_mean : interval_downtime_event_mean,  
                    interval_downtime_event_dev : interval_downtime_event_dev,
                    downtime_event_duration_mean : downtime_event_duration_mean,   
                    downtime_event_duration_dev : downtime_event_duration_dev,  
                    number_parallel_downtime_events : number_parallel_downtime_events,
                    layout_configuration : layout_configuration,
                    down_machine_index: 1,
                }
            }
        }
    }

    concept Machine1Down(input): MachineActionMinusOne {
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
            action TransformAction1Down

            lesson `Take Machine 1 Out` {
                scenario {
                    control_type : 1,
                    control_frequency : control_frequency, 
                    interval_downtime_event_mean : interval_downtime_event_mean,  
                    interval_downtime_event_dev : interval_downtime_event_dev,
                    downtime_event_duration_mean : downtime_event_duration_mean,   
                    downtime_event_duration_dev : downtime_event_duration_dev,  
                    number_parallel_downtime_events : number_parallel_downtime_events,
                    layout_configuration : layout_configuration,
                    down_machine_index: 0,
                }
            }
        }
    }

    concept Padding(input, AllMachines, Machine10Down, Machine9Down, Machine8Down, Machine7Down, Machine6Down, Machine5Down, Machine4Down, Machine3Down, Machine2Down, Machine1Down): SimAction {
        programmed pad
    }

    output Padding
}