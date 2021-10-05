from textwrap import indent
from .line_config import adj, adj_conv # [AJ]: For single line
import json
import os
import time
import random
from collections import OrderedDict, deque
from typing import Dict, Any, Optional, ValuesView
import simpy
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.animation import FuncAnimation
import networkx as nx
from networkx.generators import line
import pandas as pd
import threading
from threading import Lock
import pdb
# from queue import Queue
lock = Lock()

'''
Simulation environment for multi machine manufacturing line.
'''

random.seed(10)


def get_machines_conveyors_sources_sets(adj, adj_conv):
    adj = OrderedDict(sorted(adj.items()))
    adj_conv = OrderedDict(sorted(adj_conv.items()))
    conveyors = set()
    sources = set()
    sinks = set()
    for key in list(adj.keys()):
        for element in adj[key]:
            if ("source" not in element) and ("sink" not in element):
                conveyors.add(element)
            elif "source" in element:
                sources.add(element)
            elif "sink" in element:
                sinks.add(element)
            else:
                pass

    return sorted(list(set(adj.keys()))), sorted(list(conveyors)), sorted(list(sources)), sorted(list(sinks))


class General:
    machines, conveyors, sources, sinks = get_machines_conveyors_sources_sets(
        adj, adj_conv)
    number_of_machines = len(machines) # number of General machines
    number_of_conveyors = len(conveyors) # number of conveyors
    conveyor_min_speed = 10
    conveyor_max_speed = 1000
    conveyor_speed = conveyor_max_speed    
    # downtime_event_prob = 0.1 # probability applied every "downtime-even_gen_mean" to create downtime on a random machine
    # seconds (s) average time between random downtime events
    interval_downtime_event_mean = 15
    # deviation, a random interval_downtime_event is generated in range [interval_downtime_event_mean - interval_downtime_event_dev, interval_downtime_event_mean + interval_downtime_event_dev]
    interval_downtime_event_dev = 10
    # seconds(s), mean duration of each downtime event
    downtime_event_duration_mean = 4
    # seconds(s), deviation from mean. [downtime_event_duration_mean - downtime_event_duration_std, downtime_event_duration_mean + downtime_event_duration_std]
    downtime_event_duration_dev = 3
    # distribution parameters of startup time
    idletime_duration = random.sample(range(2, 10), number_of_machines)
    control_frequency = 1  # seconds (s), fixed control frequency duration
    # control type: -1: control at fixed time frequency but no downtime event 0: control at fixed time frequency
    # control type: 1: event driven, i.e. when a downtime occurs, 2: both at fixed control frequency and downtime
    control_type = 0
    number_parallel_downtime_events = 3
    # placeholder for different configurations of machines.
    layout_configuration = 1
    # granularity of simulation updates. Larger values make simulation less accurate. Recommended value: 1.
    simulation_time_step = 1
    down_machine_index = -1 # [AJ]: from 0 to 5 to refer to the specific down machine, -1 for random down machine
    
    initial_bin_level = 100 # [AJ]: initial capacity of the bin (from 0 to 100)
    bin_maximum_capacity = 100 # [AJ]: maximum capacity of each bin
    num_conveyor_bins = 10 # number of bins per conveyor
    conveyor_capacity = bin_maximum_capacity * num_conveyor_bins  # in cans
    
    infeed_prox_upper_limit = 50 # [AJ]: threshold to turn on/off the prox - infeed
    infeed_prox_lower_limit =  50 # # [AJ]: threshold to turn on/off the prox - infeed
    discharge_prox_upper_limit = 50 # [AJ]: threshold to turn on/off the prox - discharge
    discharge_prox_lower_limit = 50 # [AJ]: threshold to turn on/off the prox - discharge
    machine0_min_speed = 100
    machine1_min_speed = 25
    machine2_min_speed = 50
    machine3_min_speed = 40
    machine4_min_speed = 70
    machine5_min_speed = 70
    machine_min_speed = [machine0_min_speed, machine1_min_speed, machine2_min_speed,
     machine3_min_speed, machine4_min_speed, machine5_min_speed]
    machine0_max_speed = 150
    machine1_max_speed = 170
    machine2_max_speed = 160
    machine3_max_speed = 160
    machine4_max_speed = 160
    machine5_max_speed = 250
    machine_max_speed = [machine0_max_speed, machine1_max_speed, machine2_max_speed,
     machine3_max_speed, machine4_max_speed, machine5_max_speed]
    machine0_initial_speed = 110
    machine1_initial_speed = 50
    machine2_initial_speed = 70
    machine3_initial_speed = 60
    machine4_initial_speed = 100
    machine5_initial_speed = 120
    machine_initial_speed = [machine0_initial_speed, machine1_initial_speed, machine2_initial_speed,
     machine3_initial_speed, machine4_initial_speed, machine5_initial_speed]
    
    infeedProx_index1 = 1 # bin index for location of first infeed sensor
    infeedProx_index2 = 4 # bin index for location of second infeed sensor
    dischargeProx_index1 = 0 # bin index for location of first discharge sensor
    dischargeProx_index2 = 3 # bin index for location of second discharge sensor
    
    num_cans_at_discharge_index1 = (num_conveyor_bins - dischargeProx_index1 - 1) * bin_maximum_capacity + discharge_prox_lower_limit
    num_cans_at_discharge_index2 = (num_conveyor_bins - dischargeProx_index2 - 1) * bin_maximum_capacity + discharge_prox_upper_limit

    num_cans_at_infeed_index1 = (infeedProx_index1 - 1) * bin_maximum_capacity + infeed_prox_lower_limit
    num_cans_at_infeed_index2 = (infeedProx_index2 - 1) * bin_maximum_capacity + infeed_prox_upper_limit


class Machine(General):
    '''
    This class represents a General machine, i.e. its states and function
    '''

    def __init__(self, id, speed):
        super().__init__()      
        self.id = id
        self._speed = speed
        self._state = 'idle' if speed == 0 else 'active'
        self.idle_counter = 0
        # keep track of the down time event times.

    @property
    def speed(self):
        return self._speed

    @property
    def state(self):
        return self._state

    # explanation of states
    # idle: machine speed is 0 due to conveyor being overloaded/underloaded
    # down: machine speed is 0 due to jamming/hardware issue
    # startup: machine speed is 0 due to being in startup phase after being idle
    # active: machine is running at a non-zero speed

    @speed.setter
    def speed(self, value):
        if not (value <= self.machine_max_speed[self.id] or value == 0):
            raise ValueError(f'speed must be 0 or smaller than {self.machine_max_speed[self.id]}')
        if self.state == "down":
            self._speed = 0
            print('machine is down, machine speed will be kept zero')
        elif self.state == "idle":
            self._speed = 0
            print('machine is idle, machine speed will be kept zero')
        elif self.state == "startup":
            self._speed = 0
            print('machne is startup, machine speed will be kept zero')     
        elif value > 0 and self.state != "down" and self.state != "idle" and self.state != "startup":
            self._speed = value
            self.state = "active"

    @state.setter
    def state(self, state):
        if state not in ("idle", "active", "down", "startup"):
            raise ValueError(
                'state must be one of the idle, active, down, startup')
        self._state = state
        if state == 'down' or state == 'idle' or state == 'startup':
            self._speed = 0

    def __repr__(self):
        return (f'Machine with id of {self.id} \
                runs at speed of {self.speed} and is in {self.state} mode')


