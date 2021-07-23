#!/usr/bin/env python3
# coding=utf-8

"""
MSFT Bonsai SDK3 Template for Simulator Integration using Python
Copyright 2020 Microsoft

Usage:
  For registering simulator with the Bonsai service for training:
    python simulator_integration.py   
    Then connect your registered simulator to a Brain via UI, or using the CLI: `bonsai simulator unmanaged connect -b <brain-name> -a <train-or-assess> -c  --simulator-name 
"""

import simpy
from sim.line_config import adj, adj_conv
from sim import manufacturing_env as MLS
from policies import random_policy, brain_policy, max_policy, down_policy
import datetime
import json
import os
import pathlib
import random
import sys
import time
import numpy as np
from typing import Dict, Union
from scipy.stats import truncnorm

from dotenv import load_dotenv, set_key
from microsoft_bonsai_api.simulator.client import BonsaiClient, BonsaiClientConfig
from microsoft_bonsai_api.simulator.generated.models import (
    SimulatorInterface,
    SimulatorState,
    SimulatorSessionResponse,
)
from azure.core.exceptions import HttpResponseError
from functools import partial
import threading
# from threading import Lock
# # from queue import Queue
# lock = Lock()

# import manufacturing line sim (MLS)
# import adj dict to match actions
MACHINES, CONVEYORS, _, _ = MLS.get_machines_conveyors_sources_sets(adj, adj_conv)
ENV = simpy.Environment()


