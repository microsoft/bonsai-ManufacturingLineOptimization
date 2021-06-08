inkling "2.0"
using Number
using Math

## define constants, part of sim config 
const number_of_iterations = 480
## the below control frequency does not apply to control type 1 and will be ignored
const control_frequency = 3 # in seconds (s)

## Downtime event config 
## a random interval_downtime_event is generated in the range [interval_downtime_event_mean - interval_downtime_event_dev, interval_downtime_event_mean + interval_downtime_event_dev]
## a random downtime duration is generated in the range [downtime_event_duration_mean - downtime_event_duration_std, downtime_event_duration_mean + downtime_event_duration_std]
const interval_downtime_event_mean = 60  # seconds (s) 
const interval_downtime_event_dev = 15 #  seconds (s) 
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


type ObservationState {
    machines_speed: number[10], 
    machines_state: number[10],
    # [AJ]: Comment the following as conveyors's speed is always the same
    #conveyors_speed: number[5],
    sink_machines_rate_sum: number,
    sink_throughput_delta_sum: number,
    conveyor_infeed_m1_prox_empty: number[9],
    conveyor_infeed_m2_prox_empty: number[9],
    conveyor_discharge_p1_prox_full: number[9],
    conveyor_discharge_p2_prox_full: number[9], 
    illegal_machine_actions: number[10],
    remaining_downtime_machines: number[10] 
}

type MachineState {
    machines_speed: number[3], 
    machines_state: number[3],
    # [AJ]: Comment the following as conveyors's speed is always the same
    #conveyors_speed: number[1],
    sink_machines_rate_sum: number,
    sink_throughput_delta_sum: number,
    conveyor_infeed_m1_prox_empty: number[2],
    conveyor_infeed_m2_prox_empty: number[2],
    conveyor_discharge_p1_prox_full: number[2],
    conveyor_discharge_p2_prox_full: number[2], 
    illegal_machine_actions: number[3],
    remaining_downtime_machines: number[3] 
}

type MachineStateConnect {
    machines_speed: number[4], 
    machines_state: number[4],
    # [AJ]: Comment the following as conveyors's speed is always the same
    #conveyors_speed: number[1],
    sink_machines_rate_sum: number,
    sink_throughput_delta_sum: number,
    conveyor_infeed_m1_prox_empty: number[3],
    conveyor_infeed_m2_prox_empty: number[3],
    conveyor_discharge_p1_prox_full: number[3],
    conveyor_discharge_p2_prox_full: number[3], 
    illegal_machine_actions: number[4],
    remaining_downtime_machines: number[4] 
}

type MachineStateSourceSink {
    machines_speed: number[2], 
    machines_state: number[2],
    # [AJ]: Comment the following as conveyors's speed is always the same
    #conveyors_speed: number[1],
    sink_machines_rate_sum: number,
    sink_throughput_delta_sum: number,
    conveyor_infeed_m1_prox_empty: number[1],
    conveyor_infeed_m2_prox_empty: number[1],
    conveyor_discharge_p1_prox_full: number[1],
    conveyor_discharge_p2_prox_full: number[1], 
    illegal_machine_actions: number[2],
    remaining_downtime_machines: number[2] 
}


# multiarm bandit actions. 
type SimAction {
    machines_speed: number<0,10,20,30,100,>[10],
    # [AJ]: Comment the following as brain's job is not to decide on conveyors' speeds
    #conveyors_speed: number<0,10,20,30,100,>[9]
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
    buffer_size_IC: number[9]
}

function ExpertActionExceptMachine9(a: MachineAction): SimAction {
    return {
        machines_speed: [
            100,
            100,
            100,
            100,
            100,
            100,
            100,
            100,
            100,
            a.machines_speed,
        ]
    }
}

function ExpertActionExceptMachine8(a: MachineAction): SimAction {
    return {
        machines_speed: [
            100,
            100,
            100,
            100,
            100,
            100,
            100,
            100,
            a.machines_speed,
            100,
        ]
    }
}

function ExpertActionExceptMachine7(a: MachineAction): SimAction {
    return {
        machines_speed: [
            100,
            100,
            100,
            100,
            100,
            100,
            100,
            a.machines_speed,
            100,
            100,
        ]
    }
}