class Conveyor(General):

    def __init__(self, id, speed, env):
        super().__init__()
        self.min_speed = General.conveyor_min_speed
        self.max_speed = General.conveyor_max_speed
        # [AJ]: Adding general conveyor speed
        self.conv_speed = General.conveyor_speed
        self._speed = speed
        self.id = id
        self._state = 'idle' if self._speed == 0 else 'active'
        self.bins_capacity = self.conveyor_capacity / self.num_conveyor_bins
        # each bin is a container and has a capacity and initial value
        for i in range(0, self.num_conveyor_bins):
            setattr(self, "bin" + str(i), self.initial_bin_level)
            setattr(self, "previous_bin_level" + str(i), 0)

    @property
    def speed(self):
        return self._speed

    @property
    def state(self):
        return self._state

    @speed.setter
    def speed(self, value):
        if not (self.min_speed <= value <= self.max_speed or value == 0):
            raise ValueError(
                f'speed must be 0 or between {self.min_speed} and {self.max_speed}')
        if self.state == "down":
            self._speed = 0
            print('Illegal action: machine is down, machine speed will be kept zero')
        elif value == 0 and self.state != "down":
            self.state = "idle"
            self._speed = value
        elif value > 0:
            self._speed = value
            self.state = "active"

    @state.setter
    def state(self, state):
        if state not in ("prime", "idle", "active", "down"):
            raise ValueError(
                'state must be one of the following prime, idle, active, down')
        self._state = state
        if state == 'down' or state == 'idle':
            self._speed = 0

    # need to implement a setter and getter
    def __repr__(self):
        return (f'Conveyor with id of {self.id}\
            runs at speed of {self.speed} and is in {self.state} mode')


class Sink():
    def __init__(self, id):
        super().__init__()
        # count of product accumulation at a sink, where manufactured product is collected.
        # assumption is an infinite capacity
        self.product_count = 0
        # a deque to track can accumulation between events
        self.count_history = deque([0, 0, 0], maxlen=10)