DIR_PATH = os.path.dirname(os.path.realpath(__file__))
LOG_PATH = "logs"
default_config = {
    "control_type": -1,
    "control_frequency": 1,
    "interval_downtime_event_mean": 100,
    "interval_downtime_event_dev": 20,
    "downtime_event_duration_mean": 10,
    "downtime_event_duration_dev": 3,
    "number_parallel_downtime_events": 1,
    "layout_configuration": 1,
    # The following is added by Amir
    "down_machine_index": 2, 
    "initial_bin_level": 0,
    "bin_maximum_capacity": 100,
    "conveyor_capacity": 1000,
    "machine_min_speed": 5,
    "machine_max_speed": 100,
    "machine_BF_buffer": 100,
    "machine_AF_buffer": 100,
    "prox_upper_limit": 100,
    "prox_lower_limit": 5,
    "num_conveyor_bins": 10,
    "machine_initial_speed": 100,
    "infeedProx_index1": 1,
    "infeedProx_index2": 2, 
    "dischargeProx_index1": 0, 
    "dischargeProx_index2": 1
}

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
        render: bool = False,
        env_name: str = "MLSim",
        log_data: bool = False,
        log_file_name: str = None,
    ):
        """Simulator Interface with the Bonsai Platform

        Parameters
        ----------
        render : bool, optional
            Whether to visualize episodes during training, by default False
        env_name : str, optional
            Name of simulator interface, by default "Cartpole"
        log_data: bool, optional
            Whether to log data, by default False
        log_file_name : str, optional
            where to log data, by default None. If not specified, will generate a name.
        """

        self.simulator = MLS.DES(ENV)
        self._episode_count = 0

        self.count_view = False
        self.env_name = env_name
        self.render = render
        self.log_data = log_data
        if not log_file_name:
            current_time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
            log_file_name = current_time + "_" + env_name + "_log.csv"

        self.log_full_path = os.path.join(LOG_PATH, log_file_name)
        ensure_log_dir(self.log_full_path)

    def get_state(self) -> Dict[str, float]:
        """Extract current states from the simulator

        Returns
        -------
        Dict[str, float]
            Returns float of current values from the simulator
        """
        sim_states = self.simulator.get_states()
        # Add an extra field needed for go-to-point experiments

        print('Status of Conveyor Buffers')
        print('cpnveyor 0', sim_states['conveyor_buffers'][0])
        print('cpnveyor 1', sim_states['conveyor_buffers'][1])
        print('cpnveyor 2', sim_states['conveyor_buffers'][2]) 
        print('cpnveyor 3', sim_states['conveyor_buffers'][3])   
        print('cpnveyor 4', sim_states['conveyor_buffers'][4])         

        if self.render:
            pass

        return sim_states

    def halted(self) -> bool:
        """Halt current episode. Note, this should only return True if the simulator has reached an unexpected state.

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
        config : Dict, optional.
        """
        # Reset the sim, passing fields from config
        if config is None:
            config = default_config

        print('-----------------------------------resetting new episode-------------------------------')
        print(config)
        # Re-intializing the simulator to make sure all the processes are killed.
        ENV = simpy.Environment()
        self.simulator = MLS.DES(ENV)
        # overwrite some parameters with that of config:
        self.simulator.control_type = \
            config["control_type"]
        self.simulator.control_frequency = \
            config["control_frequency"]
        self.simulator.interval_downtime_event_mean = \
            config["interval_downtime_event_mean"]
        self.simulator.interval_downtime_event_dev = \
            config["interval_downtime_event_dev"]
        self.simulator.downtime_event_duration_mean = \
            config["downtime_event_duration_mean"]
        self.simulator.downtime_event_duration_dev = \
            config["downtime_event_duration_dev"]
        self.simulator.number_parallel_downtime_events = \
            config["number_parallel_downtime_events"]
        self.simulator.layout_configuration = \
            config["layout_configuration"]
        self.simulator.down_machine_index = \
            config["down_machine_index"]
        self.simulator.initial_bin_level = \
            config["initial_bin_level"]
        self.simulator.conveyor_capacity = \
            config["conveyor_capacity"]
        self.simulator.machine_min_speed = \
            config["machine_min_speed"]
        self.simulator.machine_max_speed = \
            config["machine_max_speed"]
        self.simulator.machine_BF_buffer = \
            config["machine_BF_buffer"]
        self.simulator.machine_AF_buffer = \
            config["machine_AF_buffer"]
        self.simulator.prox_upper_limit = \
            config["prox_upper_limit"]
        self.simulator.prox_lower_limit = \
            config["prox_lower_limit"]                        
        self.simulator.num_conveyor_bins = \
            config["num_conveyor_bins"]
        self.simulator.machine_initial_speed = \
            config["machine_initial_speed"]
        self.simulator.infeedProx_index1 = \
            config["infeedProx_index1"]
        self.simulator.infeedProx_index2 = \
            config["infeedProx_index2"]
        self.simulator.dischargeProx_index1 = \
            config["dischargeProx_index1"]
        self.simulator.dischargeProx_index2 = \
            config["dischargeProx_index2"]
        self.simulator.bin_maximum_capacity = \
            config["bin_maximum_capacity"]                       

        # Reset the simulator to create new processes
        self.simulator.reset()
        self.config = config

        if self.render:
            self.simulator.render()

    def log_iterations(
        self,
        state,
        action,
        episode: int = 0,
        iteration: int = 1,
    ):
        """Log iterations during training to a CSV.

        Parameters
        ----------
        state : Dict
        action : Dict
        episode : int, optional
        iteration : int, optional
        sim_speed_delay : float, optional
        """

        import pandas as pd

        def add_prefixes(d, prefix: str):
            return {f"{prefix}_{k}": v for k, v in d.items()}

        # Custom way to turn lists into strings for logging
        log_state = state.copy()
        log_action = action.copy()

        for key, value in log_state.items():
            if type(value) == list:
                log_state[key] = str(log_state[key])

        for key, value in log_action.items():
            if type(value) == list:
                log_action[key] = str(log_action[key])

        log_state = add_prefixes(log_state, "state")
        log_action = add_prefixes(log_action, "action")

        config = add_prefixes(self.config, "config")
        data = {**log_state, **log_action, **config}

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

    def episode_step(self, action: Dict):
        """Step through the environment for a single iteration.

        Parameters
        ----------
        action : Dict
            An action to take to modulate environment.
        """
        machines_speed_list = action['machines_speed']
        
        # take speed arrays and assign them into sim_action dictionary
        sim_action = {}
        index = 0
        # print(MACHINES)
        # print(CONVEYORS)
        for machine in MACHINES:
            sim_action[machine] = machines_speed_list[index]
            index += 1

        print('sim action is:\n', sim_action)
        self.simulator.step(brain_actions=sim_action)

    # hkh commented until we add rendering
    #     if self.render:
    #         self.sim_render()

    # def sim_render(self):
    #     from sim import render

    #     if self.count_view == False:
    #         self.viewer = render.Viewer()
    #         self.viewer.model = self.simulator
    #         self.count_view = True

    #     self.viewer.update()
    #     if self.viewer.has_exit:
    #         sys.exit(0)


def env_setup(env_file: str = ".env"):
    """Helper function to setup connection with Project Bonsai

    Returns
    -------
    Tuple
        workspace, and access_key
    """

    load_dotenv(verbose=True, override=True)
    workspace = os.getenv("SIM_WORKSPACE")
    access_key = os.getenv("SIM_ACCESS_KEY")

    env_file_exists = os.path.exists(env_file)
    if not env_file_exists:
        open(env_file, "a").close()

    if not all([env_file_exists, workspace]):
        workspace = input("Please enter your workspace id: ")
        set_key(env_file, "SIM_WORKSPACE", workspace)
    if not all([env_file_exists, access_key]):
        access_key = input("Please enter your access key: ")
        set_key(env_file, "SIM_ACCESS_KEY", access_key)

    load_dotenv(verbose=True, override=True)
    workspace = os.getenv("SIM_WORKSPACE")
    access_key = os.getenv("SIM_ACCESS_KEY")

    return workspace, access_key