function ExpertActionExceptMachine6(a: MachineAction): SimAction {
    return {
        machines_speed: [
            100,
            100,
            100,
            100,
            100,
            100,
            a.machines_speed,
            100,
            100,
            100,
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
            100,
            a.machines_speed,
            100,
            100,
            100,
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
            100,
            a.machines_speed,
            100,
            100,
            100,
            100,
            100
        ]
    }
}

function ExpertActionExceptMachine3(a: MachineAction): SimAction {
    return {
        machines_speed: [
            100,
            100,
            100,
            a.machines_speed,
            100,
            100,
            100,
            100,
            100,
            100
        ]
    }
}

function ExpertActionExceptMachine2(a: MachineAction): SimAction {
    return {
        machines_speed: [
            100,
            100,
            a.machines_speed,
            100,
            100,
            100,
            100,
            100,
            100,
            100
        ]
    }
}

function ExpertActionExceptMachine1(a: MachineAction): SimAction {
    return {
        machines_speed: [
            100,
            a.machines_speed,
            100,
            100,
            100,
            100,
            100,
            100,
            100,
            100
        ]
    }
}

function ExpertActionExceptMachine0(a: MachineAction): SimAction {
    return {
        machines_speed: [
            a.machines_speed,
            100,
            100,
            100,
            100,
            100,
            100,
            100,
            100,
            100
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

function decompose0(s: ObservationState): MachineStateSourceSink {
    return {
        machines_speed: [
            s.machines_speed[0],
            s.machines_speed[1]
        ], 
        machines_state: [
            s.machines_state[0],
            s.machines_state[1]
        ],
        sink_machines_rate_sum: s.sink_machines_rate_sum,
        sink_throughput_delta_sum: s.sink_throughput_delta_sum,
        conveyor_infeed_m1_prox_empty: [
            s.conveyor_infeed_m1_prox_empty[0],
        ],
        conveyor_infeed_m2_prox_empty: [
            s.conveyor_infeed_m2_prox_empty[0], 
        ],
        conveyor_discharge_p1_prox_full: [
            s.conveyor_discharge_p1_prox_full[0], 
        ],
        conveyor_discharge_p2_prox_full: [
            s.conveyor_discharge_p2_prox_full[0],
        ], 
        illegal_machine_actions: [
            s.illegal_machine_actions[0],
            s.illegal_machine_actions[1]
        ],
        remaining_downtime_machines: [
            s.illegal_machine_actions[0],
            s.illegal_machine_actions[1]
        ]
    }

}

function decompose1(s: ObservationState): MachineStateConnect {
    return {
        machines_speed: [
            s.machines_speed[0],
            s.machines_speed[1],
            s.machines_speed[2],
            s.machines_speed[7],
        ], 
        machines_state: [
            s.machines_state[0],
            s.machines_state[1],
            s.machines_state[2],
            s.machines_state[7]
        ],
        sink_machines_rate_sum: s.sink_machines_rate_sum,
        sink_throughput_delta_sum: s.sink_throughput_delta_sum,
        conveyor_infeed_m1_prox_empty: [
            s.conveyor_infeed_m1_prox_empty[0],
            s.conveyor_infeed_m1_prox_empty[1],
            s.conveyor_infeed_m1_prox_empty[6]
        ],
        conveyor_infeed_m2_prox_empty: [
            s.conveyor_infeed_m2_prox_empty[0], 
            s.conveyor_infeed_m1_prox_empty[1],
            s.conveyor_infeed_m1_prox_empty[6]
        ],
        conveyor_discharge_p1_prox_full: [
            s.conveyor_discharge_p1_prox_full[0], 
            s.conveyor_discharge_p1_prox_full[1],
            s.conveyor_discharge_p1_prox_full[6]
        ],
        conveyor_discharge_p2_prox_full: [
            s.conveyor_discharge_p2_prox_full[0],
            s.conveyor_discharge_p2_prox_full[1],
            s.conveyor_discharge_p2_prox_full[6]
        ], 
        illegal_machine_actions: [
            s.illegal_machine_actions[0],
            s.illegal_machine_actions[1],
            s.illegal_machine_actions[2],
            s.illegal_machine_actions[7]
        ],
        remaining_downtime_machines: [
            s.illegal_machine_actions[0],
            s.illegal_machine_actions[1],
            s.illegal_machine_actions[0],
            s.illegal_machine_actions[7]
        ]
    }

}

function decompose2(s: ObservationState): MachineState {
    return {
        machines_speed: [
            s.machines_speed[1],
            s.machines_speed[2],
            s.machines_speed[3]
        ], 
        machines_state: [
            s.machines_state[1],
            s.machines_state[2],
            s.machines_state[3]
        ],
        sink_machines_rate_sum: s.sink_machines_rate_sum,
        sink_throughput_delta_sum: s.sink_throughput_delta_sum,
        conveyor_infeed_m1_prox_empty: [
            s.conveyor_infeed_m1_prox_empty[1],
            s.conveyor_infeed_m1_prox_empty[2]
        ],
        conveyor_infeed_m2_prox_empty: [
            s.conveyor_infeed_m2_prox_empty[1], 
            s.conveyor_infeed_m1_prox_empty[2]
        ],
        conveyor_discharge_p1_prox_full: [
            s.conveyor_discharge_p1_prox_full[1], 
            s.conveyor_discharge_p1_prox_full[2]
        ],
        conveyor_discharge_p2_prox_full: [
            s.conveyor_discharge_p2_prox_full[1],
            s.conveyor_discharge_p2_prox_full[2]
        ], 
        illegal_machine_actions: [
            s.illegal_machine_actions[1],
            s.illegal_machine_actions[2],
            s.illegal_machine_actions[3]
        ],
        remaining_downtime_machines: [
            s.illegal_machine_actions[1],
            s.illegal_machine_actions[2],
            s.illegal_machine_actions[3]
        ]
    }

}

function decompose3(s: ObservationState): MachineState {
    return {
        machines_speed: [
            s.machines_speed[2],
            s.machines_speed[3],
            s.machines_speed[4]
        ], 
        machines_state: [
            s.machines_state[2],
            s.machines_state[3],
            s.machines_state[4]
        ],
        sink_machines_rate_sum: s.sink_machines_rate_sum,
        sink_throughput_delta_sum: s.sink_throughput_delta_sum,
        conveyor_infeed_m1_prox_empty: [
            s.conveyor_infeed_m1_prox_empty[2],
            s.conveyor_infeed_m1_prox_empty[3]
        ],
        conveyor_infeed_m2_prox_empty: [
            s.conveyor_infeed_m2_prox_empty[2], 
            s.conveyor_infeed_m1_prox_empty[3]
        ],
        conveyor_discharge_p1_prox_full: [
            s.conveyor_discharge_p1_prox_full[2], 
            s.conveyor_discharge_p1_prox_full[3]
        ],
        conveyor_discharge_p2_prox_full: [
            s.conveyor_discharge_p2_prox_full[2],
            s.conveyor_discharge_p2_prox_full[3]
        ], 
        illegal_machine_actions: [
            s.illegal_machine_actions[2],
            s.illegal_machine_actions[3],
            s.illegal_machine_actions[4]
        ],
        remaining_downtime_machines: [
            s.illegal_machine_actions[2],
            s.illegal_machine_actions[3],
            s.illegal_machine_actions[4]
        ]
    }

}

function decompose4(s: ObservationState): MachineState {
    return {
        machines_speed: [
            s.machines_speed[3],
            s.machines_speed[4],
            s.machines_speed[5]
        ], 
        machines_state: [
            s.machines_state[3],
            s.machines_state[4],
            s.machines_state[5]
        ],
        sink_machines_rate_sum: s.sink_machines_rate_sum,
        sink_throughput_delta_sum: s.sink_throughput_delta_sum,
        conveyor_infeed_m1_prox_empty: [
            s.conveyor_infeed_m1_prox_empty[3],
            s.conveyor_infeed_m1_prox_empty[4]
        ],
        conveyor_infeed_m2_prox_empty: [
            s.conveyor_infeed_m2_prox_empty[3], 
            s.conveyor_infeed_m1_prox_empty[4]
        ],
        conveyor_discharge_p1_prox_full: [
            s.conveyor_discharge_p1_prox_full[3], 
            s.conveyor_discharge_p1_prox_full[4]
        ],
        conveyor_discharge_p2_prox_full: [
            s.conveyor_discharge_p2_prox_full[3],
            s.conveyor_discharge_p2_prox_full[4]
        ], 
        illegal_machine_actions: [
            s.illegal_machine_actions[3],
            s.illegal_machine_actions[4],
            s.illegal_machine_actions[5]
        ],
        remaining_downtime_machines: [
            s.illegal_machine_actions[3],
            s.illegal_machine_actions[4],
            s.illegal_machine_actions[5]
        ]
    }

}

function decompose5(s: ObservationState): MachineStateSourceSink {
    return {
        machines_speed: [
            s.machines_speed[4],
            s.machines_speed[5]
        ], 
        machines_state: [
            s.machines_state[4],
            s.machines_state[5]
        ],
        sink_machines_rate_sum: s.sink_machines_rate_sum,
        sink_throughput_delta_sum: s.sink_throughput_delta_sum,
        conveyor_infeed_m1_prox_empty: [
            s.conveyor_infeed_m1_prox_empty[4],
        ],
        conveyor_infeed_m2_prox_empty: [
            s.conveyor_infeed_m2_prox_empty[4], 
        ],
        conveyor_discharge_p1_prox_full: [
            s.conveyor_discharge_p1_prox_full[4], 
        ],
        conveyor_discharge_p2_prox_full: [
            s.conveyor_discharge_p2_prox_full[4],
        ], 
        illegal_machine_actions: [
            s.illegal_machine_actions[4],
            s.illegal_machine_actions[5]
        ],
        remaining_downtime_machines: [
            s.illegal_machine_actions[4],
            s.illegal_machine_actions[5]
        ]
    }

}

function decompose6(s: ObservationState): MachineStateSourceSink {
    return {
        machines_speed: [
            s.machines_speed[6],
            s.machines_speed[7]
        ], 
        machines_state: [
            s.machines_state[6],
            s.machines_state[7]
        ],
        sink_machines_rate_sum: s.sink_machines_rate_sum,
        sink_throughput_delta_sum: s.sink_throughput_delta_sum,
        conveyor_infeed_m1_prox_empty: [
            s.conveyor_infeed_m1_prox_empty[5],
        ],
        conveyor_infeed_m2_prox_empty: [
            s.conveyor_infeed_m2_prox_empty[5], 
        ],
        conveyor_discharge_p1_prox_full: [
            s.conveyor_discharge_p1_prox_full[5], 
        ],
        conveyor_discharge_p2_prox_full: [
            s.conveyor_discharge_p2_prox_full[5],
        ], 
        illegal_machine_actions: [
            s.illegal_machine_actions[6],
            s.illegal_machine_actions[7]
        ],
        remaining_downtime_machines: [
            s.illegal_machine_actions[6],
            s.illegal_machine_actions[7]
        ]
    }

}

function decompose7(s: ObservationState): MachineStateConnect {
    return {
        machines_speed: [
            s.machines_speed[6],
            s.machines_speed[7],
            s.machines_speed[8],
            s.machines_speed[1],
        ], 
        machines_state: [
            s.machines_state[6],
            s.machines_state[7],
            s.machines_state[8],
            s.machines_state[1],
        ],
        sink_machines_rate_sum: s.sink_machines_rate_sum,
        sink_throughput_delta_sum: s.sink_throughput_delta_sum,
        conveyor_infeed_m1_prox_empty: [
            s.conveyor_infeed_m1_prox_empty[5],
            s.conveyor_infeed_m1_prox_empty[6],
            s.conveyor_infeed_m1_prox_empty[1]
        ],
        conveyor_infeed_m2_prox_empty: [
            s.conveyor_infeed_m2_prox_empty[5], 
            s.conveyor_infeed_m1_prox_empty[6],
            s.conveyor_infeed_m1_prox_empty[1]
        ],
        conveyor_discharge_p1_prox_full: [
            s.conveyor_discharge_p1_prox_full[5], 
            s.conveyor_discharge_p1_prox_full[6],
            s.conveyor_discharge_p1_prox_full[1]
        ],
        conveyor_discharge_p2_prox_full: [
            s.conveyor_discharge_p2_prox_full[5],
            s.conveyor_discharge_p2_prox_full[6],
            s.conveyor_discharge_p2_prox_full[1]
        ], 
        illegal_machine_actions: [
            s.illegal_machine_actions[6],
            s.illegal_machine_actions[7],
            s.illegal_machine_actions[8],
            s.illegal_machine_actions[1],
        ],
        remaining_downtime_machines: [
            s.illegal_machine_actions[6],
            s.illegal_machine_actions[7],
            s.illegal_machine_actions[8],
            s.illegal_machine_actions[1]
        ]
    }
}

function decompose8(s: ObservationState): MachineState {
    return {
        machines_speed: [
            s.machines_speed[7],
            s.machines_speed[8],
            s.machines_speed[9]
        ], 
        machines_state: [
            s.machines_state[7],
            s.machines_state[8],
            s.machines_state[9]
        ],
        sink_machines_rate_sum: s.sink_machines_rate_sum,
        sink_throughput_delta_sum: s.sink_throughput_delta_sum,
        conveyor_infeed_m1_prox_empty: [
            s.conveyor_infeed_m1_prox_empty[6],
            s.conveyor_infeed_m1_prox_empty[7]
        ],
        conveyor_infeed_m2_prox_empty: [
            s.conveyor_infeed_m2_prox_empty[6], 
            s.conveyor_infeed_m1_prox_empty[7]
        ],
        conveyor_discharge_p1_prox_full: [
            s.conveyor_discharge_p1_prox_full[6], 
            s.conveyor_discharge_p1_prox_full[7]
        ],
        conveyor_discharge_p2_prox_full: [
            s.conveyor_discharge_p2_prox_full[6],
            s.conveyor_discharge_p2_prox_full[7]
        ], 
        illegal_machine_actions: [
            s.illegal_machine_actions[7],
            s.illegal_machine_actions[8],
            s.illegal_machine_actions[9]
        ],
        remaining_downtime_machines: [
            s.illegal_machine_actions[7],
            s.illegal_machine_actions[8],
            s.illegal_machine_actions[9]
        ]
    }

}

function decompose9(s: ObservationState): MachineStateConnect {
    return {
        machines_speed: [
            s.machines_speed[8],
            s.machines_speed[9],
            s.machines_speed[4],
            s.machines_speed[3]
        ], 
        machines_state: [
            s.machines_state[8],
            s.machines_state[9],
            s.machines_state[4],
            s.machines_state[3],
        ],
        sink_machines_rate_sum: s.sink_machines_rate_sum,
        sink_throughput_delta_sum: s.sink_throughput_delta_sum,
        conveyor_infeed_m1_prox_empty: [
            s.conveyor_infeed_m1_prox_empty[7],
            s.conveyor_infeed_m1_prox_empty[8],
            s.conveyor_infeed_m1_prox_empty[3]
        ],
        conveyor_infeed_m2_prox_empty: [
            s.conveyor_infeed_m2_prox_empty[7], 
            s.conveyor_infeed_m1_prox_empty[8],
            s.conveyor_infeed_m1_prox_empty[3],
        ],
        conveyor_discharge_p1_prox_full: [
            s.conveyor_discharge_p1_prox_full[7], 
            s.conveyor_discharge_p1_prox_full[8],
            s.conveyor_discharge_p1_prox_full[3]
        ],
        conveyor_discharge_p2_prox_full: [
            s.conveyor_discharge_p2_prox_full[7],
            s.conveyor_discharge_p2_prox_full[8],
            s.conveyor_discharge_p2_prox_full[3],
        ], 
        illegal_machine_actions: [
            s.illegal_machine_actions[8],
            s.illegal_machine_actions[9],
            s.illegal_machine_actions[4],
            s.illegal_machine_actions[3],
        ],
        remaining_downtime_machines: [
            s.illegal_machine_actions[8],
            s.illegal_machine_actions[9],
            s.illegal_machine_actions[4],
            s.illegal_machine_actions[3],
        ]
    }

}

function aggregate(a: MachineAction, b: MachineAction, c: MachineAction, d: MachineAction, e: MachineAction, f: MachineAction, g: MachineAction, h: MachineAction, i: MachineAction, j: MachineAction): SimAction {
    return {
        machines_speed: [
            a.machines_speed,
            b.machines_speed,
            c.machines_speed,
            d.machines_speed,
            e.machines_speed,
            f.machines_speed,
            g.machines_speed,
            h.machines_speed,
            i.machines_speed,
            j.machines_speed
        ]
    }
}

simulator Simulator(action: SimAction, config: SimConfig): SimState {
    package "MFGLineDoubleWork"
}

graph (input: ObservationState): SimAction {

    concept Decompose0(input): MachineStateSourceSink {
        programmed decompose0
    }

    concept Decompose1(input): MachineStateConnect {
        programmed decompose1
    }

    concept Decompose2(input): MachineState {
        programmed decompose2
    }

    concept Decompose3(input): MachineState {
        programmed decompose3
    }

    concept Decompose4(input): MachineState {
        programmed decompose4
    }

    concept Decompose5(input): MachineStateSourceSink {
        programmed decompose5
    }

    concept Decompose6(input): MachineStateSourceSink {
        programmed decompose6
    }

    concept Decompose7(input): MachineStateConnect {
        programmed decompose7
    }

    concept Decompose8(input): MachineState {
        programmed decompose8
    }

    concept Decompose9(input): MachineStateConnect {
        programmed decompose9
    }

    concept Machine0(Decompose0): MachineAction {
        curriculum {
            algorithm {
                Algorithm: "SAC",
                #BatchSize: 8000,
                #PolicyLearningRate: 0.001
            }
            training {
                EpisodeIterationLimit: number_of_iterations,
                NoProgressIterationLimit: 20000000
            }
            source Simulator
            reward Reward
            action ExpertActionExceptMachine0

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

                training {
                    LessonRewardThreshold: 478
                }
            }
            
            lesson `Randomize 1 Machine down` {
                scenario {
                    control_type : 0,
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
    
     concept Machine1(Decompose1): MachineAction {
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
                    control_type : 0,
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

    concept Machine2(Decompose2): MachineAction {
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
                    control_type : 0,
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

    concept Machine3(Decompose3): MachineAction {
        curriculum {
            algorithm {
                Algorithm: "SAC",
                #BatchSize: 8000,
                #PolicyLearningRate: 0.001
            }
            training {
                EpisodeIterationLimit: number_of_iterations,
                NoProgressIterationLimit: 20000000
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
                    control_type : 0,
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

    concept Machine4(Decompose4): MachineAction {
        curriculum {
            algorithm {
                Algorithm: "SAC",
                #BatchSize: 8000,
                #PolicyLearningRate: 0.001
            }
            training {
                EpisodeIterationLimit: number_of_iterations,
                NoProgressIterationLimit: 20000000
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
                    control_type : 0,
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

    concept Machine5(Decompose5): MachineAction {
        curriculum {
            algorithm {
                Algorithm: "SAC",
                #BatchSize: 8000,
                #PolicyLearningRate: 0.001
            }
            training {
                EpisodeIterationLimit: number_of_iterations,
                NoProgressIterationLimit: 20000000
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
                    control_type : 0,
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

    concept Machine6(Decompose6): MachineAction {
        curriculum {
            algorithm {
                Algorithm: "SAC",
                #BatchSize: 8000,
                #PolicyLearningRate: 0.001
            }
            training {
                EpisodeIterationLimit: number_of_iterations,
                NoProgressIterationLimit: 20000000
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
                    control_type : 0,
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

    concept Machine7(Decompose7): MachineAction {
        curriculum {
            algorithm {
                Algorithm: "SAC",
                #BatchSize: 8000,
                #PolicyLearningRate: 0.001
            }
            training {
                EpisodeIterationLimit: number_of_iterations,
                NoProgressIterationLimit: 20000000
            }
            source Simulator
            reward Reward
            action ExpertActionExceptMachine7

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
                    control_type : 0,
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

    concept Machine8(Decompose8): MachineAction {
        curriculum {
            algorithm {
                Algorithm: "SAC",
                #BatchSize: 8000,
                #PolicyLearningRate: 0.001
            }
            training {
                EpisodeIterationLimit: number_of_iterations,
                NoProgressIterationLimit: 20000000
            }
            source Simulator
            reward Reward
            action ExpertActionExceptMachine8

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
                    control_type : 0,
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

    concept Machine9(Decompose9): MachineAction {
        curriculum {
            algorithm {
                Algorithm: "SAC",
                #BatchSize: 8000,
                #PolicyLearningRate: 0.001
            }
            training {
                EpisodeIterationLimit: number_of_iterations,
                NoProgressIterationLimit: 20000000
            }
            source Simulator
            reward Reward
            action ExpertActionExceptMachine9

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
                    control_type : 0,
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

    concept Aggregate(Machine0, Machine1, Machine2, Machine3, Machine4, Machine5, Machine6, Machine7, Machine8, Machine9): SimAction {
        programmed aggregate
    }

    output Aggregate
}