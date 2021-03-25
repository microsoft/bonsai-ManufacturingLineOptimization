import os
import time 
import json
import time
import json
from typing import Dict, Any, Optional
from microsoft_bonsai_api.simulator.client import BonsaiClientConfig, BonsaiClient
from microsoft_bonsai_api.simulator.generated.models import (
    SimulatorState,
    SimulatorInterface,
)
import numpy as np
from dotenv import load_dotenv, set_key

config_client = BonsaiClientConfig()

# Load json file as simulator integration config type file
with open('interface.json') as file:
    interface = json.load(file)

with open('workspace.json') as file:
    args = json.load(file)


config_client.workspace = args['workspace']
config_client.access_key = args['access_key']
client = BonsaiClient(config_client)


# Create simulator session and init sequence id
registration_info = SimulatorInterface(
                        name=interface['name'], 
                        timeout=interface['timeout'], 
                        simulator_context=config_client.simulator_context, 
)
registered_session = client.session.create(
                        workspace_name=config_client.workspace, 
                        body=registration_info
)

print("Registered simulator.")
sequence_id = 1



while True:
    # Advance by the new state depending on the event type
    states = {'n_machine': np.random.randint(1,5), 'event_type': np.random.randint(5,10)}

    try:
        sim_state = SimulatorState(
                            sequence_id=sequence_id, state=states,
                            halted=False
            )
        event = client.session.advance(
                        workspace_name=config_client.workspace, 
                        session_id=registered_session.session_id, 
                        body=sim_state
            )
        sequence_id = event.sequence_id
        print("[{}] Last Event: {}".format(time.strftime('%H:%M:%S'), 
                                                event.type))
                                                

        # Event loop
        if event.type == 'Idle':
            time.sleep(event.idle.callback_time)
            print('Idling...')
        elif event.type == 'EpisodeStart':
            print('episode reseting...')
            #event.episode_start(event.episode_start.config)
            #sim.episode_start(event.episode_start.config)
        elif event.type == 'EpisodeStep':
            print(event.episode_step.action)
        elif event.type == 'EpisodeFinish':
            print('Episode Finishing...')
        elif event.type == 'Unregister':
            client.session.delete(
                workspace_name=config_client.workspace, 
                session_id=registered_session.session_id
            )
            print("Unregistered simulator.")
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
        print("Unregistered simulator .")