# Manual test policy loop


def test_policy(
    render=False,
    num_episodes: int = 1,
    num_iterations: int = 10,
    log_iterations: bool = False,
    policy=max_policy,
    policy_name: str = "test_policy",
    scenario_file: str = "assess_config.json",
    exported_brain_url: str = "http://localhost:5000"
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
        sim_state = sim.episode_start(config=default_config)
        # sim_state = sim.episode_start(config=scenario_configs[episode-1])
        sim_state = sim.get_state()
        if log_iterations:
            action = policy(sim_state)
            for key, value in action.items():
                action[key] = None
            sim.log_iterations(sim_state, action, episode, iteration)
        print(f"Running iteration #{iteration} for episode #{episode}")
        iteration += 1
        while not terminal:
            action = policy(sim_state)
            sim.episode_step(action)
            sim_state = sim.get_state()
            if log_iterations:
                sim.log_iterations(sim_state, action, episode, iteration)
            print(f"Running iteration #{iteration} for episode #{episode}")
            #print(f"Observations: {sim_state}")
            iteration += 1
            terminal = iteration >= num_iterations+2 or sim.halted()

    return sim


def main(
    render: bool = False,
    log_iterations: bool = False,
    config_setup: bool = False,
    env_file: Union[str, bool] = ".env",
    workspace: str = None,
    accesskey: str = None,
):
    """Main entrypoint for running simulator connections

    Parameters
    ----------
    render : bool, optional
        visualize steps in environment, by default True, by default False
    log_iterations: bool, optional
        log iterations during training to a CSV file
    config_setup: bool, optional
        if enabled then uses a local `.env` file to find sim workspace id and access_key
    env_file: str, optional
        if config_setup True, then where the environment variable for lookup exists
    workspace: str, optional
        optional flag from CLI for workspace to override
    accesskey: str, optional
        optional flag from CLI for accesskey to override
    """

    # check if workspace or access-key passed in CLI
    use_cli_args = all([workspace, accesskey])

    # check for accesskey and workspace id in system variables
    if all(
        [
            not use_cli_args,
            "SIM_WORKSPACE" in os.environ,
            "SIM_ACCESS_KEY" in os.environ,
        ]
    ):
        workspace = os.environ["SIM_WORKSPACE"]
        accesskey = os.environ["SIM_ACCESS_KEY"]
    elif use_cli_args:
        # Use workspace and access key from CLI args passed into main
        pass
    elif config_setup or env_file:
        print(
            f"No system variables for workspace-id or access-key found, checking in env-file (.env by default)"
        )
        workspace, accesskey = env_setup(env_file)
        load_dotenv(verbose=True, override=True)
    else:
        pass

    # Grab standardized way to interact with sim API
    sim = TemplateSimulatorSession(render=render, log_data=log_iterations)

    # Configure client to interact with Bonsai service
    config_client = BonsaiClientConfig()
    client = BonsaiClient(config_client)

    # # Load json file as simulator integration config type file
    with open('interface.json') as file:
        interface = json.load(file)

    # Create simulator session and init sequence id
    registration_info = SimulatorInterface(
        name=sim.env_name,
        timeout=interface["timeout"],
        simulator_context=config_client.simulator_context,
        description=interface["description"],
    )

    def CreateSession(
        registration_info: SimulatorInterface, config_client: BonsaiClientConfig
    ):
        """Creates a new Simulator Session and returns new session, sequenceId
        """

        try:
            print(
                "config: {}, {}".format(
                    config_client.server, config_client.workspace)
            )
            registered_session: SimulatorSessionResponse = client.session.create(
                workspace_name=config_client.workspace, body=registration_info
            )
            print("Registered simulator. {}".format(
                registered_session.session_id))

            return registered_session, 1
        except HttpResponseError as ex:
            print(
                "HttpResponseError in Registering session: StatusCode: {}, Error: {}, Exception: {}".format(
                    ex.status_code, ex.error.message, ex
                )
            )
            raise ex
        except Exception as ex:
            print(
                "UnExpected error: {}, Most likely, it's some network connectivity issue, make sure you are able to reach bonsai platform from your network.".format(
                    ex
                )
            )
            raise ex

    registered_session, sequence_id = CreateSession(
        registration_info, config_client)
    episode = 0
    iteration = 0

    try:
        while True:
            # Advance by the new state depending on the event type
            # TODO: it's risky not doing doing `get_state` without first initializing the sim
            sim_state = SimulatorState(
                sequence_id=sequence_id, state=sim.get_state(), halted=sim.halted(),
            )
            try:
                event = client.session.advance(
                    workspace_name=config_client.workspace,
                    session_id=registered_session.session_id,
                    body=sim_state,
                )
                sequence_id = event.sequence_id
                print(
                    "[{}] Last Event: {}".format(
                        time.strftime("%H:%M:%S"), event.type)
                )
            except HttpResponseError as ex:
                print(
                    "HttpResponseError in Advance: StatusCode: {}, Error: {}, Exception: {}".format(
                        ex.status_code, ex.error.message, ex
                    )
                )
                # This can happen in network connectivity issue, though SDK has retry logic, but even after that request may fail,
                # if your network has some issue, or sim session at platform is going away..
                # So let's re-register sim-session and get a new session and continue iterating. :-)
                registered_session, sequence_id = CreateSession(
                    registration_info, config_client
                )
                continue
            except Exception as err:
                print("Unexpected error in Advance: {}".format(err))
                # Ideally this shouldn't happen, but for very long-running sims It can happen with various reasons, let's re-register sim & Move on.
                # If possible try to notify Bonsai team to see, if this is platform issue and can be fixed.
                registered_session, sequence_id = CreateSession(
                    registration_info, config_client
                )
                continue

            # Event loop
            if event.type == "Idle":
                time.sleep(event.idle.callback_time)
                print("Idling...")
            elif event.type == "EpisodeStart":
                print(event.episode_start.config)
                sim.episode_start(event.episode_start.config)
                episode += 1
            elif event.type == "EpisodeStep":
                sim.episode_step(event.episode_step.action)
                iteration += 1
                if sim.log_data:
                    sim.log_iterations(
                        episode=episode,
                        iteration=iteration,
                        state=sim.get_state(),
                        action=event.episode_step.action,
                    )
            elif event.type == "EpisodeFinish":
                print("Episode Finishing...")
                iteration = 0
            elif event.type == "Unregister":
                print(
                    "Simulator Session unregistered by platform because '{}', Registering again!".format(
                        event.unregister.details
                    )
                )
                registered_session, sequence_id = CreateSession(
                    registration_info, config_client
                )
                continue
            else:
                pass
    except KeyboardInterrupt:
        # Gracefully unregister with keyboard interrupt
        client.session.delete(
            workspace_name=config_client.workspace,
            session_id=registered_session.session_id,
        )
        print("Unregistered simulator.")
    # except Exception as err:
    #     # Gracefully unregister for any other exceptions
    #     client.session.delete(
    #         workspace_name=config_client.workspace,
    #         session_id=registered_session.session_id,
    #     )
    #     print("Unregistered simulator because: {}".format(err))


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        description="Bonsai and Simulator Integration...")
    parser.add_argument(
        "--render", action="store_true", default=False, help="Render training episodes",
    )
    parser.add_argument(
        "--log-iterations",
        action="store_true",
        default=False,
        help="Log iterations during training",
    )
    parser.add_argument(
        "--config-setup",
        action="store_true",
        default=False,
        help="Use a local environment file to setup access keys and workspace ids",
    )
    parser.add_argument(
        "--env-file",
        type=str,
        metavar="ENVIRONMENT FILE",
        help="path to your environment file",
        default=".env",
    )
    parser.add_argument(
        "--workspace",
        type=str,
        metavar="WORKSPACE ID",
        help="your workspace id",
        default=None,
    )
    parser.add_argument(
        "--accesskey",
        type=str,
        metavar="Your Bonsai workspace access-key",
        help="your bonsai workspace access key",
        default=None,
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--test-random", action="store_true",
    )

    group.add_argument(
        "--test-exported",
        type=int,
        const=5000,  # if arg is passed with no PORT, use this
        nargs="?",
        metavar="PORT",
        help="Run simulator with an exported brain running on localhost:PORT (default 5000)",
    )

    parser.add_argument(
        "--iteration-limit",
        type=int,
        metavar="EPISODE_ITERATIONS",
        help="Episode iteration limit when running local test.",
        default=200,
    )

    parser.add_argument(
        "--custom_assess",
        type=str,
        default=None,
        help="Custom assess config json filename",
    )

    args = parser.parse_args()

    if args.test_random:
        test_policy(
            render=args.render, log_iterations=args.log_iterations, policy=max_policy
        )
    elif args.test_exported:
        port = args.test_exported
        url = f"http://localhost:{port}"
        print(f"Connecting to exported brain running at {url}...")
        scenario_file = 'assess_config.json'
        if args.custom_assess:
            scenario_file = args.custom_assess
        trained_brain_policy = partial(brain_policy, exported_brain_url=url)
        test_policy(
            render=args.render,
            log_iterations=args.log_iterations,
            policy=trained_brain_policy,
            policy_name="exported",
            num_iterations=args.iteration_limit,
            scenario_file=scenario_file
        )
    else:
        main(
            config_setup=args.config_setup,
            render=args.render,
            log_iterations=args.log_iterations,
            env_file=args.env_file,
            workspace=args.workspace,
            accesskey=args.accesskey,
        )
