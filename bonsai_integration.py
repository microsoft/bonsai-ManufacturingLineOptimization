#!/usr/bin/env python3

"""
MSFT Bonsai SDK3 Template for Simulator Integration using Python
Copyright 2020 Microsoft

Usage:
  For registering simulator with the Bonsai service for training:
    python simulator_integration.py   
    Then connect your registered simulator to a Brain via UI, or using the CLI: `bonsai simulator unmanaged connect -b <brain-name> -a <train-or-assess> -c BalancePole --simulator-name Cartpole
"""

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

from policies import random_policy, brain_policy
# import manufacturing line sim (MLS)
from sim import manufacturing_env as MLS
# import adj dict to match actions 
from sim.line_config import adj
import simpy 
MACHINES, CONVEYORS, _, _ = MLS.get_machines_conveyors_sources_sets(adj)

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
LOG_PATH = "logs"
default_config = {
    "control_type": 1,
    "control_frequency": 1, 
    "inter_downtime_event_mean": 100,  
    "inter_downtime_event_dev": 20,
    "downtime_event_duration_mean": 10,   
    "downtime_event_duration_dev": 3,  
    "number_parallel_downtime_events": 1,
    "layout_configuration": 1,
}

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
        render: bool = False,
        env_name: str = "Cartpole",
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
        print(sim_states)

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
        config : Dict, optional. The following keys are supported:
            - cart_mass   # (kg)
            - pole_mass   # (kg)
            - pole_length  # (m)
            - initial_cart_position  # (m)
            - initial_cart_velocity  # (m/s)
            - initial_pole_angle  # (rad)
            - initial_angular_velocity  # (rad/s)
            - target_pole_position  # (m)
        """
        ## Reset the sim, passing fields from config
        if config is None:
            config = default_config

        ## Re-intializing the simulator to make sure all the processes are killed. 
        self.simulator = MLS.DES(ENV)
        ## overwrite some parameters with that of config:
        self.simulator.control_type = \
             config["control_type"]
        self.simulator.control_frequency = \
             config["control_frequency"]
        self.simulator.inter_downtime_event_mean = \
             config["inter_downtime_event_mean"]  
        self.simulator.inter_downtime_event_dev = \
             config["inter_downtime_event_dev"]
        self.simulator.downtime_event_duration_mean = \
             config["downtime_event_duration_mean"]   
        self.simulator.downtime_event_duration_dev = \
             config["downtime_event_duration_dev"]  
        self.simulator.number_parallel_downtime_events = \
             config["number_parallel_downtime_events"]
        self.simulator.layout_configuration = \
             config["layout_configuration"]
        
        # Reset the simulator to create new processes 
        self.simulator.reset()

    def log_iterations(
        self,
        state,
        action,
        episode: int = 0,
        iteration: int = 1,
        sim_speed_delay: float = 0.0,
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

        state = add_prefixes(state, "state")
        action = add_prefixes(action, "action")
        config = add_prefixes(self.config, "config")
        data = {**state, **action, **config}
        data["episode"] = episode
        data["iteration"] = iteration
        data["sim_speed_delay"] = sim_speed_delay
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
        print('brain action arrays is :\n', action)
        machines_speed_list = action['machines_speed']
        conveyors_speed_list = action['conveyors_speed']

        # take speed arrays and assign them into sim_action dictionary
        sim_action = {}
        index = 0 
        print(MACHINES)
        print(CONVEYORS)
        for machine in MACHINES:
            sim_action[machine] = machines_speed_list[index]
            index += 1 
        
        index = 0 
        for conveyor in CONVEYORS:
            sim_action[conveyor] = conveyors_speed_list[index]
            index += 1 
        print('sim action is:\n', sim_action)
        self.simulator.step(brain_actions = sim_action)

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


def test_policy(
    num_episodes: int = 10,
    render: bool = True,
    num_iterations: int = 200,
    log_iterations: bool = False,
    policy=random_policy,
    policy_name: str = "random",
):
    """Test a policy using random actions over a fixed number of episodes

    Parameters
    ----------
    num_episodes : int, optional
        number of iterations to run, by default 10
    """

    current_time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    log_file_name = current_time + "_" + policy_name + "_log.csv"
    sim = TemplateSimulatorSession(
        render=render, log_data=log_iterations, log_file_name=log_file_name
    )
    # test_config = {"length": 1.5}
    for episode in range(num_episodes):
        iteration = 0
        terminal = False
        # When testing, initialize throughout the range.
        config = {"initial_cart_position": random.uniform(-0.9, 0.9)}
        sim_state = sim.episode_start(config=config)
        sim_state = sim.get_state()
        while not terminal:
            action = policy(sim_state)
            sim.episode_step(action)
            sim_state = sim.get_state()
            if log_iterations:
                sim.log_iterations(sim_state, action, episode, iteration)
            print(f"Running iteration #{iteration} for episode #{episode}")
            print(f"Observations: {sim_state}")
            iteration += 1
            terminal = iteration >= num_iterations

    return sim


def main(
    render: bool = False,
    log_iterations: bool = False,
    config_setup: bool = False,
    sim_speed: int = 0,
    sim_speed_variance: int = 0,
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
    sim_speed: int, optional
        the average delay to use, default = 0
    sim_speed_variance: int, optional
        the variance for sim delay
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
                "config: {}, {}".format(config_client.server, config_client.workspace)
            )
            registered_session: SimulatorSessionResponse = client.session.create(
                workspace_name=config_client.workspace, body=registration_info
            )
            print("Registered simulator. {}".format(registered_session.session_id))

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

    registered_session, sequence_id = CreateSession(registration_info, config_client)
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
                    "[{}] Last Event: {}".format(time.strftime("%H:%M:%S"), event.type)
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
                iteration += 1
                delay = 0.0
                if sim_speed > 0:
                    if (
                        sim_speed_variance > 0
                    ):  # stochastic delay, truncated normal distribution
                        mu = sim_speed
                        sigma = sim_speed_variance
                        lower = np.max(
                            [0, sim_speed - 3 * sim_speed_variance]
                        )  # truncating at min +/- 3*variance
                        upper = sim_speed + 3 * sim_speed_variance
                        delay = truncnorm.rvs(
                            (lower - mu) / sigma,
                            (upper - mu) / sigma,
                            loc=mu,
                            scale=sigma,
                        )
                        print("stochastic sim delay: {}s".format(delay))
                        time.sleep(delay)
                    else:  # fixed delay
                        delay = sim_speed
                        print("sim delay: {}s".format(delay))
                        time.sleep(delay)
                sim.episode_step(event.episode_step.action)
                if sim.log_data:
                    sim.log_iterations(
                        episode=episode,
                        iteration=iteration,
                        state=sim.get_state(),
                        action=event.episode_step.action,
                        sim_speed_delay=delay,
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

    parser = argparse.ArgumentParser(description="Bonsai and Simulator Integration...")
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
        "--sim-speed",
        type=int,
        metavar="SIM_SPEED",
        help="additional emulated sim speed wait in seconds, default: adds 0s",
        default=0,
    )

    parser.add_argument(
        "--sim-speed-variance",
        type=int,
        metavar="SIM_SPEED_VARIANCE",
        help="emulates stochastic sim speed, adds uniform variance to --sim-speed",
        default=0,
    )

    args = parser.parse_args()

    if args.test_random:
        test_policy(
            render=args.render, log_iterations=args.log_iterations, policy=random_policy
        )
    elif args.test_exported:
        port = args.test_exported
        url = f"http://localhost:{port}"
        print(f"Connecting to exported brain running at {url}...")
        trained_brain_policy = partial(brain_policy, exported_brain_url=url)
        test_policy(
            render=args.render,
            log_iterations=args.log_iterations,
            policy=trained_brain_policy,
            policy_name="exported",
            num_iterations=args.iteration_limit,
        )
    else:
        main(
            config_setup=args.config_setup,
            render=args.render,
            log_iterations=args.log_iterations,
            sim_speed=args.sim_speed,
            sim_speed_variance=args.sim_speed_variance,
            env_file=args.env_file,
            workspace=args.workspace,
            accesskey=args.accesskey,
        )

