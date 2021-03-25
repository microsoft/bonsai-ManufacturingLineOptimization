import json 
import os
import time 
import json
import time
from typing import Dict, Any, Optional
from microsoft_bonsai_api.simulator.client import BonsaiClientConfig, BonsaiClient
from microsoft_bonsai_api.simulator.generated.models import (
    SimulatorState,
    SimulatorInterface,
)
import simpy
import numpy as np 
# from dotenv import load_dotenv, set_key
# dir_path = os.path.dirname(os.path.realpath(__file__))
# log_path = "logs"


# this is an example consists of 5 machine 
# this version

class BonsaiCall:
    def __init__(self):
        self.config_client = BonsaiClientConfig()

        # Load json file as simulator integration config type file
        with open('interface.json') as file:
            interface = json.load(file)

        with open('workspace.json') as file:
            args = json.load(file)


        self.config_client.workspace = args['workspace']
        self.config_client.access_key = args['access_key']
        self.client = BonsaiClient(self.config_client)


        # Create simulator session and init sequence id
        self.registration_info = SimulatorInterface(
                                name=interface['name'], 
                                timeout=interface['timeout'], 
                                simulator_context=self.config_client.simulator_context, 
        )
        self.registered_session = self.client.session.create(
                                workspace_name=self.config_client.workspace, 
                                body=self.registration_info
        )

        print("Registered simulator.")
        print(f'registerd_session is {self.registered_session}')
        self.sequence_id = 1

    def get_event(self, simstates):
        
        # states = {'n_machine': np.random.randint(1,5), 'event_type': np.random.randint(5,10)}

        try:
            sim_state = SimulatorState(
                                sequence_id=self.sequence_id, state=simstates,
                                halted=False
                )
            event = self.client.session.advance(
                            workspace_name=self.config_client.workspace, 
                            session_id=self.registered_session.session_id, 
                            body=sim_state
                )
            self.sequence_id = event.sequence_id
            print("[{}] Last Event: {}".format(time.strftime('%H:%M:%S'), 
                                                    event.type))
                                                    
            # Event loop
            if event.type == 'Idle':
                time.sleep(event.idle.callback_time)
                print('Idling...')
            elif event.type == 'EpisodeStart':
                print('episode reseting...')
            elif event.type == 'EpisodeStep':
                print('episode stepping with brain action ...')
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
            return event
        except KeyboardInterrupt:
            # Gracefully unregister with keyboard interrupt
            self.client.session.delete(
                workspace_name=self.config_client.workspace, 
                session_id=self.registered_session.session_id
            )
            print("Unregistered simulator.")
        except Exception as err:
            # Gracefully unregister for any other exceptions
            self.client.session.delete(
                workspace_name=self.config_client.workspace, 
                session_id=self.registered_session.session_id
            )
            print("Unregistered simulator .")
    

class general:
    number_of_machines = 2   # number of general machines 
    machine_infeed_buffer = 100
    machine_discharge_buffer = 100 # 
    conveyor_capacity = 1000  # in cans 
    machine_min_speed = 10
    machine_max_speed = 100

    conveyor_min_speed = 10
    conveyor_max_speed = 100
    warmup_time = 100 # in seconds 
    downtime_generation_m4 = 100 # every 100 seconds machine 1 goes down
    downtime_m4 = 10 # in seconds 
    control_frequency = 1  # in seconds 

 
class Machine(general):
    '''
    This class represents a general machine, i.e. its states and function   

    '''
    def __init__(self, id , speed):
        super().__init__()
        self.min_speed = general.machine_min_speed
        self.max_speed = general.machine_max_speed
        self.id = id
        self._speed = speed
        self._state = 'idle'

    @property
    def speed(self):
        return self._speed
    @property
    def state(self):
        return self._state
    
    @speed.setter
    def speed(self, value):
        if not (self.min_speed < value < self.max_speed or value == 0):
            raise ValueError('speed must be 0 or between 10 and 100')
        self._speed = value 
        if value == 0 and self.state != "down":
            self.state = "idle"
        if value > 0:
            self.state = "active"

    @state.setter
    def state(self, state):
        if state not in ("prime","idle", "active", "down"):
            raise ValueError('state must be one of the following prime, idle, active, down')
        self._state = state
        if state == 'down' or state == 'idle':
            self.speed = 0

    # need to implement a setter and getter 
    def __repr__(self):
        return (f'Machine with id of {self.id} runs at speed of {self.speed} and is in {self.state} mode')
    

class DES(general):
    def __init__(self):
        super().__init__()
        #input->m1->c1->m2->c2->m3->c3->m4->c4->m5 output 
        self.env = simpy.Environment()

        self._initialize_machines()
        self._initialize_bonsai_connection()
        
    
    def _initialize_machines(self):
    # create instance of each machine 
        for i in range(0, general.number_of_machines):
            setattr(self, "m" + str(i),  Machine(id = i, speed = 0))
            print(getattr(self, "m" + str(i)))
    
    def _initialize_bonsai_connection(self):
        self.brain = BonsaiCall()

    def downtime_generator(self):
         
        while True:
            print('started can processing. All machines working ')
            self.env.process(self.can_processor())            
            # Reserve the place holder to define the downtime events 
            yield self.env.timeout(np.random.randint(0,100))
            # set a machine speed and state to a given mode 
            # receive speed actions from the brain 


    def can_processor(self):
        '''
        The idea is to take machine speed and update accumulation of cans at discharge of the each machine  

        '''
        control_frequency = 1 
        print(f'processing can at control frequency of {control_frequency}s')
        yield self.env.timeout(control_frequency)  # every 1 control frequency, we will pause 
                                                    # and calculate the can accumulation in the buffer and in the conveyor 
                                                    # we may think of a lag as well. 
        # update number of cans at each bin

        # for i in range(0, general.number_of_machines):
        #     machine = getattr(self , "m"+ str(i))
        #     yield setattr(self, "m" + str(i) + "speed", brain_action['speed'+str(i)])
    
    def run(self):
        self.env.process(self.downtime_generator())

        for i in range(1000):
            print(f'getting brain action at time: {self.env.now}')

            # need to replace with get state 
            machine_state = {}
            for i in range(0, general.number_of_machines):
                machine = getattr(self , "m"+ str(i))
                machine_state['speed'+ str(i)]= machine.speed

            
            machine_states = {'n_machine': np.random.randint(1,5), 'event_type': np.random.randint(5,10)}
            # create a function that calls brain
            
            brain_event = self.brain.get_event(simstates = machine_states)

            print(f'brain event is {brain_event}')
            while brain_event.type is 'Idle':
                '''
                retry to get action from brain  
                '''
                time.sleep(brain_event.idle.callback_time)
                brain_event = self.brain.get_event(sim_state = machine_state)

            if brain_event.type == 'EpisodeStart':
                print('episode reseting...')
            elif brain_event.type == 'EpisodeStep':
                self.env.step()
                print('episode stepping with brain action ...')
                brain_action = brain_event.episode_step.action
                print(f'Brain action is:', brain_action)


    

    
    

mySim = DES()
mySim.run()


