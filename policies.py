"""
Fixed policies to test our sim integration with. These are intended to take
Brain states and return Brain actions.
"""

import random
from typing import Dict
import requests


def machine_speed_heuristic(dschrg_p1, dschrg_p2, infeed_m1, infeed_m2, machine_state):

    machine_max_speed = 100
    if dschrg_p1 == 0 and infeed_m1 == 0: # machine is running
        if dschrg_p2  == 1 or infeed_m2 == 1:
            machine_new_speed = machine_max_speed / 2
            return  machine_new_speed        
        else : # if p2 or m2 are 0
            return machine_max_speed        
    elif machine_state == -1 : # machine is down
        return 0
    else:  # machine is idle
        return machine_max_speed


def heuristic_policy(state):
    action = {"machines_speed": []}
    for machine_idx in range(6):
        if machine_idx == 0: # first machine
            machine_speed = machine_speed_heuristic(state['conveyor_discharge_p1_prox_full'][machine_idx], state['conveyor_discharge_p2_prox_full'][machine_idx], 0, 0, state['machines_state'][machine_idx])

        elif machine_idx == 5: # last machine
            machine_speed = machine_speed_heuristic(0, 0,
                                state['conveyor_infeed_m1_prox_empty'][machine_idx-1], state['conveyor_infeed_m2_prox_empty'][machine_idx-1], state['machines_state'][machine_idx])

        else:
            machine_speed = machine_speed_heuristic(state['conveyor_discharge_p1_prox_full'][machine_idx], state['conveyor_discharge_p2_prox_full'][machine_idx],
                                        state['conveyor_infeed_m1_prox_empty'][machine_idx-1], state['conveyor_infeed_m2_prox_empty'][machine_idx-1], state['machines_state'][machine_idx])

        action["machines_speed"].append(machine_speed)
    return action

def random_policy(state):
    """
    Ignore the state, move randomly.
    """
    action = {}
    machine_min_speed = [100, 30, 60, 40, 80, 80]
    machine_max_speed = [170, 190, 180, 180, 180, 300]
    for i in range(6):
        action["m" + str(i)] = random.randint(machine_min_speed[i], machine_max_speed[i])
    return action


def max_policy_various(state):
    """
    Pick the max speed for each machine.
    """
    action = {
        'm0': 170,
        'm1': 190,
        'm2': 180,
        'm3': 180,
        'm4': 180,
        'm5': 300
    }
    return action

def max_bottleneck_policy(state):
    """
    Run all machines at max speed of bottleneck machine.
    """
    action = {
        'm0': 170,
        'm1': 170,
        'm2': 170,
        'm3': 170,
        'm4': 170,
        'm5': 170
    }
    return action

def down_policy(state):
    """
    Ignore the state, move randomly.
    """

    action = {
        'm0': 80,
        'm1': 80,
        'm2': 40,
        'm3': 80,
        'm4': 80,
        'm5': 80
    }
    return action


def brain_policy(
    state: Dict[str, float],
    exported_brain_url: str = "http://localhost:5005"
):

    prediction_endpoint = f"{exported_brain_url}/v1/prediction"
    response = requests.get(prediction_endpoint, json=state)

    return response.json()
