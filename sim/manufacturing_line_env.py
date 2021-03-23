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

'''
Simulation environment for multi machine simulation environment. 

'''

'''
components_config = {

m0 -> c0 ->m1-> c1 -> m2 -> c2 --> m3 
}

'''

class General:
    number_of_machines = 2   # number of General machines 
    machine_infeed_buffer = 100
    machine_discharge_buffer = 100 # 
    conveyor_capacity = 1000  # in cans 
    num_conveyor_bins = 10  # every conveyor is divided into 10 sections. For approximation and connection purposes  
    machine_min_speed = 10
    machine_max_speed = 100
    conveyor_min_speed = 10
    conveyor_max_speed = 100
    warmup_time = 100  # seconds(s) 
    downtime_event_gen_mean = 10    # seconds(s), on average every 100s one machine goes down 
    downtime_duration_mean = 5  # seconds(s), on average each downtime event lasts for about 30s.  
    control_frequency = 1  #  0: Control at generation of events, any other number indicates a fixed control frequency  

 
class Machine(General):
    '''
    This class represents a General machine, i.e. its states and function   

    '''
    def __init__(self, id , speed):
        super().__init__()
        self.min_speed = General.machine_min_speed
        self.max_speed = General.machine_max_speed
        self.id = id 
        self._speed = speed 
        self._state = 'idle' if speed == 0 else 'active'

    @property
    def speed(self):
        return self._speed
    @property
    def state(self):
        return self._state
    
    @speed.setter
    def speed(self, value):
        if not (self.min_speed <= value <= self.max_speed or value == 0):
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
        return (f'Machine with id of {self.id} \
                runs at speed of {self.speed} and is in {self.state} mode')
    
class Conveyor(General):

    def __init__(self, id, speed, number_of_bins, env):
        super().__init__()
        self.min_speed = General.conveyor_min_speed
        self.max_speed = General.conveyor_max_speed
        self._speed = speed 
        self.id = id 
        self._state = 'idle' if self._speed == 0 else 'active'
        self.capcity = General.conveyor_capacity
        self.number_of_bins = General.num_conveyor_bins
        ## self.number_of_bins*[bin_capacity]             
        self.bins_capacity = self.capcity/self.number_of_bins 
        ## each bin is a container and has a capacity and initial value  
        for i in range(0, self.number_of_bins):
            setattr(self, "bin" + str(i), simpy.Container(env, init = self.bins_capacity/2,  capacity = self.bins_capacity))

    @property
    def speed(self):
        return self._speed
    @property
    def state(self):
        return self._state
    
    @speed.setter
    def speed(self, value):
        if not (self.min_speed <= value <= self.max_speed or value == 0):
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

    ## need to implement a setter and getter 
    def __repr__(self):
        return (f'Conveyor with id of {self.id}\
                runs at speed of {self.speed} and is in {self.state} mode')


