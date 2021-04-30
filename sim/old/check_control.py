import json 
import os
import time 
import random 
from collections import OrderedDict, deque
from typing import Dict, Any, Optional
import simpy
import numpy as np 
import time

class General:
    downtime_duration = 5  # seconds (s), fixed control frequency duration 

class DES(General):
    def __init__(self,env):
        super().__init__()
        self.env = env
        self.is_control_frequency_event = 0 
                    
    def processes_generator(self):  
        self.env.process(self.control_frequency_update())

    def control_frequency_update(self):
        while True: 
            ## define event type as control frequency event a ahead of the event 
            self.is_control_frequency_event = 1 
            print(f'start of downtime event at {self.env.now} and event requires control. call brain ...')

            time.sleep(1)
            yield self.env.timeout(self.downtime_duration)
            self.is_control_frequency_event = 0 
            ## change the flag to zero, in case other events occur.  
            print(f'we are now at {self.env.now} and control is not required for the next 100 seconds')
            time.sleep(1)
            yield self.env.timeout(100)
            print(f'completed the no control time, we are now at {self.env.now}')


    def reset(self):
        #self.episode_end = False
        self.processes_generator()  
        #self.env.step()    


    def step(self, brain_actions):
        # step through the controllable event
        print(f'applying brain action at {self.env.now}')
        ## there is a code that applies brain action 
        self.env.step()
        while self.is_control_frequency_event!= 1:
            self.env.step()

    def get_states(self):
        '''
        In this section, we will read the following:
        (1) Machine speed, an array indicating speed of all the machines 
        (2) conveyor speed, an array indicating speed of all the conveyors 
        (3) proxes, amount of can accumulations in each bin (Note: Not available in real world )
        (4) if proxes are full (two proxes before and two proxes after each machine is available in real world)
        (5) Throughput, i.e. the production rate from sink, i.e the speed of the last machine (will be used as reward)
        '''
        return {}
                

if __name__=="__main__":                             
    env = simpy.Environment()
    my_env = DES(env)
    my_env.reset()
    print('-------------------------------------------')
    iteration = 0 
    print('start of an episode, getting brain action ..')
    while True:
        print(f'iteration is {iteration}')
        print('Getting brain action ...')
        my_env.step(brain_actions = {'c0': 50, 'm0': 100, 'm1': 10} )
        #input('Press Enter to continue ...')    
        states = my_env.get_states()
        print('-------------------------------------------')
        iteration += 1 
        if iteration ==100000:
            my_env = DES(env)
            my_env.reset()
            iteration = 0


##sequence of events:

#(0, donwtime_start) (5, downtime_end) (5, regualr_run_start)(105, regular_run_end)(105, down_time_start)(110, down_time_end)(110, regular run_start)(210, regular_run_end)(210, downtime_start)

## idea control at the start of an event. assume no control lag      

#CONTROL(0, donwtime_start) (5, downtime_end) (5, regualr_run_start)(105, regular_run_end) CONTROL (105, down_time_start)(110, down_time_end)CONTROL(110, regular run_start)(210, regular_run_end)(210, downtime_start)