class DES(General):
    def __init__(self, env):
        super().__init__()
        self.env = env
        self.components_speed = {}
        self.iteration = 1
        self.conveyor_initial_level = General.initial_bin_level * General.num_conveyor_bins
        self.all_conveyor_levels = [self.conveyor_initial_level] * General.number_of_conveyors
        self.all_conveyor_levels_estimate = [self.conveyor_initial_level] * General.number_of_conveyors
        self.down_cnt = [0] * General.number_of_machines
        self.mean_downtime_offset = [0] * General.number_of_machines
        self.max_downtime_offset = [0] * General.number_of_machines
        self.brain_speed = [0] * General.number_of_machines
        self._initialize_conveyor_buffers()
        self._initialize_machines()
        self._initialize_sink()
        self.episode_end = False
        # a flag to identify events that require control
        self.is_control_downtime_event = 0 # [AJ]: flag that a downtime event has occured
        self.is_control_frequency_event = 0 # [AJ]: flag that a fixed control frequency event has occured
        self.downtime_event_times_history = deque([0, 0, 0], maxlen=10)
        self.downtime_machine_history = deque([0, 0, 0], maxlen=10)
        self.control_frequency_history = deque([0, 0, 0], maxlen=10)
        self._initialize_downtime_tracker()
        self._check_simulation_step()
        self.sinks_throughput_abs = 0
        print(f'components speed are\n:', self.components_speed)

    def _initialize_conveyor_buffers(self):
        # There is no input buffer for machine 1. We can safely assume that it is infinite
        # note -1: as number of conveyors are one less than total number of machines
        id = 0
        for conveyor in General.conveyors:
            # [AJ]: Set the conveyor speed at the general conveyor speed which is the max speed
            setattr(self, conveyor,  Conveyor(id = id, speed = General.conveyor_speed, env = self.env))
            # [AJ]: Set the component speed at the general conveyor speed which is the max speed
            self.components_speed[conveyor] = General.conveyor_speed

            id += 1

    def _initialize_machines(self):
        # create instance of each machine
        id = 0
        for machine in General.machines:
            setattr(self, machine,  Machine(
                id=id, speed=self.machine_initial_speed[id])) # [AJ]: Added by Amir   
            self.components_speed[machine] = self.machine_initial_speed[id]
            id += 1

    def _initialize_sink(self):
        id = 0
        for sink in General.sinks:
            setattr(self, sink, Sink(id=id))
            id += 1

    def _initialize_downtime_tracker(self):
        # initialize a dictionary to keep track of remaining downtime
        self.downtime_tracker_machines = {}
        self.downtime_tracker_conveyors = {}
        for machine in General.machines:
            self.downtime_tracker_machines[machine] = 0
        for conveyor in General.conveyors:
            self.downtime_tracker_conveyors[conveyor] = 0

    def _check_simulation_step(self):
        '''
        simulation step should be equal or smaller than control frequency
        '''
        if self.control_frequency < self.simulation_time_step:
            print(
                'Simulation time step should be equal or smaller than control frequency!')
            print(
                f'Adjusting simulation time step from {self.simulation_time_step} s to {self.control_frequency}')
            time.sleep(1)
            self.simulation_time_step = self.control_frequency
        else:
            pass

    def processes_generator(self):
        print('Started can processing ... ')
        self.env.process(self.update_line_simulation_time_step())

        if self.control_type == -1:
            # no downtime event used for brain training for steady state
            self.env.process(self.control_frequency_update())
        elif self.control_type == 0:
            self.env.process(self.control_frequency_update())
            for num_process in range(0, self.number_parallel_downtime_events):
                self.env.process(self.downtime_generator())
        elif self.control_type == 1:
            for num_process in range(0, self.number_parallel_downtime_events):
                self.env.process(self.downtime_generator())
            # self.env.process(self.downtime_generator())
        elif self.control_type == 2:
            self.env.process(self.control_frequency_update())
            for num_process in range(0, self.number_parallel_downtime_events):
                self.env.process(self.downtime_generator())
        else:
            raise ValueError(f"Only the following modes are currently available: \
                -1: fixed control frequency with no downtime event, \
                    fixed control frequency (0) or event driven (1), both (2) with downtime events")

    def control_frequency_update(self):
        while True: # [AJ]: an infinite loop for the generator function
            # define event type as control frequency event a ahead of the event
            self.is_control_frequency_event = 1
            self.is_control_downtime_event = 0
            print(
                f'................ control at {self.env.now} and event requires control: {self.is_control_frequency_event}...')
            yield self.env.timeout(self.control_frequency) # [AJ]: the yield signals the simulation that it wants to wait for the next event to occur
            self.is_control_frequency_event = 0
            # change the flag to zero, in case other events occur.
            print('-------------------------------------------')
            print(f'control freq event at {self.env.now} s ...')

    def update_line_simulation_time_step(self):
        '''
        Updating can accumulation at fixed time interval, i.e General.simulation_time_step
        '''
        while True: # [AJ]: an infinite loop for the generator function
            self.is_control_frequency_event = 0
            self.is_control_downtime_event = 0
            # [AJ]: the yield signals the simulation that it wants to wait for the next event (either fixed control frequency event or down time event) to occur
            yield self.env.timeout(self.simulation_time_step)
            print(f'----simulation update at {self.env.now}')
            self.update_line()

    def downtime_generator(self):
        '''
        Parameters used in General will be used to generate downtime events on a random machine.
        '''
        while True:    
            machines_list = list(General.machines) # [AJ]: Added by Amir
            print('The list of machines is', machines_list)
            for machine in General.machines:
                machine_status = getattr(eval('self.' + machine), 'state')
                if machine_status == 'down' or machine_status == 'startup':
                    machines_list.remove(machine)
            print('The list of non-down machines is', machines_list)
            if self.down_machine_index == -1: # [AJ]: pick a machine randomly to go down
                down_machine = random.choice(machines_list)
            else: # [AJ]: pick a specific machine to go down
                down_machine = machines_list[self.down_machine_index]
            print('down machine is', down_machine)
            self.is_control_downtime_event = 1
            self.is_control_frequency_event = 0
            # print(
            #     f'................ now machine {down_machine} goes down at {self.env.now} and event requires control: {self.is_control_downtime_event}...')
            setattr(eval('self.' + down_machine), 'state', 'down')
            # track current downtime event for the specific machine
            random_downtime_duration = random.randint(self.downtime_event_duration_mean-self.downtime_event_duration_dev,
                                                           self.downtime_event_duration_mean + self.downtime_event_duration_dev)
            print('down time duration is', random_downtime_duration)
            # only add control events to a deque
            self.track_event(down_machine, random_downtime_duration)
            yield self.env.timeout(random_downtime_duration) # [AJ]: it means machine should go down for this amount of time
            
            setattr(eval('self.' + down_machine), 'state', 'active') # [AJ]: put the machine in active mode so that it can receive the new speed from brain            
            setattr(eval('self.' + down_machine), "speed", self.components_speed[down_machine])     

            print(
                f'................ let machines run for a given period of time without any downtime event')
            self.is_control_downtime_event = 0
            self.is_control_frequency_event = 0
            interval_downtime_event_duration = random.randint(self.interval_downtime_event_mean - self.interval_downtime_event_dev,
                                                              self.interval_downtime_event_mean + self.interval_downtime_event_dev)
            yield self.env.timeout(interval_downtime_event_duration) # [AJ]: in simple terms, it means wait for this amount of time
       
    
    def idletime_generator(self, machine, machine_index):
        '''
        Parameters used in General will be used to generate idle time events.
        '''
        machine_state = getattr(eval('self.' + machine), 'state')
        machine_counter = getattr(eval('self.' + machine), 'idle_counter')
        machine_idletime_duration = self.idletime_duration[machine_index]

        if machine_state == "startup":
            setattr(eval('self.' + machine), 'state', 'startup')
            setattr(eval('self.' + machine), 'speed', 0)
            machine_counter += 1
            # [AJ]: Shall I add this or not?
            # setattr(eval('self.' + machine), 'idle_counter', machine_counter)
            if machine_counter == machine_idletime_duration:
                setattr(eval('self.' + machine), 'state', 'active')
                setattr(eval('self.' + machine), "speed", self.components_speed[machine])     
                machine_counter = 0
            else:
                pass
        setattr(eval('self.' + machine), 'idle_counter', machine_counter)
            
    
    def downtime_estimator(self):

        max_downDuration = General.downtime_event_duration_mean + General.downtime_event_duration_dev
        mean_downDuration = General.downtime_event_duration_mean
        for ind, machine in enumerate(General.machines):
            machine_state = getattr(eval('self.' + machine), 'state')
            if machine_state == 'down':
                offset_mean = mean_downDuration - self.down_cnt[ind]
                offset_max = max_downDuration - self.down_cnt[ind]
                self.mean_downtime_offset[ind] = offset_mean
                self.max_downtime_offset[ind] = offset_max
                self.down_cnt[ind] += 1
            else:
                self.down_cnt[ind] = 0
                self.mean_downtime_offset[ind] = 0
                self.max_downtime_offset[ind] = 0
                continue
        # print('down time estimation')
        # print(self.mean_downtime_offset)
        # print(self.max_downtime_offset)
    
    def update_line(self):

        self.get_conveyor_level()
        self.plc_control_machine_speed()
        index = 0
        for machine in General.machines:
            self.idletime_generator(machine, index)
            index += 1        
        self.actual_machine_speeds()
        self.store_bin_levels()
        self.accumulate_conveyor_bins()
        self.update_sinks_product_accumulation()
        self.get_conveyor_level_estimate() ## Added estimation
        self.downtime_estimator()

    def update_sinks_product_accumulation(self):
        '''
        For each machine, we will check if to is connected to sink, then accumulate product according to machine speed .
        '''
        # update machine infeed and discharge buffers according to machine speed
        for machine in adj.keys():
            # [AJ]: From line_config.py, adj is a dictionary
            # [AJ]: The machine is the key and before/after conveyors are the values
            # [AJ]: First value is infeed and second value is discharge
            adj_conveyors = adj[machine]
            infeed = adj_conveyors[0] # [AJ]: the conveyor before machine
            discharge = adj_conveyors[1] # [AJ]: the conveyor after the machine
            # amount of cans going from one side to the other side
            delta = getattr(eval('self.' + machine), 'speed') * \
                self.simulation_time_step # [AJ]: delta is speed (cans per minutes) * minute

            if 'sink' in discharge: # [AJ]: if the machine is the last machine in the line
                # now check buffer full  ....................................TODO:
                level = getattr(getattr(self, discharge), "product_count")
                setattr(eval('self.' + discharge),
                        "product_count", level + delta)

    def track_event(self, down_machine, random_downtime_duration):
        '''
        Once called, will add current simulation time and also
        It will be used to track the occurrence time of downtime events
        '''
        self.downtime_event_times_history.append(self.env.now)
        self.downtime_machine_history.append(
            (self.env.now, down_machine, random_downtime_duration))

    def track_control_frequency(self):
        self.control_frequency_history.append(self.env.now)

    def track_sinks_throughput(self):
        for sink in General.sinks:
            level = getattr(getattr(self, sink), "product_count")
            s = eval('self.' + sink)
            s.count_history.append(level)

    def calculate_inter_event_delta_time(self):
        '''
        The goal is to keep track of time lapsed between events.
        potential use: (1) calculate remaining downtime (2) for reward normalization
        '''
        return self.downtime_event_times_history[-1] - self.downtime_event_times_history[-2]

    def calculate_control_frequency_delta_time(self):
        '''
        To track time between brain controls following the config parameter, set through inkling
        '''
        return self.control_frequency_history[-1] - self.control_frequency_history[-2]

    def update_machines_speed(self):
        '''
        update the speed of the machine using brain actions that has written in components_speed[machine] dictionary
        '''

        for machine in General.machines:
            # print(f'now at {self.env.now} s updating machine speed')
            updated_speed = self.components_speed[machine]
            setattr(eval('self.' + machine), 'speed', updated_speed)
            print(eval('self.' + machine))

    def get_conveyor_level(self):
        '''
        get the total number of cans that exist in the conveyor at each iteration
        '''      

        self.all_conveyor_levels = []
        for conveyor in adj_conv.keys():
            conveyor_level = 0

            for bin_num in range(General.num_conveyor_bins-1, -1, -1):
                bin_level = getattr(getattr(self, conveyor), 
                                "bin" + str(bin_num))
                conveyor_level += bin_level # [AJ]: total number of cans in the conveyor
            self.all_conveyor_levels.append(conveyor_level) # [AJ]: array that contains the total level of all conveyors

    def get_conveyor_level_estimate_initally(self):
        '''
        get the estimate of the total number of cans that exist in the conveyor initally
        '''    
        # [KN]
        # num_cans_at_discharge_index1 =  950
        # num_cans_at_discharge_index2 = 650
        # num_cans_at_infeed_index1 = 50
        # num_cans_at_infeed_index2 = 350

        self.all_conveyor_levels_estimate = []
        for conveyor_level in self.all_conveyor_levels:
            if conveyor_level <= General.num_cans_at_infeed_index1:
                conveyor_estimate_initial= round(General.num_cans_at_infeed_index1/2)
                
            elif(conveyor_level > General.num_cans_at_infeed_index1) and (conveyor_level < General.num_cans_at_infeed_index2):
                conveyor_estimate_initial= round((General.num_cans_at_infeed_index1 + General.num_cans_at_infeed_index2)/2)

            elif(conveyor_level >= General.num_cans_at_infeed_index2) and (conveyor_level < General.num_cans_at_discharge_index2):
                conveyor_estimate_initial= round((General.num_cans_at_infeed_index2 + General.num_cans_at_discharge_index2)/2)

            elif(conveyor_level >= General.num_cans_at_discharge_index2) and (conveyor_level < General.num_cans_at_discharge_index1):
                conveyor_estimate_initial= round((General.num_cans_at_discharge_index2 + General.num_cans_at_discharge_index1)/2)

            else:
                conveyor_estimate_initial= round(General.num_cans_at_discharge_index1/2)

            self.all_conveyor_levels_estimate.append(conveyor_estimate_initial)
     
    def get_conveyor_level_estimate(self):
        '''
        estimate the total number of cans that exist on the conveyor at each iteration
        ''' 
        
        machines_speed = []
        for machine in General.machines:
            machines_speed.append(getattr(eval('self.' + machine), 'speed'))
        
        #######
        # minus 1, minus2
        conveyor_infeed_m1_prox_empty = []
        conveyor_infeed_m2_prox_empty = []
        conveyor_previous_infeed_m1_prox_empty = []
        conveyor_previous_infeed_m2_prox_empty = []

        # plus 1, plus2
        conveyor_discharge_p1_prox_full = []
        conveyor_discharge_p2_prox_full = []
        conveyor_previous_discharge_p1_prox_full = []
        conveyor_previous_discharge_p2_prox_full = []

        for conveyor in General.conveyors:
            # [AJ]: The following is added by Amir
            # The infeed sensor next to machine
            conveyor_infeed_m1_prox_empty.append(int(getattr(
                getattr(self, conveyor), "bin" + str(self.num_conveyor_bins-self.infeedProx_index1))) <= self.infeed_prox_lower_limit)
            # The second infeed sensor next to machine
            conveyor_infeed_m2_prox_empty.append(int(getattr(
                getattr(self, conveyor), "bin" + str(self.num_conveyor_bins-self.infeedProx_index2))) < self.infeed_prox_upper_limit)

            conveyor_previous_infeed_m1_prox_empty.append(int(getattr(
                getattr(self, conveyor), "previous_bin_level" + str(self.num_conveyor_bins-self.infeedProx_index1))) <= self.infeed_prox_lower_limit)
            # The second infeed sensor next to machine
            conveyor_previous_infeed_m2_prox_empty.append(int(getattr(
                getattr(self, conveyor), "previous_bin_level" + str(self.num_conveyor_bins-self.infeedProx_index2))) < self.infeed_prox_upper_limit)                

            # [AJ]: The following is added by Amir
            # The discharge sensor next to machine
            conveyor_discharge_p1_prox_full.append(
                int(getattr(getattr(self, conveyor), "bin" + str(self.dischargeProx_index1))) >= self.discharge_prox_lower_limit)
            # The second discharge sensor next to machine
            conveyor_discharge_p2_prox_full.append(
                int(getattr(getattr(self, conveyor), "bin" + str(self.dischargeProx_index2))) >= self.discharge_prox_upper_limit)    

            conveyor_previous_discharge_p1_prox_full.append(
                int(getattr(getattr(self, conveyor), "previous_bin_level" + str(self.dischargeProx_index1))) >= self.discharge_prox_lower_limit)
            # The second discharge sensor next to machine
            conveyor_previous_discharge_p2_prox_full.append(
                int(getattr(getattr(self, conveyor), "previous_bin_level" + str(self.dischargeProx_index2))) >= self.discharge_prox_upper_limit)            

        #######
        all_conveyor_levels_estimate_temp = []
        
        for i in range(len(self.all_conveyor_levels_estimate)):
            ## Predict Phase of Estimator
            _estimate = self.all_conveyor_levels_estimate[i] + machines_speed[i] - machines_speed[i+1]

            ## Update Phase of Estimator (Assumption: Measurement are true whenever available)
            if conveyor_infeed_m1_prox_empty[i] != conveyor_previous_infeed_m1_prox_empty[i]:
                _estimate = General.num_cans_at_infeed_index1
            elif conveyor_infeed_m2_prox_empty[i] != conveyor_previous_infeed_m2_prox_empty[i]:
                _estimate = General.num_cans_at_infeed_index2
            elif conveyor_discharge_p1_prox_full[i] != conveyor_previous_discharge_p1_prox_full[i]:
                _estimate = General.num_cans_at_discharge_index1
            elif conveyor_discharge_p2_prox_full[i] != conveyor_previous_discharge_p2_prox_full[i]:
                _estimate = General.num_cans_at_discharge_index2

            all_conveyor_levels_estimate_temp.append(_estimate)

        self.all_conveyor_levels_estimate = all_conveyor_levels_estimate_temp.copy()

    def store_bin_levels(self):
        for conveyor in adj_conv.keys():        
            for bin_num in range(General.num_conveyor_bins-1, -1, -1):
                previous_bin_level = getattr(getattr(self, conveyor), 
                                "bin" + str(bin_num)) # [AJ]: get the level of the conveyor bin
                setattr(eval('self.' + conveyor), "previous_bin_level" +
                        str(bin_num), previous_bin_level) # [AJ]: set the previous level of the bin             
    
    def accumulate_conveyor_bins(self):
        
        index = 0
        for conveyor in adj_conv.keys():
            capacity = getattr(getattr(self, conveyor), "bins_capacity") # [AJ]: maximum capacity of the bin
            current_conveyor_level = self.all_conveyor_levels[index] # [AJ]: current conveyor level
            # print('original current_conveyor_level is', current_conveyor_level)

            adj_machines = adj_conv[conveyor] # [AJ]: the machines corresponding to each conveyor
            previous_machine = adj_machines[0] # [AJ]: the machine before the conveyor
            next_machine = adj_machines[1] # [AJ]: the machine after the conveyor

            # [AJ]: amount of cans processed by the machine before the conveyor - input to the conveyor
            delta_previous = getattr(eval('self.' + previous_machine), 'speed') * \
                self.simulation_time_step
            # print('previous machine speed is', getattr(eval('self.' + previous_machine), 'speed'))
            # print('previous delta is', delta_previous)
            # [AJ]: amount of cans processed by the machine after the conveyor - output from the conveyor
            delta_next = getattr(eval('self.' + next_machine), 'speed') * \
                self.simulation_time_step
            # print('next machine speed is', getattr(eval('self.' + next_machine), 'speed'))
            # print('next delta is', delta_next)

            current_conveyor_level += delta_previous # [AJ]: addition of cans receiving from machine before the conveyor 
            # print('current_conveyor_level after addition is', current_conveyor_level)
            current_conveyor_level -= delta_next # [AJ]: subtraction of cans passing to the machine after the conveyor
            # print('current_conveyor_level after subtraction is', current_conveyor_level)
            current_conveyor_level = max(0, current_conveyor_level)

            for bin_num in range(General.num_conveyor_bins-1, -1, -1): # [AJ]: accumulate cans in the conveyor from last bin to first bin
                
                setattr(eval('self.' + conveyor), "bin" +
                        str(bin_num), 0) # [AJ]: set the level of the bin to 0
                bin_level = min(current_conveyor_level, capacity)
                setattr(eval('self.' + conveyor), "bin" +
                        str(bin_num), bin_level)
                new_bin_level = getattr(getattr(self, conveyor), 
                                "bin" + str(bin_num)) # [AJ]: get the level of the conveyor bin
                # print('for bin number', bin_num)
                # print('the new bin level is', new_bin_level)

                current_conveyor_level -= new_bin_level 
                if current_conveyor_level <= 0:
                    current_conveyor_level = 0
            index += 1

    def plc_control_machine_speed(self):
        '''
        rule1: machine should stop, i.e. speed = 0, if discharge prox exceeds a threshold
        rule2: machine should stop, i.e. speed = 0, if infeed prox falls below a threshold
        '''
        for machine in adj.keys():
            adj_conveyors = adj[machine]
            infeed = adj_conveyors[0] # [AJ]: conveyor before the machine
            discharge = adj_conveyors[1] # [AJ]: conveyor after the machine

            machine_state = getattr(eval('self.' + machine), 'state')

            if machine_state == "down" or machine_state == "startup":
                continue

            if 'source' not in infeed and 'sink' not in discharge: # [AJ]: if not the first machine and not the last machine in the line
                
                # [AJ]: get the level of last bin for infeed - conveyor before the machine
                level_infeed = getattr(getattr(self, infeed), "bin" +
                    str(self.num_conveyor_bins-self.infeedProx_index1))  
                # [AJ}: get the level of first bin for discharge - conveyor after the machine
                level_discharge = getattr(getattr(self, discharge), "bin" + str(self.dischargeProx_index1)) 
                
                if machine_state == "active" and level_infeed > self.infeed_prox_lower_limit and level_discharge < self.discharge_prox_lower_limit:
                   pass  
                elif machine_state == "active" and (level_infeed <= self.infeed_prox_lower_limit or level_discharge >= self.discharge_prox_lower_limit):
                    setattr(eval('self.' + machine), "state", "idle")
                    setattr(eval('self.' + machine), "speed", 0)           
                elif machine_state == "idle" and (level_infeed <= self.infeed_prox_lower_limit or level_discharge >= self.discharge_prox_lower_limit):
                    setattr(eval('self.' + machine), "state", "idle")
                    setattr(eval('self.' + machine), "speed", 0)                   
                elif machine_state == "idle" and level_infeed > self.infeed_prox_lower_limit and level_discharge < self.discharge_prox_lower_limit:
                    # set the machine state to startup and its speed to 0
                    setattr(eval('self.' + machine), "state", "startup")
                    setattr(eval('self.' + machine), "speed", 0) 

            elif 'source' in infeed: # [AJ]: if the first machine in the line

                # [AJ}: get the level of first bin for discharge - conveyor after the machine
                level_discharge = getattr(getattr(self, discharge), "bin" + str(self.dischargeProx_index1))
                
                if machine_state == "active" and level_discharge < self.discharge_prox_lower_limit:
                   pass
                elif machine_state == "active" and level_discharge >= self.discharge_prox_lower_limit:
                    setattr(eval('self.' + machine), "state", "idle")
                    setattr(eval('self.' + machine), "speed", 0)                
                elif machine_state == "idle" and level_discharge >= self.discharge_prox_lower_limit:
                    setattr(eval('self.' + machine), "state", "idle")
                    setattr(eval('self.' + machine), "speed", 0)                                     
                elif machine_state == "idle" and level_discharge < self.discharge_prox_lower_limit:
                    # set the machine state to startup and its speed to 0
                    setattr(eval('self.' + machine), "state", "startup")
                    setattr(eval('self.' + machine), "speed", 0) 

            elif 'sink' in discharge: # [AJ]: if the last machine in the line
                
                # [AJ]: get the level of last bin for infeed - conveyor before the machine
                level_infeed = getattr(getattr(self, infeed), "bin" +
                    str(self.num_conveyor_bins-self.infeedProx_index1))  
                
                if machine_state == "active" and level_infeed > self.infeed_prox_lower_limit:
                   pass 
                elif machine_state == "active" and level_infeed <= self.infeed_prox_lower_limit:
                    setattr(eval('self.' + machine), "state", "idle")
                    setattr(eval('self.' + machine), "speed", 0)                  
                elif machine_state == "idle" and level_infeed <= self.infeed_prox_lower_limit:
                    setattr(eval('self.' + machine), "state", "idle")
                    setattr(eval('self.' + machine), "speed", 0)                                   
                elif machine_state == "idle" and level_infeed > self.infeed_prox_lower_limit:
                    # set the machine state to startup and its speed to 0
                    setattr(eval('self.' + machine), "state", "startup")
                    setattr(eval('self.' + machine), "speed", 0) 
    
    def actual_machine_speeds(self):
        index = 0
        self.actual_speeds = {}
        # for machine in General.machines:
        for machine in adj.keys():   
            speed = getattr(eval('self.' + machine), 'speed') # [AJ]: brain choice of speed for the machine
            if 'source' not in adj[machine][0] and 'sink' not in adj[machine][1]: # [AJ]: if not the first machine and not the last machine in the line
                past_conveyor_level = self.all_conveyor_levels[index] # [AJ]: level of past conveyor
                next_conveyor_left_capacity = General.conveyor_capacity - self.all_conveyor_levels[index+1] # [AJ]: remaining empty space of next coveyor
                tmp = min(past_conveyor_level, next_conveyor_left_capacity)
                if speed == 0:
                    self.actual_speeds[machine] = 0
                elif speed <= tmp:
                    self.actual_speeds[machine] = speed
                elif speed > tmp:
                    self.actual_speeds[machine] = tmp
                setattr(eval('self.' + machine), 'speed', self.actual_speeds[machine])
                index += 1
            elif 'source' in adj[machine][0]: # [AJ]: if the first machine in the line
                if speed == 0:
                    self.actual_speeds[machine] = 0               
                else:
                    tmp1 = min(speed, General.conveyor_capacity - self.all_conveyor_levels[0])
                    self.actual_speeds[machine] = tmp1
                setattr(eval('self.' + machine), 'speed', self.actual_speeds[machine])
            elif 'sink' in adj[machine][1]: # [AJ]: if the last machine in the line
                if speed == 0:
                    self.actual_speeds[machine] = 0                    
                else:
                    tmp2 = min(speed, self.all_conveyor_levels[4])
                    self.actual_speeds[machine] = tmp2
                setattr(eval('self.' + machine), 'speed', self.actual_speeds[machine])
        return self.actual_speeds

    def check_illegal_actions(self):
        '''
        We will compare brain action (component action) with actual speed. If different then brain action was illegal.
        '''
        illegal_machine_actions = []

        for machine in General.machines:
            speed = getattr(eval('self.' + machine), 'speed')
            # [AJ]: components_speed contains the speeds that come from the brain           
            illegal_machine_actions.append(
                int(speed != self.components_speed[machine]))

        return illegal_machine_actions

    def reset(self, config):
        # self.episode_end = False
        # overwrite some parameters with that of config:
        General.simulation_time_step = \
            config["simulation_time_step"]        
        General.control_type = \
            config["control_type"]
        General.control_frequency = \
            config["control_frequency"]          
        General.interval_downtime_event_mean = \
            config["interval_downtime_event_mean"]
        General.interval_downtime_event_dev = \
            config["interval_downtime_event_dev"]
        General.downtime_event_duration_mean = \
            config["downtime_event_duration_mean"]
        General.downtime_event_duration_dev = \
            config["downtime_event_duration_dev"]
        General.number_parallel_downtime_events = \
            config["number_parallel_downtime_events"]
        General.idletime_duration = \
            config["idletime_duration"]
        General.layout_configuration = \
            config["layout_configuration"]
        General.down_machine_index = \
            config["down_machine_index"]
        General.initial_bin_level = \
            config["initial_bin_level"]
        General.bin_maximum_capacity = \
            config["bin_maximum_capacity"]               
        General.num_conveyor_bins = \
            config["num_conveyor_bins"]           
        General.conveyor_capacity = \
            config["conveyor_capacity"]
        General.machine0_min_speed = \
            config["machine0_min_speed"]
        General.machine1_min_speed = \
            config["machine1_min_speed"]
        General.machine2_min_speed = \
            config["machine2_min_speed"]
        General.machine3_min_speed = \
            config["machine3_min_speed"]
        General.machine4_min_speed = \
            config["machine4_min_speed"]
        General.machine5_min_speed = \
            config["machine5_min_speed"]
        General.machine_min_speed = [General.machine0_min_speed, General.machine1_min_speed, General.machine2_min_speed, 
        General.machine3_min_speed, General.machine4_min_speed, General.machine5_min_speed]
        General.machine0_max_speed = \
            config["machine0_max_speed"]
        General.machine1_max_speed = \
            config["machine1_max_speed"]            
        General.machine2_max_speed = \
            config["machine2_max_speed"]
        General.machine3_max_speed = \
            config["machine3_max_speed"]            
        General.machine4_max_speed = \
            config["machine4_max_speed"]
        General.machine5_max_speed = \
            config["machine5_max_speed"]  
        General.machine_max_speed = [General.machine0_max_speed, General.machine1_max_speed, General.machine2_max_speed, 
        General.machine3_max_speed, General.machine4_max_speed, General.machine5_max_speed]              
        General.machine0_initial_speed = \
            config["machine0_initial_speed"] 
        General.machine1_initial_speed = \
            config["machine1_initial_speed"] 
        General.machine2_initial_speed = \
            config["machine2_initial_speed"] 
        General.machine3_initial_speed = \
            config["machine3_initial_speed"] 
        General.machine4_initial_speed = \
            config["machine4_initial_speed"] 
        General.machine5_initial_speed = \
            config["machine5_initial_speed"] 
        General.machine_initial_speed = [General.machine0_initial_speed, General.machine1_initial_speed, General.machine2_initial_speed,
        General.machine3_initial_speed, General.machine4_initial_speed, General.machine5_initial_speed]
        General.infeed_prox_upper_limit = \
            config["infeed_prox_upper_limit"]
        General.infeed_prox_lower_limit = \
            config["infeed_prox_lower_limit"]        
        General.discharge_prox_upper_limit = \
            config["discharge_prox_upper_limit"]
        General.discharge_prox_lower_limit = \
            config["discharge_prox_lower_limit"]                        
        General.infeedProx_index1 = \
            config["infeedProx_index1"]
        General.infeedProx_index2 = \
            config["infeedProx_index2"]
        General.dischargeProx_index1 = \
            config["dischargeProx_index1"]
        General.dischargeProx_index2 = \
            config["dischargeProx_index2"]
        General.num_cans_at_discharge_index1 = \
            config["num_cans_at_discharge_index1"]
        General.num_cans_at_discharge_index2 = \
            config["num_cans_at_discharge_index2"]  
        General.num_cans_at_infeed_index1 = \
            config["num_cans_at_infeed_index1"]  
        General.num_cans_at_infeed_index2 = \
            config["num_cans_at_infeed_index2"]

        self._initialize_machines()
        self._initialize_sink()
        self._initialize_conveyor_buffers()
        self._initialize_downtime_tracker()

        self.processes_generator()

        self.get_conveyor_level()
        self.get_conveyor_level_estimate_initally() # [KN]: estimate initial conveyor levels
        self.downtime_estimator()
        self.accumulate_conveyor_bins()
        self.store_bin_levels()

    def step(self, brain_actions):

        self.iteration += 1
        
        # update the speed dictionary for those comming from the brain
        self.brain_speed = []
        for key in list(sorted(brain_actions.keys())):
            self.components_speed[key] = brain_actions[key]
            self.brain_speed.append(brain_actions[key])
        
        print('The component speeds are')
        print(self.components_speed)
        
        # # update line using self.component_speed
        # self.update_line() 

        # using brain actions
        self.update_machines_speed()

        print('Simulation time at step:', self.env.now)

        # step through the controllable event
        self.env.step()
        if self.control_type == 0 or self.control_type == -1:
            # control at fixed frequency. -1 for no-downtime event
            while self.is_control_frequency_event != 1:
                self.env.step()

        elif self.control_type == 1:
            # control when downtime events occur
            # Step through other events until a controllable event occurs.
            while self.is_control_downtime_event != 1:
                # step through events until a control event, such as downtime, occurs
                # Some events such as time laps are not control events and are excluded by the flag
                self.env.step()
        elif self.control_type == 2:
            while (self.is_control_frequency_event == 0 and self.is_control_downtime_event == 0):
                self.env.step()
        else:
            raise ValueError(f'unknown control type: {self.control_type}. \
                available modes: -1: fixed time no downtime, 0:fixed time, 1: downtime event, 2: both at fixed time and downtime event')

        # register the time of the controllable event: for use in calculation of delta-t.
        self.track_control_frequency()
        # track can accumulation in sinks once a new control event is triggered.
        self.track_sinks_throughput()

    def get_states(self):
        '''
        In this section, we will read the following:
        (1) Machine speed, an array indicating speed of all the machines
        (2) conveyor speed, an array indicating speed of all the conveyors
        (3) proxes, amount of can accumulations in each bin (Note: Not available in real world )
        (4) if proxes are full (two proxes before and two proxes after each machine is available in real world)
        (5) Throughput, i.e. the production rate from sink, i.e the speed of the last machine (will be used as reward)
        '''
        # 1
        machines_speed = []
        machines_state = []
        for machine in General.machines:
            machines_speed.append(getattr(eval('self.' + machine), 'speed'))
            state = getattr(eval('self.' + machine), 'state')
            # Bonsai platform can only handle numerical values
            # Assigning integer values to the states
            if state == 'active':
                machines_state.append(1)
            elif state == 'startup':
                machines_state.append(2)
            elif state == 'idle':
                machines_state.append(0)
            elif state == 'down':
                machines_state.append(-1)

        # 2
        conveyors_speed = []
        conveyors_state = []
        for conveyor in General.conveyors:
            # [AJ]: Used to double check the following since conveyors' speed must be constant
            # [AJ]: Machine speed and state should always remain the same
            conveyors_speed.append(getattr(eval('self.' + conveyor), 'speed'))
            conveyors_state.append(getattr(eval('self.' + conveyor), 'state'))

        # 3,4
        conveyor_buffers = []
        conveyor_buffers_full = []
        conveyor_buffers_previous = []

        # minus 1, minus2
        conveyor_infeed_m1_prox_empty = []
        conveyor_infeed_m2_prox_empty = []
        conveyor_previous_infeed_m1_prox_empty = []
        conveyor_previous_infeed_m2_prox_empty = []

        # plus 1, plus2
        conveyor_discharge_p1_prox_full = []
        conveyor_discharge_p2_prox_full = []
        conveyor_previous_discharge_p1_prox_full = []
        conveyor_previous_discharge_p2_prox_full = []

        for conveyor in General.conveyors:
            buffer = []
            buffer_previous = []
            buffer_full = []
            bin_capacity = getattr(getattr(self, conveyor), "bins_capacity")
            # [AJ]: For each bin, it checks whether the bin is full or not
            # [AJ]: Full refers to bin capacity (conveyor capacity / number of bins)
            for bin_num in range(0, self.num_conveyor_bins): # [AJ]: Added by Amir
                buffer.append(
                    getattr(getattr(self, conveyor), "bin" + str(bin_num)))
                buffer_previous.append(
                    getattr(getattr(self, conveyor), "previous_bin_level" + str(bin_num)))
                buffer_full.append(
                    int(getattr(getattr(self, conveyor), "bin" + str(bin_num)) == bin_capacity)) # [AJ]: Check whether each bin reaches bin capacity or not

            # [AJ]: The following is added by Amir
            # The infeed sensor next to machine
            current_infeed_m1_level = getattr(
                getattr(self, conveyor), "bin" + str(self.num_conveyor_bins-self.infeedProx_index1))
            if current_infeed_m1_level <= self.infeed_prox_lower_limit:
                conveyor_infeed_m1_prox_empty.append(1)
            else:
                conveyor_infeed_m1_prox_empty.append(0)

            # The second infeed sensor next to machine
            current_infeed_m2_level = getattr(
                getattr(self, conveyor), "bin" + str(self.num_conveyor_bins-self.infeedProx_index2))
            if current_infeed_m2_level <= self.infeed_prox_upper_limit:
                conveyor_infeed_m2_prox_empty.append(1)
            else:
                conveyor_infeed_m2_prox_empty.append(0)

            # [AJ]: The following is added by Amir
            current_discharge_p1_level = getattr(getattr(self, conveyor), "bin" + str(self.dischargeProx_index1))
            # The discharge sensor next to machine
            if current_discharge_p1_level >= self.discharge_prox_lower_limit:
                conveyor_discharge_p1_prox_full.append(1)
            else:
                conveyor_discharge_p1_prox_full.append(0)

            # The second discharge sensor next to machine 
            current_discharge_p2_level = getattr(getattr(self, conveyor), "bin" + str(self.dischargeProx_index2))
            if current_discharge_p2_level >= self.discharge_prox_upper_limit:
                conveyor_discharge_p2_prox_full.append(1)
            else:
                conveyor_discharge_p2_prox_full.append(0)

            conveyor_previous_infeed_m1_prox_empty.append(int(getattr(
                getattr(self, conveyor), "previous_bin_level" + str(self.num_conveyor_bins-self.infeedProx_index1))) <= self.infeed_prox_lower_limit)
            conveyor_previous_infeed_m2_prox_empty.append(int(getattr(
                getattr(self, conveyor), "previous_bin_level" + str(self.num_conveyor_bins-self.infeedProx_index2))) <= self.infeed_prox_upper_limit)                


            conveyor_previous_discharge_p1_prox_full.append(
                int(getattr(getattr(self, conveyor), "previous_bin_level" + str(self.dischargeProx_index1))) >= self.discharge_prox_lower_limit)
            # The second discharge sensor next to machine
            conveyor_previous_discharge_p2_prox_full.append(
                int(getattr(getattr(self, conveyor), "previous_bin_level" + str(self.dischargeProx_index2))) >= self.discharge_prox_upper_limit)            

            conveyor_buffers.append(buffer)
            conveyor_buffers_full.append(buffer_full)
            conveyor_buffers_previous.append(buffer_previous)

            conveyor_buffers_array = np.array(conveyor_buffers)
            conveyors_level = conveyor_buffers_array.sum(axis=1).tolist()

            conveyor_previous_buffers_array = np.array(conveyor_buffers_previous)
            conveyors_previous_level = conveyor_previous_buffers_array.sum(axis=1).tolist()           


        # throughput rate: 5
        # Most useful for fixed control frequency
        sink_machines_rate = []
        for machine in adj.keys():
            adj_conveyors = adj[machine]
            infeed = adj_conveyors[0]
            discharge = adj_conveyors[1]
            if 'sink' in discharge: # [AJ]: if the last machine in the line
                sink_machines_rate.append(
                    getattr(eval('self.' + machine), 'speed'))


        # sink inter-event product accumulation: 6

        # throughput change between control actions
        sinks_throughput_delta = []
        # absolute value of throughput
        sinks_throughput_abs = []

        for sink in General.sinks:
            s = eval('self.' + sink)
            delta = s.count_history[-1] - s.count_history[-2]
            sinks_throughput_delta.append(delta)
            # print('sinks_throughput_delta is', sinks_throughput_delta)
            sinks_throughput_abs.append(s.count_history[-1])
            # print('sinks_throughput_abs is', sinks_throughput_abs)

        self.sinks_throughput_abs = sum(sinks_throughput_abs)
        # print('self.sinks_throughput_abs is', self.sinks_throughput_abs)
        
        ## illegal actions: 7
        # [AJ]: Comment following since there is no illegal conveyor actions
        illegal_machine_actions = self.check_illegal_actions()

        control_delta_t = self.calculate_control_frequency_delta_time()
       
        states = {'machines_actual_speed': machines_speed, # actual speed used by the machine
                  'machines_state': machines_state,
                  'brain_speed': self.brain_speed, # brain choice of speed that can be over-written by the sim
                  'machines_state_sum': sum(machines_state),
                  'iteration_count': self.iteration,
                  'conveyors_speed': conveyors_speed,
                  'conveyors_state': conveyors_state,
                  'conveyor_buffers': conveyor_buffers,
                  'conveyor_buffers_full': conveyor_buffers_full,
                  'conveyors_level': conveyors_level,
                  'conveyors_previous_level': conveyors_previous_level,
                  'sink_machines_rate': sink_machines_rate,
                  'sink_machines_rate_sum': sum(sink_machines_rate),
                  'sink_throughput_delta': sinks_throughput_delta,
                  'sink_throughput_delta_sum': sum(sinks_throughput_delta),
                  'sink_throughput_absolute_sum': sum(sinks_throughput_abs),
                  'conveyor_infeed_m1_prox_empty': [int(val) for val in conveyor_infeed_m1_prox_empty],
                  'conveyor_infeed_m2_prox_empty': [int(val) for val in conveyor_infeed_m2_prox_empty],
                  'conveyor_discharge_p1_prox_full': [int(val) for val in conveyor_discharge_p1_prox_full],
                  'conveyor_discharge_p2_prox_full': [int(val) for val in conveyor_discharge_p2_prox_full],
                  'conveyor_previous_infeed_m1_prox_empty': [int(val) for val in conveyor_previous_infeed_m1_prox_empty],
                  'conveyor_previous_infeed_m2_prox_empty': [int(val) for val in conveyor_previous_infeed_m2_prox_empty],
                  'conveyor_previous_discharge_p1_prox_full': [int(val) for val in conveyor_previous_discharge_p1_prox_full],
                  'conveyor_previous_discharge_p2_prox_full': [int(val) for val in conveyor_previous_discharge_p2_prox_full],
                  'illegal_machine_actions': illegal_machine_actions,
                  'control_delta_t': control_delta_t,
                  'env_time': self.env.now,
                  'all_conveyor_levels': self.all_conveyor_levels,
                  'all_conveyor_levels_estimate': self.all_conveyor_levels_estimate,
                  'mean_downtime_offset': self.mean_downtime_offset,
                  'max_downtime_offset': self.max_downtime_offset
                  }

        print('Conveyor Estimate..............  ', self.all_conveyor_levels_estimate)

        return states

    def animation_concurrent_run(self):
        """
        Multi-threading for concurrent run of rendering
        Supported for the default config
        """
        print('Rendering ....')
        print('Please note that rendering is only functional for the default line config.')

        plt.style.use('fivethirtyeight')

        # {x, Y] position of the line elements in the plot.
        position = {'source1': (0, 0.02), 'm0': (5, 0.02), 'm1': (10, 0.02), 'con1': (12.5, 0.02), 'm2': (15, 0.02),
                    'm3': (20, 0.02), 'm4': (25, 0.02), 'con2': (27.5, 0.02), 'm5': (30, 0.02), 'sink': (35, 0.02),
                    'source2': (0, 0), 'm6': (5, 0), 'm7': (10, 0), 'con3': (12.5, 0), 'm8': (15, 0), 'm9': (20, 0)}

        # functions only for use inside rendering
        def line_plot():
            plt.figure(1, figsize=(300, 300))

            G = nx.Graph()
            G.add_edges_from([("source1", "m0"), ("m0", "m1"), ("m1", "con1"), ("con1", "con3"), ("con1", "m2"),
                              ("m2", "m3"), ("m3", "m4"), ("m4",
                                                           "con2"), ("con2", "m5"), ("m5", "sink"),
                              ("source2", "m6"), ("m6", "m7"), ("m7", "con3"), ("con3", "m8"), ("m8", "m9"), ("m9", "con2")])

            node_sizes = [7500, 7500, 7500, 4000, 4000, 7500, 7500,
                          7500, 4000, 7500, 7500, 7500, 7500, 7500, 7500, 7500]
            node_sizes = [node/10 for node in node_sizes]
            lock.acquire()
            for key, val in position.items():
                G.add_node(str(key), pos=val)
                if key == "con1" or key == "con2" or key == "con3"\
                        or key == "source1" or key == "source2":
                    continue
                elif key == "sink":
                    plt.text(val[0]-0.6, val[1] + 0.002,
                             'Throughput =' + str(self.sinks_throughput_abs), fontsize=8)
                else:
                    machine_speed = getattr(eval('self.' + key), 'speed')
                    plt.text(val[0]-0.6, val[1] + 0.002,
                             'Speed =' + str(machine_speed), fontsize=8)
            lock.release()
            nx.draw(G, nx.get_node_attributes(G, 'pos'),
                    with_labels=True, node_size=node_sizes, font_size=8)
            nx.draw_networkx_edge_labels(G, position, edge_labels={('m0', 'm1'): 'c0', ('m1', 'con1'): 'c1', ('con1', 'm2'): 'c1',
                                                                   ('con3', 'con1'): 'Load Balancing Conveyor',
                                                                   ('m2', 'm3'): 'c2', ('m3', 'm4'): 'c3', ('m4', 'con2'): 'c4',
                                                                   ('con2', 'm5'): 'c4', ('m6', 'm7'): 'c5', ('m7', 'con3'): 'c6',
                                                                   ('con3', 'm8'): 'c6', ('m8', 'm9'): 'c7',
                                                                   ('m9', 'con2'): 'Joining Conveyor'}, font_color='red',
                                         font_size=8)
            plt.tight_layout()

        def animate(i):
            plt.cla()
            plt.tight_layout()
            line_plot()

        ani = FuncAnimation(plt.gcf(), animate, interval=1000)
        print('Rendering...')
        plt.show()

    def render(self):
        p = threading.Thread(target=self.animation_concurrent_run)
        p.daemon = True
        p.start()


