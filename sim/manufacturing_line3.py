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
        self.client = BonsaiClient(config_client)

        # Load json file as simulator integration config type file
        with open('interface.json') as file:
            interface = json.load(file)

        # Create simulator session and init sequence id
        self.registration_info = SimulatorInterface(
                                name=interface['name'], 
                                timeout=interface['timeout'], 
                                simulator_context=config_client.simulator_context, 
        )
        self.registered_session = client.session.create(
                                workspace_name=config_client.workspace, 
                                body=registration_info
        )
    
        print("Registered simulator.")
        sequence_id = 1


class general:
    number_of_machines = 3   # number of general machines 
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
    def __init__(self):
        super.__init__()
        self.min_speed = general.min_speed
        self.max_speed = general.max_speed
        self._speed = 0
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
        if state == 'down' or state = 'idle':
            self.speed = 0

    # need to implement a setter and getter 
    def __repr__(self):
        return (f'Machine with id of {self.id} 
                runs at speed of {self.speed} and is in {self.state} mode')
    
class Conveyor(general):

    def __init__(self, id, speed, number_of_bins):
        super.__init__()
        self.min_speed = general.conveyor_min_speed
        self.max_speed = general.conveyor_max_speed
        self._speed = speed 
        self.id = id 
        self._state = 'idle'
        self.capcity = general.capacity
        self.number_of_bins = 10 
        self.bins_capacity = self.capcity/self.number_of_bins # self.number_of_bins*[bin_capacity]
        
        # each bin is a container and has a capacity and initial value  
        for i in range(0, self.number_of_bins):
            setattr(self, "bin" + str(i), simpy.Container(self.env, init = self.bins_capacity/2,  capacity = self.bins_capacity))

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
        if state == 'down' or state = 'idle':
            self.speed = 0

    # need to implement a setter and getter 
    def __repr__(self):
        return (f'Conveyor with id of {self.id} 
                runs at speed of {self.speed} and is in {self.state} mode')


class DES(general):
    def __init__(self):
        super.__init__()
        #input->m1->c1->m2->c2->m3->c3->m4->c4->m5 output 
        self.env = simpy.Environment()

        self._initialize_conveyor_buffers(self)
        self._initialize_macines(self)

        def _initialize_conveyor_buffers(self):
        #There is no input buffer for machine 1. We can safely assume that it is infinity 

            # note -1: as number of conveyors are one less than total number of machines 
            for i in range(0, general.number_of_machines-1):
                setattr(self, "c" + str(i),  Conveyor(id = i, speed = 10))
    
        def _initialize_macines(self):
        # create instance of each machine 
            for i in range(0, general.number_of_machines-1):
                setattr(self, "c" + str(i),  Machine(id = i, speed = 10))


    def downtime_generator(self):
         
        while True:
            print('started can processing. All machines working ')
            self.env.process(self.can_processor_machines)
            self.env.process(self.can_processor_conveyor)
            
            # Reserve the place holder to define the downtime events 
            # yield Timeout()
            # set a machine speed and state to a given mode 
            # receive speed actions from the brain 


    def can_processor(self):
        '''
        The idea is to take machine speed and update accumulation of cans at discharge of the each machine  

        '''

        control_frequency = general.control_frequency 
        yield self.env.timeout(control_frequency)  # every 1 control frequency, we will pause 
                                                    # and calculate the can accumulation in the buffer and in the conveyor 
                                                    # we may think of a lag as well. 
        
        # update number of cans at each bin
        for i in range(0, general.number_of_machines-1):
            bin_val = getattr(self, "c"+ str(i)+ ".bin"+ str(i))
            machine_speed = getattr(self, "m"+ str(i) + ".speed"
            bin_capacity = getattr(self, "c" + str(i) + "bin" )
            
            yield setattr(self, "c"+ str(i)+ ".bin"+ str(i), bin_val +  self.m1.speed*control_frequency)

        yield self.c1.bin1 += 
        yield self.c2.bin1 += self.m2.speed*control_frequency
        yield self.c3.bin1 += self.m3.speed*control_frequency
        yield self.c1.bin1 += self.m4.speed*control_frequency
        yield self.c1.bin1 += self.m5.speed*control_frequency

        # remove cans from the input buffer 
        yield self.m1bin -=  self.m1.speed*control_frequency 
        yield self.m2bin -=  self.m2.speed*control_frequency
        yield self.m3bin -=  self.m3.speed*control_frequency
        yield self.m4bin -=  self.m4.speed*control_frequency
        yield self.m5bin -=  self.m5.speed*control_frequency

        #now check their capacity and see if they should go to zero speed (idle speed)
        if self.m1bout == self.general.capacity:
                ## then machine speed wills be set to zero 
        if self.m2bout == Self.general.capacity:
                ## then mach

    def can_processor_conveyor_infeed_discharge(self):
        '''
        The idea is to take conveyor speed and capacity and update can accumulation on the conveyor  
        '''
        control_frequency = general.control_frequency

        yield self.env.timeout(control_frequency)
        # in this section, we wil check if the conveyor is full, in this case cans are not moving forward  
        if self.cb1< self.c1.capcity:
            yield self.m1bout -= self.c1.speed*control_frequency

        if self.cb2< self.c2.capcity:
            yield self.m2bout -= self.c2.speed*control_frequency
        
        if self.cb3< self.c3.capcity:
            yield self.m3bout -= self.c3.speed*control_frequency

        if self.cb4< self.c4.capcity:
            yield self.m4bout -= self.c4.speed*control_frequency


    def activity_m1(self):
        time_machine_started = self.env.now

        yield 



