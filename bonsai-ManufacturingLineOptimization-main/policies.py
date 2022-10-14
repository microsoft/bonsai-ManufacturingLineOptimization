"""
Fixed policies to test our sim integration with. These are intended to take
Brain states and return Brain actions.
"""

import random
from typing import Dict
import requests

machine_min_speed = [100, 30, 60, 40, 80, 80, 100, 30, 60, 40, 80, 80]
machine_max_speed = [170, 190, 180, 180, 180, 300, 170, 190, 180, 180, 180, 300]
no_machines = len(machine_min_speed)


def machine_speed_heuristic(dschrg_p1, dschrg_p2, infeed_m1, infeed_m2, machine_state, machine_index):

    if machine_state != -1 and dschrg_p1 == 0 and infeed_m1 == 0: # machine is running - neither of primary proxes are active
        if dschrg_p2  == 1 or infeed_m2 == 1: # either of secondary proxes are active
            machine_new_speed = machine_max_speed[machine_index] * 0.8 # run the machine at 80% of max speed
            return  machine_new_speed        
        elif dschrg_p2 == 0 and infeed_m2 == 0: # neither of secondary proxes are active
            machine_new_speed = machine_max_speed[machine_index] # run the machine at max speed
            return machine_new_speed
    elif machine_state == -1 : # machine is down
        return 0
    elif dschrg_p1 == 1 or infeed_m1 == 1 or machine_state == 0 or machine_state == 2:  # machine is idle or startup or either of primary proxes are active
        return 0


def heuristic_policy(state):
    action = {}
    for machine_idx in range(no_machines):
        if machine_idx == 0: # first machine
            machine_speed = machine_speed_heuristic(state['conveyor_discharge_p1_prox_full'][machine_idx], state['conveyor_discharge_p2_prox_full'][machine_idx], 0, 0, state['machines_state'][machine_idx], machine_idx)
        elif machine_idx == no_machines - 1: # last machine
            machine_speed = machine_speed_heuristic(0, 0, state['conveyor_infeed_m1_prox_empty'][machine_idx-1], state['conveyor_infeed_m2_prox_empty'][machine_idx-1], state['machines_state'][machine_idx], machine_idx)
        else: # any other machine
            machine_speed = machine_speed_heuristic(state['conveyor_discharge_p1_prox_full'][machine_idx], state['conveyor_discharge_p2_prox_full'][machine_idx],
                                        state['conveyor_infeed_m1_prox_empty'][machine_idx-1], state['conveyor_infeed_m2_prox_empty'][machine_idx-1], state['machines_state'][machine_idx], machine_idx)
        action["m" + str(machine_idx)] = machine_speed
    return action

def random_policy(state):
    """
    Ignore the state, move randomly.
    """
    action = {}
    for i in range(no_machines):
        action["m" + str(i)] = random.randint(machine_min_speed[i], machine_max_speed[i])
    return action


def max_policy(state):
    """
    Run each machine at its max speed.
    """
    action = {}
    for i in range(no_machines):
        action["m" + str(i)] = machine_max_speed[i]
    return action

def max_bottleneck_policy(state):
    """
    Run all machines at max speed of bottleneck machine.
    """
    action = {}
    bottleneck_speed = min(machine_max_speed)
    action = {}
    for i in range(no_machines):
        action["m" + str(i)] = bottleneck_speed
    return action


def brain_policy(
    state: Dict[str, float],
<<<<<<< HEAD
    exported_brain_url: str = "http://localhost:5005"
=======
    exported_brain_url: str = "http://localhost:5000"
>>>>>>> 6aa7bce (Updated sim, logs & integration)
):

    prediction_endpoint = f"{exported_brain_url}/v1/prediction"
    response = requests.get(prediction_endpoint, json=state)

    return response.json()