if __name__ == "__main__":
    env = simpy.Environment()
    my_env = DES(env)
    default_config = {
        "simulation_time_step": 1,
        "control_type": -1,
        "control_frequency": 1,
        "interval_downtime_event_mean": 100,
        "interval_downtime_event_dev": 20,
        "downtime_event_duration_mean": 4,
        "downtime_event_duration_dev": 2,
        "idletime_duration_mean": 6,
        "idletime_duration_dev": 4,
        "number_parallel_downtime_events": 1,
        "layout_configuration": 1,
        "down_machine_index": 2, 
        "initial_bin_level": 10,
        "bin_maximum_capacity": 100,
        "num_conveyor_bins": 10,
        "conveyor_capacity": 1000,
        "machine0_min_speed": 1,
        "machine1_min_speed": 2,
        "machine2_min_speed": 3,
        "machine3_min_speed": 4,
        "machine4_min_speed": 5,
        "machine5_min_speed": 6,
        "machine0_max_speed": 10,
        "machine1_max_speed": 20,
        "machine2_max_speed": 30,
        "machine3_max_speed": 40,
        "machine4_max_speed": 50,
        "machine5_max_speed": 60,
        "machine0_initial_speed": 1,
        "machine1_initial_speed": 2,
        "machine2_initial_speed": 3,
        "machine3_initial_speed": 4,
        "machine4_initial_speed": 5,
        "machine5_initial_speed": 6,
        "infeed_prox_upper_limit": 50,
        "infeed_prox_lower_limit": 50,
        "discharge_prox_upper_limit": 50,
        "discharge_prox_lower_limit": 50,
        "infeedProx_index1": 1,
        "infeedProx_index2": 4, 
        "dischargeProx_index1": 0, 
        "dischargeProx_index2": 3,
        "num_cans_at_discharge_index1": 950 , 
        "num_cans_at_discharge_index2": 650 ,
        "num_cans_at_infeed_index2": 350 ,  
        "num_cans_at_infeed_index2": 50 ,  
    }
    my_env.reset(default_config)
    my_env.render()
    # my_env.animation_concurrent_run()
    # rendering.join()
    # my_env.render()
    iteration = 0
    while True:
        my_env.step(brain_actions={'c0': 50, 'm0': 100, 'm1': 10})
        # input('Press Enter to continue ...')
        states = my_env.get_states()
        print(f'iteration is {iteration}')
        iteration += 1
        if iteration == 100000:
            my_env = DES(env)
            my_env.reset()
            time.sleep(5)
            iteration = 0
