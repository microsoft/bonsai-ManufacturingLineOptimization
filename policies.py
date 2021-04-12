"""
Fixed policies to test our sim integration with. These are intended to take
Brain states and return Brain actions.
"""

import random
from typing import Dict
import requests


def random_policy(state):
    """
    Ignore the state, move randomly.
    """
    action = {
        "machine_actions": random.randint(-1, 0, 1), 
    }
    return action

def brain_policy(
    state: Dict[str, float],
    exported_brain_url: str="http://localhost:5005"
):

    prediction_endpoint = f"{exported_brain_url}/v1/prediction"
    response = requests.get(prediction_endpoint, json=state)

    return response.json()