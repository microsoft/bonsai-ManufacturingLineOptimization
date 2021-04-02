inkling "2.0"
using Number
using Math


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
}


# multiarm bandit actions. 
type SimAction{
    machines_speed: number<0,10,20,30,100,>[10],
    conveyors_speed: number<0,10,20,30,100,>[9]
}


type SimConfig {
    None: number
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
    #package "PlannerTunnerDelta5"
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
                EpisodeIterationLimit: 200,
                NoProgressIterationLimit: 500000
            }
            source Simulator
            reward Reward
            

            lesson `learn 1` {
                scenario {
                    None: 2,
                }
            }
        }
    }
    output optimize 
}   
