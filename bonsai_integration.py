#!/usr/bin/env python3

"""
MSFT Bonsai SDK3 Template for Simulator Integration using Python
Copyright 2020 Microsoft

Usage:
  For registering simulator with the Bonsai service for training:
    python bonsai_integration.py \
           --workspace <workspace_id> \
           --accesskey="<access_key> \
    Then connect your registered simulator to a Brain via UI
    Alternatively, one can set the SIM_ACCESS_KEY and SIM_WORKSPACE as
    environment variables.
    Then connect your registered simulator to a Brain via UI, or using the CLI: `bonsai simulator unmanaged connect -b <brain-name> -a <train-or-assess> -c BalancePole --simulator-name Cartpole
"""


import json
import time
from typing import Dict, Any, Optional
from microsoft_bonsai_api.simulator.client import BonsaiClientConfig, BonsaiClient
from microsoft_bonsai_api.simulator.generated.models import (
    SimulatorState,
    SimulatorInterface,
)
import numpy as np
import argparse
from policies import random_policy, brain_policy
import logging
import datetime
import os
import pathlib
from sim import manufacturing as MLS
import simpy 


DIR_PATH = os.path.dirname(os.path.realpath(__file__))
LOG_PATH = "logs"

log = logging.getLogger(__name__)

ENV = simpy.Environment()

def ensure_log_dir(log_full_path):
    """
    Ensure the directory for logs exists — create if needed.
    """
    print(f"logfile: {log_full_path}")
    logs_directory = pathlib.Path(log_full_path).parent.absolute()
    print(f"Checking {logs_directory}")
    if not pathlib.Path(logs_directory).exists():
        print(
            "Directory does not exist at {0}, creating now...".format(
                str(logs_directory)
            )
        )
        logs_directory.mkdir(parents=True, exist_ok=True)

class TemplateSimulatorSession:
    def __init__(
        self,
        render: bool=False,
        log_data: bool=False,
        log_file_name: str=None
    ):

        self.simulator = MLS.DES(ENV)
        self.number_of_drivers = self.simulator.number_of_drivers
        
        self._episode_count = 0
        
        self.log_data = log_data
        if not log_file_name:
            current_time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
            log_file_name = current_time + "_log.csv"

        self.log_full_path = os.path.join(LOG_PATH, log_file_name)
        ensure_log_dir(self.log_full_path)
        self.render = render

    def get_state(self) -> Dict[str, float]:
        """Extract current states from the simulator

        Returns
        -------
        Dict[str, float]
            Returns float of current values from the simulator
        """
        self.simulator.get_states()

        if self.render:
            pass 

        return sim_state

    def halted(self) -> bool:
        """Halt current episode. Note, this should only be called if the simulator has reached an unexpected state.

        Returns
        -------
        bool
            Whether to terminate current episode
        """
        return False

    def episode_start(self, config: Dict = None) -> None:
        """Initialize simulator environment using scenario paramters from inkling. Note, `simulator.reset()` initializes the simulator parameters for initial positions and velocities of the cart and pole using a random sampler. See the source for details.

        Parameters
        ----------
        config : Dict, optional
            masspole and length parameters to initialize, by default None
        """



        # Re-intializing the simulator 
        self.simulator = MLS.DES(ENV)

    def episode_step(self, action: Dict):
        """Step through the environment for a single iteration.

        Parameters
        ----------
        action : Dict
            An action to take to modulate environment.
        """


        self.simulator.step(brain_actions = action)
    
    def log_iterations(self, state, action, episode: int = 0, iteration: int = 1):
        """Log iterations during training to a CSV.
        Parameters
        ----------
        state : Dict
        action : Dict
        episode : int, optional
        iteration : int, optional
        """

        import pandas as pd

        def add_prefixes(d, prefix: str):
            return {f"{prefix}_{k}": v for k, v in d.items()}

        ## Custom way to turn lists into strings for logging
        log_state = state.copy()
        log_state['n_clusters_per_bin_array_10'] = str(state['n_clusters_per_bin_array_10'])
        log_state['hist_array_10'] = str(state['hist_array_10'])

        log_state = add_prefixes(log_state, "state")

        action = add_prefixes(action, "action")
        config = add_prefixes(self.sim_config, "config")
        data = {**log_state, **action, **config}
        data["episode"] = episode
        data["iteration"] = iteration
        log_df = pd.DataFrame(data, index=[0])

        if os.path.exists(self.log_full_path):
            log_df.to_csv(
                path_or_buf=self.log_full_path, mode="a", header=False, index=False
            )
        else:
            log_df.to_csv(
                path_or_buf=self.log_full_path, mode="w", header=True, index=False
            )