class DES(General):
    def __init__(self):
        super().__init__()
        #input->m1->c1->m2->c2->m3->c3->m4->c4->m5 output 
        self.env = simpy.Environment()
        self.components_speed = {}
        self._initialize_conveyor_buffers()
        self._initialize_machines()
        self.episode_end = False 
        print(f'components speed are\n:', self.components_speed)
        
    def _initialize_conveyor_buffers(self):
    ## There is no input buffer for machine 1. We can safely assume that it is infinity 
        # note -1: as number of conveyors are one less than total number of machines 
        for i in range(0, General.number_of_machines-1):
            setattr(self, "c" + str(i),  Conveyor(id = i, speed = 10, number_of_bins = General.num_conveyor_bins, env = self.env))
            print(getattr(self, "c" + str(i)))
            self.components_speed["c" + str(i)] = General.conveyor_max_speed
    
    def _initialize_machines(self):
    ## create instance of each machine 
        for i in range(0, General.number_of_machines):
            setattr(self, "m" + str(i),  Machine(id = i, speed = General.machine_max_speed))
            print(getattr(self, "m" + str(i)))
            self.components_speed["m" + str(i)] = General.machine_max_speed

    def processes_generator(self):  
        print('started can processing. All machines working ')
        self.env.process(self.downtime_generator())
        self.env.process(self.control_frequency_update())  # aims to update machine speed at defined control freq
        #self.env.process(self.event_driven_update())  # aims to update machine speed at when events occur 
    
    def control_frequency_update(self):
        while not self.episode_end: 
            yield self.env.timeout(General.control_frequency)
            print(f'control freq of all events {self.env.now} s ...')
            #self.env.process(self.can_processor_machines())
            self.update_machines_speed()
            self.update_conveyors_speed()
            
            # Reserve the place holder to define the downtime events 
            # yield Timeout()
            # set a machine speed and state to a given mode 
            # receive speed actions from the brain 

    def event_driven_update(self):
        '''
        to be completed 
        '''
        pass
    
    def downtime_generator(self):
        while not self.episode_end:
            yield self.env.timeout(General.downtime_duration_mean) 
            print(f'................ now a machine went down at {self.env.now} ...')


    def update_machines_speed(self):
        '''
        The idea is to take machine speed and update accumulation of cans at discharge of the each machine  

        '''  
        for i in range(0, General.number_of_machines):
            print(f'now at {self.env.now} s updating mechine speed')
            machine_speed = self.components_speed['m' + str(i)]
            setattr(eval('self' + ".m" + str(i)),'speed', machine_speed)
            print(eval('self' + ".m" + str(i)))


        # update number of cans at each bin
        # for i in range(0, General.number_of_machines-1):
        #     bin_val = getattr(self, "c"+ str(i)+ ".bin"+ str(i))
        #     machine_speed = getattr(self, "m"+ str(i) + ".speed")
        #     bin_capacity = getattr(self, "c" + str(i) + "bin" )
        #     setattr(self, "c"+ str(i)+ ".bin"+ str(i), bin_val +  self.m1.speed*control_frequency)

        # yield self.c1.bin1 += 
        # yield self.c2.bin1 += self.m2.speed*control_frequency
        # yield self.c3.bin1 += self.m3.speed*control_frequency
        # yield self.c1.bin1 += self.m4.speed*control_frequency
        # yield self.c1.bin1 += self.m5.speed*control_frequency

        # # remove cans from the input buffer 
        # yield self.m1bin -=  self.m1.speed*control_frequency 
        # yield self.m2bin -=  self.m2.speed*control_frequency
        # yield self.m3bin -=  self.m3.speed*control_frequency
        # yield self.m4bin -=  self.m4.speed*control_frequency
        # yield self.m5bin -=  self.m5.speed*control_frequency

        #now check their capacity and see if they should go to zero speed (idle speed)
        # if self.m1bout == self.General.capacity:
        #         ## then machine speed wills be set to zero 
        # if self.m2bout == Self.General.capacity:
                ## then mach

    def update_conveyors_speed(self):
        '''
        The idea is to take conveyor speed and capacity and update can accumulation on the conveyor  
        ''' 
        print(f'now at {self.env.now} s processing can at {General.control_frequency} control frequency')
        for i in range(0, General.number_of_machines-1):
            print(f'now at {self.env.now} s updating conveyor speed')
            conveyor_speed = self.components_speed['c' + str(i)]
            setattr(eval('self' + ".c" + str(i)),'speed', conveyor_speed)
            print(eval('self' + ".c" + str(i)))


        # in this section, we wil check if the conveyor is full, in this case cans are not moving forward  
        # if self.cb1< self.c1.capcity:
        #     yield self.m1bout -= self.c1.speed*control_frequency

        # if self.cb2< self.c2.capcity:
        #     yield self.m2bout -= self.c2.speed*control_frequency
        
        # if self.cb3< self.c3.capcity:
        #     yield self.m3bout -= self.c3.speed*control_frequency

        # if self.cb4< self.c4.capcity:
        #     yield self.m4bout -= self.c4.speed*control_frequency


    # def activity_m1(self):
    #     time_machine_started = self.env.now

    #     yield 

    def reset(self):
        self.episode_end = False
        self.processes_generator()

    def step(self, brain_actions):
        ## update the speed dictionary for those comming from the brain 
        for key in list(brain_actions.keys()):
            self.components_speed[key] = brain_actions[key]
        
        self.env.step()
        #self.env.run(until=2000)
    def end_episode(self):
        self.episode_end = True
        

my_env = DES()
my_env.reset()
base = 20 
iteration = 0 
while True:
    my_env.step(brain_actions = {'c0': base+iteration, 'm0': base+iteration, 'm1': base+iteration} )
    input('Press Enter to continue ...')    
    iteration += 1 
    print(iteration)
    if iteration ==10:
        my_env.end_episode()
        my_env = DES()
        my_env.reset()
        iteration = 0

    