# Train/Assessment loop
def main(render=False):
    # Grab standardized way to interact with sim API

    sim = TemplateSimulatorSession(render=render, )

    # Configure client to interact with Bonsai service
    config_client = BonsaiClientConfig()
    client = BonsaiClient(config_client)

    # Load json file as simulator integration config type file
    with open('interface.json') as file:
        interface = json.load(file)

    # Create simulator session and init sequence id
    registration_info = SimulatorInterface(
                            name=interface['name'], 
                            timeout=interface['timeout'], 
                            simulator_context=config_client.simulator_context,
                            description=interface['description'] 
    )

    def CreateSession(registration_info: SimulatorInterface, config_client: BonsaiClientConfig):
        """Creates a new Simulator Session and returns new session, sequenceId
        """
        try:
            print("config: {}, {}".format(config_client.server, config_client.workspace))
            registered_session: SimulatorSessionResponse = client.session.create(
                workspace_name=config_client.workspace, body=registration_info
            )
            print("Registered simulator. {}".format(registered_session.session_id))

            return registered_session, 1
        except HttpResponseError as ex:
            print("HttpResponseError in Registering session: StatusCode: {}, Error: {}, Exception: {}".format(ex.status_code, ex.error.message, ex))
            raise ex
        except Exception as ex:
            print("UnExpected error: {}, Most likely, It's some network connectivity issue, make sure, you are able to reach bonsai platform from your PC.".format(ex))
            raise ex
    
    registered_session, sequence_id = CreateSession(registration_info, config_client)

    sequence_id = 1

    try:
        while True:
            # Advance by the new state depending on the event type
            sim_state = SimulatorState(
                            sequence_id=sequence_id, state=sim.get_state(), 
                            halted=sim.halted()
            )
            try:
                event = client.session.advance(
                            workspace_name=config_client.workspace, 
                            session_id=registered_session.session_id, 
                            body=sim_state
                )
                sequence_id = event.sequence_id
                print("[{}] Last Event: {}".format(time.strftime('%H:%M:%S'), 
                                                event.type))
            except HttpResponseError as ex:
                print("HttpResponseError in Advance: StatusCode: {}, Error: {}, Exception: {}".format(ex.status_code, ex.error.message, ex))
                # This can happen in network connectivity issue, though SDK has retry logic, but even after that request may fail, 
                # if your network has some issue, or sim session at platform is going away..
                # So let's re-register sim-session and get a new session and continue iterating. :-) 
                registered_session, sequence_id = CreateSession(registration_info, config_client)
                continue
            except Exception as err:
                print("Unexpected error in Advance: {}".format(err))
                # Ideally this shouldn't happen, but for very long-running sims It can happen with various reasons, let's re-register sim & Move on.
                # If possible try to notify Bonsai team to see, if this is platform issue and can be fixed.
                registered_session, sequence_id = CreateSession(registration_info, config_client)
                continue

            # Event loop
            if event.type == 'Idle':
                time.sleep(event.idle.callback_time)
                print('Idling...')
            elif event.type == 'EpisodeStart':
                sim.episode_start(event.episode_start.config)
            elif event.type == 'EpisodeStep':
                sim.episode_step(event.episode_step.action)
            elif event.type == 'EpisodeFinish':
                print('Episode Finishing...')
            elif event.type == 'Unregister':
                print("Simulator Session unregistered by platform because '{}', Registering again!".format(event.unregister.details))
                registered_session, sequence_id = CreateSession(registration_info, config_client)
                continue
            else:
                pass
    except KeyboardInterrupt:
        # Gracefully unregister with keyboard interrupt
        client.session.delete(
            workspace_name=config_client.workspace, 
            session_id=registered_session.session_id
        )
        print("Unregistered simulator.")
    except Exception as err:
        # Gracefully unregister for any other exceptions
        client.session.delete(
            workspace_name=config_client.workspace, 
            session_id=registered_session.session_id
        )
        print("Unregistered simulator because: {}".format(err))

# Manual test policy loop
def test_policy(
    render=False,
    num_episodes: int = 2,
    num_iterations: int = 9,
    log_iterations: bool = False,
    policy=random_policy,
    policy_name: str="staff-plan",
    scenario_file: str="assess_config.json",
    exported_brain_url: str="http://localhost:5000"
):
    """Test a policy using random actions over a fixed number of episodes
    Parameters
    ----------
    num_episodes : int, optional
        number of iterations to run, by default 10
    """
    
    # Use custom assessment scenario configs
    with open(scenario_file) as fname:
        assess_info = json.load(fname)
    scenario_configs = assess_info['episodeConfigurations']
    num_episodes = len(scenario_configs)+1

    current_time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    log_file_name = current_time + "_" + policy_name + "_log.csv"
    sim = TemplateSimulatorSession(
        render=render,
        log_data=log_iterations,
        log_file_name=log_file_name
    )
    for episode in range(1, num_episodes):
        iteration = 1
        terminal = False
        sim_state = sim.episode_start(config=scenario_configs[episode-1])
        sim_state = sim.get_state()
        if log_iterations:
            action = policy(sim_state, exported_brain_url)
            for key, value in action.items():
                action[key] = None
            sim.log_iterations(sim_state, action, episode, iteration)
        print(f"Running iteration #{iteration} for episode #{episode}")
        iteration += 1
        while not terminal:
            action = policy(sim_state, exported_brain_url)
            sim.episode_step(action)
            sim_state = sim.get_state()
            if log_iterations:
                sim.log_iterations(sim_state, action, episode, iteration)
            print(f"Running iteration #{iteration} for episode #{episode}")
            #print(f"Observations: {sim_state}")
            iteration += 1
            terminal = iteration >= num_iterations+2 or sim.halted()

    return sim

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='args for sim integration',
                                     allow_abbrev=False)
    parser.add_argument('--render', action='store_true')
    parser.add_argument('--test', action='store_true')
    parser.add_argument(
        "--endpoint",
        type=str,
        default=None,
        help="End point and PORT number to test new exported brains",
    )
    parser.add_argument(
        "--custom_assess",
        type=str,
        default=None,
        help="Custom assess config json filename",
    )
    args = parser.parse_args()
    
    scenario_file = 'assess_configs/myConfig.json'
    if args.custom_assess:
        scenario_file = args.custom_assess

    endpoint = 'http://localhost:5000'
    if args.endpoint:
        endpoint = args.endpoint

    if args.test:
        test_policy(
            render=args.render, 
            log_iterations=True,
            policy=brain_policy,
            scenario_file=scenario_file,
            exported_brain_url=endpoint,
        )
    else:
        main(render=args.render)