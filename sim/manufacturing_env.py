#! /usr/bin/env python
"""Simulation for Manufacturing Line Optimization"""
__author__ = "Amir Jafari, Hossein Khadivi Heris"
__copyright__ = "Project Socrates, Professional Services"
__credits__ = ["Amir Jafari", "Hossein Khadivi Heris"]
__license__ = "Microsoft"
__version__ = "1.0.1"
__maintainer__ = "Amir Jafari"
__email__ = "amjafari@microsoft.com"
__status__ = "Development"

from textwrap import indent
from line_config import adj, adj_conv
import json
import os
import time
import re
import random
from collections import OrderedDict, deque
from typing import Dict, Any, Optional, ValuesView
import simpy
import numpy as np
import matplotlib  
matplotlib.use('TkAgg')   
import matplotlib.pyplot as plt  
from matplotlib.animation import FuncAnimation
import networkx as nx
from networkx.generators import line
import pandas as pd
import threading
from threading import Lock
import pdb
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
    machines, conveyors, sources, sinks = get_machines_conveyors_sources_sets(adj, adj_conv)
    number_of_machines = len(machines) # number of machines
    number_of_conveyors = len(conveyors) # number of conveyors
    machine_list = ["m" + str(i) for i in range(number_of_machines)]
    conveyor_list = ["c" + str(i) for i in range(number_of_conveyors)]
    conveyor_min_speed = 10
    conveyor_max_speed = 1000
    conveyor_general_speed = conveyor_max_speed  
    first_count = 0 # flag for occurance of first down event
    interval_first_down_event = 50 # time interval before the first down event
    # average time between random downtime events in seconds
    # random time interval between down events
    interval_downtime_event_mean = 20
    interval_downtime_event_dev = 5
    # duration of downtime event for each machine
    downtime_event_duration_mean = [11, 12, 6, 15, 9, 12, 6, 15, 12, 6, 10, 12]
    downtime_event_duration_dev = [2, 4, 1, 3, 3, 4, 3, 5, 2, 2, 4, 3]
    # machine down probability - likelihood of each machine going down
    downtime_prob = [70, 10, 5, 30, 60, 10, 15, 5, 20, 5, 65, 25]
    # distribution parameters of startup time
    idletime_duration_min = 5
    idletime_duration_max = 15
    idletime_duration = [6, 10, 5, 7, 12, 8, 11, 6, 15, 9, 10, 13]
    control_frequency = 1  # fixed control frequency duration in seconds
    # control type: -1: control at fixed time frequency with no downtime event 
    # control type: 0: control at fixed time frequency with downtime event
    # control type: 1: event driven, i.e. when a downtime occurs
    # control type: 2: both at fixed control frequency and when a downtime occurs
    control_type = 0
    number_parallel_downtime_events = 4
    layout_configuration = 1 # placeholder for different configurations of machines & lines
    simulation_time_step = 1 # granularity of simulation updates so larger values make simulation less accurate; recommended value is 1
    down_machine_index = -1 # -1 for random down machine and or 0 to K for specific machine out of K machines
    initial_bin_level = 60 # initial capacity of each bin (from 0 to 100)
    num_conveyor_bins = 10 # number of bins per conveyor
    bin_maximum_capacity = 100 # maximum capacity (in products) of each bin
    conveyor_capacity = bin_maximum_capacity * num_conveyor_bins  # in products
    machine_min_speed = [100, 30, 60, 40, 80, 80, 100, 30, 60, 40, 80, 80]
    machine_max_speed = [170, 190, 180, 180, 180, 300, 170, 190, 180, 180, 180, 300]
    # initial speed of the machines
    machine0_initial_speed = 110
    machine1_initial_speed = 50
    machine2_initial_speed = 70
    machine3_initial_speed = 70
    machine4_initial_speed = 100
    machine5_initial_speed = 120
    machine6_initial_speed = 110
    machine7_initial_speed = 50
    machine8_initial_speed = 70
    machine9_initial_speed = 70
    machine10_initial_speed = 100
    machine11_initial_speed = 120
    machine_initial_speed = [machine0_initial_speed, machine1_initial_speed, machine2_initial_speed, machine3_initial_speed,
     machine4_initial_speed, machine5_initial_speed, machine6_initial_speed, machine7_initial_speed, machine8_initial_speed,
     machine9_initial_speed, machine10_initial_speed, machine11_initial_speed]
    infeed_prox_upper_limit = 50 # threshold to turn on/off the infeed prox
    infeed_prox_lower_limit =  50 # threshold to turn on/off the infeed prox
    discharge_prox_upper_limit = 50 # threshold to turn on/off the discharge prox
    discharge_prox_lower_limit = 50 # threshold to turn on/off the discharge prox
    infeedProx_index1 = 1 # bin index for location of primary infeed sensor
    infeedProx_index2 = 4 # bin index for location of secondary infeed sensor
    dischargeProx_index1 = 0 # bin index for location of primary discharge sensor
    dischargeProx_index2 = 3 # bin index for location of secondary discharge sensor
    num_products_at_infeed_index1 = (infeedProx_index1 - 1) * bin_maximum_capacity + infeed_prox_lower_limit
    num_products_at_infeed_index2 = (infeedProx_index2 - 1) * bin_maximum_capacity + infeed_prox_upper_limit
    num_products_at_discharge_index1 = (num_conveyor_bins - dischargeProx_index1 - 1) * bin_maximum_capacity + discharge_prox_lower_limit
    num_products_at_discharge_index2 = (num_conveyor_bins - dischargeProx_index2 - 1) * bin_maximum_capacity + discharge_prox_upper_limit

class Machine(General):
    '''
    This class represents a General machine, i.e. its states and function
    '''
    def __init__(self, id, speed):
        super().__init__()      
        self.id = id
        self._speed = speed
        self._state = 'idle' if speed == 0 else 'active'
        self.idle_counter = General.simulation_time_step

    @property
    def speed(self):
        return self._speed

    @property
    def state(self):
        return self._state

    # explanation of states
    # idle: machine speed is 0 due to conveyor being overloaded/underloaded
    # down: machine speed is 0 due to jamming/hardware issue
    # startup: machine speed is 0 due to going through startup phase after recovering from idle mode
    # active: machine is running at a non-zero speed

    @speed.setter
    def speed(self, value):
        if not (value <= self.machine_max_speed[self.id] or value == 0):
            raise ValueError(f'speed must be 0 or smaller than {self.machine_max_speed[self.id]}')
        if self.state == "down":
            self._speed = 0
            # print('machine is down, machine speed will be kept zero')
        elif self.state == "idle":
            self._speed = 0
            # print('machine is idle, machine speed will be kept zero')
        elif self.state == "startup":
            self._speed = 0
            # print('machne is in startup, machine speed will be kept zero')     
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
        self.general_speed = General.conveyor_general_speed
        self._speed = speed
        self.id = id
        self._state = 'idle' if self._speed == 0 else 'active'
        self.bins_capacity = self.conveyor_capacity / self.num_conveyor_bins
        # each bin is considered a container and has a maximum capacity and initial level
        for i in range(0, self.num_conveyor_bins):
            setattr(self, "bin" + str(i), self.initial_bin_level) # current bin level
            setattr(self, "previous_bin_level" + str(i), 0) # previous bin level

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
        elif value == 0 and self.state != "down":
            self.state = "idle"
            self._speed = value
        elif value > 0:
            self._speed = value
            self.state = "active"

    @state.setter
    def state(self, state):
        if state not in ("idle", "active", "down"):
            raise ValueError(
                'state must be one of the following idle, active, down')
        self._state = state
        if state == 'down' or state == 'idle':
            self._speed = 0

    def __repr__(self):
        return (f'Conveyor with id of {self.id}\
            runs at speed of {self.speed} and is in {self.state} mode')


class Sink():
    def __init__(self, id):
        super().__init__()
        # count of product accumulation at the sink, where manufactured products are collected
        # assumption is an infinite capacity to store final products
        self.product_count = 0
        # a deque to track product accumulation between events
        self.count_history = deque([0, 0, 0], maxlen=10)

class DES(General):
    def __init__(self, env):
        super().__init__()
        self.env = env
        self.components_speed = {}
        self.actual_speeds = dict.fromkeys(General.machine_list, 0)
        self.brain_speed = [0] * General.number_of_machines
        self.iteration = 1
        self.all_conveyor_levels = [General.initial_bin_level * General.num_conveyor_bins] * General.number_of_conveyors
        self.all_conveyor_levels_estimate = [General.initial_bin_level * General.num_conveyor_bins] * General.number_of_conveyors
        self.down_cnt = [0] * General.number_of_machines
        self.machine_counter = [General.simulation_time_step] * General.number_of_machines
        self.mean_downtime_offset = [0] * General.number_of_machines
        self.max_downtime_offset = [0] * General.number_of_machines
        self._initialize_conveyor_buffers()
        self._initialize_machines()
        self._initialize_sink()
        self.episode_end = False
        # a flag to identify events that require control
        self.is_control_downtime_event = 0 # flag that a downtime event has occured
        self.is_control_frequency_event = 0 # flag that a fixed control frequency event has occured
        self.downtime_event_times_history = deque([0, 0, 0], maxlen=10)
        self.downtime_machine_history = deque([0, 0, 0], maxlen=10)
        self.control_frequency_history = deque([0, 0, 0], maxlen=10)
        self._initialize_downtime_tracker()
        self._check_simulation_step()
        self.sinks_throughput_abs = 0

    def _initialize_conveyor_buffers(self):
        '''
        start the conveyors with an initial running speed
        '''
        # there is no input buffer for machine 1, and assumption is that it is infinite
        # note that the number of conveyors are one less than total number of machines
        id = 0
        for conveyor in General.conveyor_list:
            # set the conveyor speed at the general conveyor speed which is the max speed
            setattr(self, conveyor,  Conveyor(id = id, speed = General.conveyor_general_speed, env = self.env))
            self.components_speed[conveyor] = General.conveyor_general_speed
            id += 1

    def _initialize_machines(self):
        '''
        start the machines with an initial running speed
        '''
        # create instance of each machine
        id = 0
        for machine in General.machine_list:
            setattr(self, machine,  Machine(
                id=id, speed=self.machine_initial_speed[id])) 
            self.components_speed[machine] = self.machine_initial_speed[id]
            id += 1

    def _initialize_sink(self):
        '''
        initialize the sink where the manufactured products are accumulated
        '''
        id = 0
        for sink in General.sinks:
            setattr(self, sink, Sink(id=id))
            id += 1

    def _initialize_downtime_tracker(self):
        '''
        initialize a dictionary to keep track of remaining downtime
        '''
        self.downtime_tracker_machines = {}
        self.downtime_tracker_conveyors = {}
        for machine in General.machine_list:
            self.downtime_tracker_machines[machine] = 0
        for conveyor in General.conveyor_list:
            self.downtime_tracker_conveyors[conveyor] = 0

    def _check_simulation_step(self):
        '''
        check the simulation step to ensure it is equal or smaller than control frequency
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
        '''
        generate processes for different control types
        '''
        print('Started product processing...')
        self.env.process(self.update_line_simulation_time_step())

        if self.control_type == -1:
            self.env.process(self.control_frequency_update())
        elif self.control_type == 0:
            self.env.process(self.control_frequency_update())
            for num_process in range(0, self.number_parallel_downtime_events):
                self.env.process(self.downtime_generator())
        elif self.control_type == 1:
            for num_process in range(0, self.number_parallel_downtime_events):
                self.env.process(self.downtime_generator())
        elif self.control_type == 2:
            self.env.process(self.control_frequency_update())
            for num_process in range(0, self.number_parallel_downtime_events):
                self.env.process(self.downtime_generator())
        else:
            raise ValueError(f"Only the following modes are currently available: \
                -1: fixed control frequency with no downtime event, \
                0: fixed control frequency with downtime event, \
                1: event driven with downtime event (1), \
                2: both fixed control frequency and event driven with downtime event")

    def control_frequency_update(self):
        '''
        update the control frequency
        '''
        while True:
            # define event type as control frequency event ahead of the event
            self.is_control_frequency_event = 1
            self.is_control_downtime_event = 0
            print(
                f'----control at {self.env.now} and event requires control: {self.is_control_frequency_event}')
            yield self.env.timeout(self.control_frequency) # informs the simulation to wait for the next control frequency event to occur
            self.is_control_frequency_event = 0
            # change the flag to zero, in case other events occur
            print('-------------------------------------------')
            print(f'control freq event at {self.env.now} s ...')

    def update_line_simulation_time_step(self):
        '''
        update product accumulation at fixed time interval, i.e General.simulation_time_step
        '''
        while True:
            self.is_control_frequency_event = 0
            self.is_control_downtime_event = 0
            # informs the simulation to wait for the next simulation time step
            yield self.env.timeout(self.simulation_time_step)
            print(f'----simulation update at {self.env.now}')
            self.update_line()

    def downtime_generator(self):
        '''
        generate downtime events based on parameters defined in General
        '''
        while True:
            if self.control_type != -1 and self.first_count == 0:
                yield self.env.timeout(self.interval_first_down_event) # informs the simulation to wait for this amount of time before first down event
                # change the flag to one once the first down event happens
                self.first_count = 1
            down_prob = General.downtime_prob.copy()
            machines_list = General.machine_list.copy()
            for ind, machine in enumerate(machines_list):
                machine_status = getattr(eval('self.' + machine), 'state')
                if machine_status == 'down':
                    machines_list.remove(machine)
                    down_prob.pop(ind)
            if machines_list == []:
                return None
            else:
                if self.down_machine_index == -1: # select a random machine to go down
                    down_machine_list = random.choices(machines_list, weights=down_prob, k=len(machines_list))
                    down_machine = max(set(down_machine_list), key = down_machine_list.count)
                else: # select a specific machine to go down
                    down_machine = machines_list[self.down_machine_index]
                print('down machine is', down_machine)
                self.down_machine_no = int(re.findall(r"[^\W\d_]+|\d+", down_machine)[-1])
                self.is_control_downtime_event = 1
                self.is_control_frequency_event = 0
                print(
                    f'----machine {down_machine} goes down at {self.env.now} and event requires control: {self.is_control_downtime_event}')
                setattr(eval('self.' + down_machine), "state", "down")
                setattr(eval('self.' + down_machine), "speed", 0)
                self.actual_speeds[down_machine] = 0
                # track current downtime event for the specific machine
                random_downtime_duration = random.randint(self.downtime_event_duration_mean[self.down_machine_no]-self.downtime_event_duration_dev[self.down_machine_no],
                                                            self.downtime_event_duration_mean[self.down_machine_no] + self.downtime_event_duration_dev[self.down_machine_no])  
                # random_downtime_duration = np.random.lognormal(self.downtime_event_duration_mean[self.down_machine_no], self.downtime_event_duration_dev[self.down_machine_no])                                                           
                print('down time duration is', random_downtime_duration)

                # only add control events to a deque
                self.track_event(down_machine, random_downtime_duration)
                yield self.env.timeout(random_downtime_duration) # informs the simulation that machine should go down for this amount of time
                
                setattr(eval('self.' + down_machine), "state", "active") # change the machine status to active mode to receive the new speed from Bonsai brain            
                setattr(eval('self.' + down_machine), "speed", self.components_speed[down_machine])
                self.actual_speeds[down_machine] = self.components_speed[down_machine]
  
                print('-----------------------------------------------------------------------')
                print(f'let machines run for a given period of time without any downtime event')
                self.is_control_downtime_event = 0
                self.is_control_frequency_event = 0
                interval_downtime_event_duration = random.randint(self.interval_downtime_event_mean - self.interval_downtime_event_dev,
                                                                self.interval_downtime_event_mean + self.interval_downtime_event_dev)
                yield self.env.timeout(interval_downtime_event_duration) # wait for this amount of time before next down event
       
    def startup_generator(self):
        '''
        generate startup time durations based on parameters defined in General
        '''
        for ind, machine in enumerate(General.machine_list):
            machine_state = getattr(eval('self.' + machine), "state")
            self.machine_counter[ind] = getattr(eval('self.' + machine), "idle_counter")
            machine_idletime_duration = self.idletime_duration[ind]

            if machine_state == "startup":
                if self.machine_counter[ind] >= machine_idletime_duration:
                    setattr(eval('self.' + machine), "state", "active")
                    setattr(eval('self.' + machine), "speed", self.components_speed[machine])     
                    self.machine_counter[ind] = General.simulation_time_step
                elif self.machine_counter[ind] < machine_idletime_duration:
                    self.machine_counter[ind] += General.simulation_time_step
                    setattr(eval('self.' + machine), "state", "startup")
                    setattr(eval('self.' + machine), "speed", 0)
                    setattr(eval('self.' + machine), "idle_counter", self.machine_counter[ind])  
                    self.actual_speeds[machine] = 0
            if machine_state != "startup":
                continue
    
    def downtime_estimator(self):
        '''
        estimate the down time duration for the machines that are down
        '''
        for ind, machine in enumerate(General.machine_list):
            max_downDuration = General.downtime_event_duration_mean[ind] + General.downtime_event_duration_dev[ind]
            mean_downDuration = General.downtime_event_duration_mean[ind]
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
    
    def update_line(self):
        '''
        update the status of the machines and conveyors of the line
        '''
        self.get_conveyor_level() # determine the number of products that exist on the conveyor
        self.startup_generator() # determine whether the machine has finished its startup phase or not
        self.actual_machine_speeds() # determine the actual speed of the machines based on covneyor levels
        self.accumulate_conveyor_bins() # accumulate the conveyors from right to left
        self.plc_control_machine_speed() # determine whether machines need to go into idle mode due to underloading/overloading of the conveyors
        # self.store_bin_levels()
        self.update_sinks_product_accumulation()
        # self.get_conveyor_level_estimate()
        self.downtime_estimator()

    def update_sinks_product_accumulation(self):
        '''
        accumulate product in the sink according to machine speed if the machine is connected to sink
        '''
        # update machine infeed and discharge buffers according to machine speed
        for machine in adj.keys():
            # adj is a dictionary where the machine is the key and before/after conveyors are the values
            # first value is used to refer to infeed and second value is used to refer to discharge
            adj_conveyors = adj[machine]
            infeed = adj_conveyors[0] # the conveyor before machine
            discharge = adj_conveyors[1] # the conveyor after the machine
            # amount of products going from one side to the other side
            delta = getattr(eval('self.' + machine), 'speed') * \
                self.simulation_time_step

            if 'sink' in discharge: # if last machine of the line
                level = getattr(getattr(self, discharge), "product_count")
                setattr(eval('self.' + discharge),
                        "product_count", level + delta)

    def track_event(self, down_machine, random_downtime_duration):
        '''
        add the current simulation time once called and then track the occurrence time of downtime events
        '''
        self.downtime_event_times_history.append(self.env.now)
        self.downtime_machine_history.append(
            (self.env.now, down_machine, random_downtime_duration))

    def track_control_frequency(self):
        '''
        track the control frequency
        '''
        self.control_frequency_history.append(self.env.now)

    def track_sinks_throughput(self):
        '''
        track the throuhgput at the sink
        '''
        for sink in General.sinks:
            level = getattr(getattr(self, sink), "product_count")
            s = eval('self.' + sink)
            s.count_history.append(level)

    def calculate_inter_event_delta_time(self):
        '''
        keep track of time lapsed between events.
        potential use: (1) calculate remaining downtime (2) reward normalization
        '''
        return self.downtime_event_times_history[-1] - self.downtime_event_times_history[-2]

    def calculate_control_frequency_delta_time(self):
        '''
        track time between brain controls following the config parameter that is set through Inkling
        '''
        return self.control_frequency_history[-1] - self.control_frequency_history[-2]

    def update_machines_speed(self):
        '''
        update the speed of the machine using brain actions that have been written in components_speed[machine] dictionary
        '''
        for machine in General.machine_list:
            updated_speed = self.components_speed[machine]
            setattr(eval('self.' + machine), 'speed', updated_speed)

    def get_conveyor_level(self):
        '''
        get the total number of products that exist in the conveyor at each iteration
        '''      
        self.all_conveyor_levels = []
        for conveyor in General.conveyor_list:
            conveyor_level = 0
            for bin_num in range(General.num_conveyor_bins-1, -1, -1):
                bin_level = getattr(getattr(self, conveyor), 
                                "bin" + str(bin_num))
                conveyor_level += bin_level # total number of products in the conveyor
            self.all_conveyor_levels.append(conveyor_level) # array that contains the total level of all conveyors

    def get_conveyor_level_estimate_initally(self):
        '''
        estimate the initial total number of products that exist on the conveyor
        '''    
        self.all_conveyor_levels_estimate = []
        for conveyor_level in self.all_conveyor_levels:
            if conveyor_level <= General.num_products_at_infeed_index1:
                conveyor_estimate_initial= round(General.num_products_at_infeed_index1/2)
                
            elif(conveyor_level > General.num_products_at_infeed_index1) and (conveyor_level < General.num_products_at_infeed_index2):
                conveyor_estimate_initial= round((General.num_products_at_infeed_index1 + General.num_products_at_infeed_index2)/2)

            elif(conveyor_level >= General.num_products_at_infeed_index2) and (conveyor_level < General.num_products_at_discharge_index2):
                conveyor_estimate_initial= round((General.num_products_at_infeed_index2 + General.num_products_at_discharge_index2)/2)

            elif(conveyor_level >= General.num_products_at_discharge_index2) and (conveyor_level < General.num_products_at_discharge_index1):
                conveyor_estimate_initial= round((General.num_products_at_discharge_index2 + General.num_products_at_discharge_index1)/2)

            else:
                conveyor_estimate_initial= round(General.num_products_at_discharge_index1/2)

            self.all_conveyor_levels_estimate.append(conveyor_estimate_initial)
     
    def get_conveyor_level_estimate(self):
        '''
        estimate the total number of products that exist on the conveyor at each iteration
        ''' 
        machines_speed = []
        for machine in General.machine_list:
            machines_speed.append(getattr(eval('self.' + machine), 'speed'))
        
        conveyor_infeed_m1_prox_empty = []
        conveyor_infeed_m2_prox_empty = []
        conveyor_previous_infeed_m1_prox_empty = []
        conveyor_previous_infeed_m2_prox_empty = []

        conveyor_discharge_p1_prox_full = []
        conveyor_discharge_p2_prox_full = []
        conveyor_previous_discharge_p1_prox_full = []
        conveyor_previous_discharge_p2_prox_full = []

        for conveyor in General.conveyor_list:
            # The primary infeed prox - current
            conveyor_infeed_m1_prox_empty.append(int(getattr(
                getattr(self, conveyor), "bin" + str(self.num_conveyor_bins-self.infeedProx_index1))) <= self.infeed_prox_lower_limit)
            # The secondanry infeed prox - current
            conveyor_infeed_m2_prox_empty.append(int(getattr(
                getattr(self, conveyor), "bin" + str(self.num_conveyor_bins-self.infeedProx_index2))) < self.infeed_prox_upper_limit)
            # The primary infeed prox -previous iteration
            conveyor_previous_infeed_m1_prox_empty.append(int(getattr(
                getattr(self, conveyor), "previous_bin_level" + str(self.num_conveyor_bins-self.infeedProx_index1))) <= self.infeed_prox_lower_limit)
            # The secondanry infeed prox - previous iteration
            conveyor_previous_infeed_m2_prox_empty.append(int(getattr(
                getattr(self, conveyor), "previous_bin_level" + str(self.num_conveyor_bins-self.infeedProx_index2))) < self.infeed_prox_upper_limit)                

            # The primary discharge prox - current
            conveyor_discharge_p1_prox_full.append(
                int(getattr(getattr(self, conveyor), "bin" + str(self.dischargeProx_index1))) >= self.discharge_prox_lower_limit)
            # The secondary discharge prox - current
            conveyor_discharge_p2_prox_full.append(
                int(getattr(getattr(self, conveyor), "bin" + str(self.dischargeProx_index2))) >= self.discharge_prox_upper_limit)    
            # The primary discharge prox - previous iteration
            conveyor_previous_discharge_p1_prox_full.append(
                int(getattr(getattr(self, conveyor), "previous_bin_level" + str(self.dischargeProx_index1))) >= self.discharge_prox_lower_limit)
            # The secondary discharge prox - previous iteration
            conveyor_previous_discharge_p2_prox_full.append(
                int(getattr(getattr(self, conveyor), "previous_bin_level" + str(self.dischargeProx_index2))) >= self.discharge_prox_upper_limit)            

        all_conveyor_levels_estimate_temp = []
        
        for i in range(len(self.all_conveyor_levels_estimate)):
            # predict phase of the estimator
            _estimate = self.all_conveyor_levels_estimate[i] + machines_speed[i] - machines_speed[i+1]

            # update phase of the estimator - assumption is measurements are true whenever available
            if conveyor_infeed_m1_prox_empty[i] != conveyor_previous_infeed_m1_prox_empty[i]:
                _estimate = General.num_products_at_infeed_index1
            elif conveyor_infeed_m2_prox_empty[i] != conveyor_previous_infeed_m2_prox_empty[i]:
                _estimate = General.num_products_at_infeed_index2
            elif conveyor_discharge_p1_prox_full[i] != conveyor_previous_discharge_p1_prox_full[i]:
                _estimate = General.num_products_at_discharge_index1
            elif conveyor_discharge_p2_prox_full[i] != conveyor_previous_discharge_p2_prox_full[i]:
                _estimate = General.num_products_at_discharge_index2

            all_conveyor_levels_estimate_temp.append(_estimate)

        self.all_conveyor_levels_estimate = all_conveyor_levels_estimate_temp.copy()

    def store_bin_levels(self):
        '''
        store the bin levels of the conveyors
        '''
        for conveyor in adj_conv.keys():        
            for bin_num in range(General.num_conveyor_bins-1, -1, -1):
                previous_bin_level = getattr(getattr(self, conveyor), 
                                "bin" + str(bin_num)) # get the level of the conveyor bin
                setattr(eval('self.' + conveyor), "previous_bin_level" +
                        str(bin_num), previous_bin_level) # set the previous level of the bin             
    
    def accumulate_conveyor_bins(self):
        '''
        accumulate the products in the conveyors from right to left
        '''
        index = 0
        for conveyor in General.conveyor_list:
            capacity = getattr(getattr(self, conveyor), "bins_capacity") # maximum capacity of each conveyor bin
            current_conveyor_level = self.all_conveyor_levels[index] # current conveyor level
            adj_machines = adj_conv[conveyor] # the machines corresponding to each conveyor
            previous_machine = adj_machines[0] # the machine before the conveyor
            next_machine = adj_machines[1] # the machine after the conveyor

            # amount of products processed by the machine before the conveyor - input to the conveyor
            delta_previous = getattr(eval('self.' + previous_machine), 'speed') * \
                self.simulation_time_step
            # amount of products processed by the machine after the conveyor - output from the conveyor
            delta_next = getattr(eval('self.' + next_machine), 'speed') * \
                self.simulation_time_step
            current_conveyor_level += (delta_previous - delta_next)
            current_conveyor_level = max(0, current_conveyor_level)

            for bin_num in range(General.num_conveyor_bins-1, -1, -1): # accumulate products in the conveyor from last bin (right) to first bin (left) 
                setattr(eval('self.' + conveyor), "bin" +
                        str(bin_num), 0) # reset the bin level - set the level of the bin to 0
                bin_level = min(current_conveyor_level, capacity)
                setattr(eval('self.' + conveyor), "bin" +
                        str(bin_num), bin_level) # set the bin level to right level
                new_bin_level = getattr(getattr(self, conveyor), 
                                "bin" + str(bin_num)) # get the level of the conveyor bin

                current_conveyor_level -= new_bin_level 
                if current_conveyor_level <= 0:
                    current_conveyor_level = 0
            index += 1
            current_conveyor_level = 0

    def plc_control_machine_speed(self):
        '''
        apply the following plac rules to adjust the speed and status of the machines
        rule1: machine should stop, i.e. speed = 0, if primary discharge prox exceeds a threshold
        rule2: machine should stop, i.e. speed = 0, if primary infeed prox falls below a threshold
        '''
        for machine in adj.keys():
            adj_conveyors = adj[machine]
            infeed = adj_conveyors[0] # conveyor before the machine
            discharge = adj_conveyors[1] # conveyor after the machine
            machine_state = getattr(eval('self.' + machine), 'state')
            if machine_state == "down" or machine_state == "startup":
                setattr(eval('self.' + machine), "speed", 0)   
                self.actual_speeds[machine] = 0  
                continue
            if 'source' not in infeed and 'sink' not in discharge: # if not the first machine and not the last machine in the line            
                # get the level of last bin for infeed - conveyor before the machine
                level_infeed = getattr(getattr(self, infeed), "bin" +
                    str(self.num_conveyor_bins-self.infeedProx_index1))  
                # get the level of first bin for discharge - conveyor after the machine
                level_discharge = getattr(getattr(self, discharge), "bin" + str(self.dischargeProx_index1)) 
                
                if machine_state == "active" and level_infeed > self.infeed_prox_lower_limit and level_discharge < self.discharge_prox_lower_limit:
                    setattr(eval('self.' + machine), "state", "active")
                    continue
                if machine_state == "active" and (level_infeed <= self.infeed_prox_lower_limit or level_discharge >= self.discharge_prox_lower_limit):
                    setattr(eval('self.' + machine), "state", "idle")
                    setattr(eval('self.' + machine), "speed", 0)     
                    continue
                if machine_state == "idle" and (level_infeed <= self.infeed_prox_lower_limit or level_discharge >= self.discharge_prox_lower_limit):
                    setattr(eval('self.' + machine), "state", "idle")
                    setattr(eval('self.' + machine), "speed", 0)   
                    continue
                if machine_state == "idle" and level_infeed > self.infeed_prox_lower_limit and level_discharge < self.discharge_prox_lower_limit:
                    # set the machine state to startup and its speed to 0
                    setattr(eval('self.' + machine), "state", "startup")
                    setattr(eval('self.' + machine), "speed", 0) 
                    continue
            if 'source' in infeed: # if the first machine in the line
                # get the level of first bin for discharge - conveyor after the machine
                level_discharge = getattr(getattr(self, discharge), "bin" + str(self.dischargeProx_index1))              
                if machine_state == "active" and level_discharge < self.discharge_prox_lower_limit:
                    setattr(eval('self.' + machine), "state", "active")
                    continue
                if machine_state == "active" and level_discharge >= self.discharge_prox_lower_limit:
                    setattr(eval('self.' + machine), "state", "idle")
                    setattr(eval('self.' + machine), "speed", 0)  
                    continue  
                if machine_state == "idle" and level_discharge >= self.discharge_prox_lower_limit:
                    setattr(eval('self.' + machine), "state", "idle")
                    setattr(eval('self.' + machine), "speed", 0)   
                    continue
                if machine_state == "idle" and level_discharge < self.discharge_prox_lower_limit:
                    # set the machine state to startup and its speed to 0
                    setattr(eval('self.' + machine), "state", "startup")
                    setattr(eval('self.' + machine), "speed", 0) 
                    continue
            if 'sink' in discharge: # if the last machine in the line             
                # get the level of last bin for infeed - conveyor before the machine
                level_infeed = getattr(getattr(self, infeed), "bin" +
                    str(self.num_conveyor_bins-self.infeedProx_index1))             
                if machine_state == "active" and level_infeed > self.infeed_prox_lower_limit:
                    setattr(eval('self.' + machine), "state", "active")
                    continue
                if machine_state == "active" and level_infeed <= self.infeed_prox_lower_limit:
                    setattr(eval('self.' + machine), "state", "idle")
                    setattr(eval('self.' + machine), "speed", 0) 
                    continue
                if machine_state == "idle" and level_infeed <= self.infeed_prox_lower_limit:
                    setattr(eval('self.' + machine), "state", "idle")
                    setattr(eval('self.' + machine), "speed", 0)  
                    continue
                if machine_state == "idle" and level_infeed > self.infeed_prox_lower_limit:
                    # set the machine state to startup and its speed to 0
                    setattr(eval('self.' + machine), "state", "startup")
                    setattr(eval('self.' + machine), "speed", 0) 
                    continue
    
    def actual_machine_speeds(self):
        '''
        determine the actual speed of the machines based on product availability and conveyor remaining empty capacity
        '''
        index = 0
        for machine in General.machine_list: 
            machine_state = getattr(eval('self.' + machine), "state") # state of the machine
            speed = self.components_speed[machine] # brain choice of speed for machine
            if 'source' not in adj[machine][0] and 'sink' not in adj[machine][1]: # if not the first machine and not the last machine in the line
                past_conveyor_level = self.all_conveyor_levels[index] # level of previous conveyor
                next_conveyor_left_capacity = General.conveyor_capacity - self.all_conveyor_levels[index+1] # remaining empty space of next coveyor
                tmp = min(past_conveyor_level, next_conveyor_left_capacity)
                if machine_state == "down" or machine_state == "idle" or machine_state == "startup": # machine is down, idle, or in startup mode
                    self.actual_speeds[machine] = 0
                    setattr(eval('self.' + machine), 'speed', self.actual_speeds[machine])
                    index += 1
                    continue
                if (machine_state != "down" or machine_state != "idle" or machine_state != "startup") and speed <= tmp:
                    self.actual_speeds[machine] = speed
                    setattr(eval('self.' + machine), 'speed', self.actual_speeds[machine])
                    index += 1
                    continue                    
                if (machine_state != "down" or machine_state != "idle" or machine_state != "startup") and speed > tmp:
                    self.actual_speeds[machine] = tmp
                    setattr(eval('self.' + machine), 'speed', self.actual_speeds[machine])
                    index += 1
                    continue
            elif 'source' in adj[machine][0]: # if the first machine in the line
                if machine_state == "down" or machine_state == "idle" or machine_state == "startup": # machine is down, idle, or in startup mode
                    self.actual_speeds[machine] = 0 
                    setattr(eval('self.' + machine), 'speed', self.actual_speeds[machine])
                    continue              
                if machine_state != "down" or machine_state != "idle" or machine_state != "startup":
                    tmp1 = min(speed, General.conveyor_capacity - self.all_conveyor_levels[0])
                    self.actual_speeds[machine] = tmp1
                    setattr(eval('self.' + machine), 'speed', self.actual_speeds[machine])
                    continue
            elif 'sink' in adj[machine][1]: # if the last machine in the line
                if machine_state == "down" or machine_state == "idle" or machine_state == "startup": # machine is down, idle, or in startup mode
                    self.actual_speeds[machine] = 0 
                    setattr(eval('self.' + machine), 'speed', self.actual_speeds[machine])
                    continue                   
                if machine_state != "down" or machine_state != "idle" or machine_state != "startup":
                    tmp2 = min(speed, self.all_conveyor_levels[-1])
                    self.actual_speeds[machine] = tmp2
                    setattr(eval('self.' + machine), 'speed', self.actual_speeds[machine])
                    continue
        return self.actual_speeds

    def check_illegal_actions(self):
        '''
        compare the brain action (component action) with actual machine speed and consider it illegal if they are not identical
        '''
        illegal_machine_actions = []

        for machine in General.machine_list:
            speed = getattr(eval('self.' + machine), 'speed')
            illegal_machine_actions.append(
                int(speed != self.components_speed[machine]))

        return illegal_machine_actions

    def reset(self, config):
        '''
        reset the configuration parameters
        '''
        # self.episode_end = False
        # overwrite some parameters with that of config
        General.simulation_time_step = \
            config["simulation_time_step"]        
        General.control_type = \
            config["control_type"]
        General.control_frequency = \
            config["control_frequency"]  
        General.interval_first_down_event = \
            config["interval_first_down_event"]        
        General.interval_downtime_event_mean = \
            config["interval_downtime_event_mean"]
        General.interval_downtime_event_dev = \
            config["interval_downtime_event_dev"]
        General.number_parallel_downtime_events = \
            config["number_parallel_downtime_events"]
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
        General.machine6_initial_speed = \
            config["machine6_initial_speed"] 
        General.machine7_initial_speed = \
            config["machine7_initial_speed"] 
        General.machine8_initial_speed = \
            config["machine8_initial_speed"] 
        General.machine9_initial_speed = \
            config["machine9_initial_speed"] 
        General.machine10_initial_speed = \
            config["machine10_initial_speed"] 
        General.machine11_initial_speed = \
            config["machine11_initial_speed"] 
        General.machine_initial_speed = [General.machine0_initial_speed, General.machine1_initial_speed, General.machine2_initial_speed,
        General.machine3_initial_speed, General.machine4_initial_speed, General.machine5_initial_speed, General.machine6_initial_speed,
        General.machine7_initial_speed, General.machine8_initial_speed, General.machine9_initial_speed, General.machine10_initial_speed, General.machine11_initial_speed]
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
        General.num_products_at_discharge_index1 = \
            config["num_products_at_discharge_index1"]
        General.num_products_at_discharge_index2 = \
            config["num_products_at_discharge_index2"]  
        General.num_products_at_infeed_index1 = \
            config["num_products_at_infeed_index1"]  
        General.num_products_at_infeed_index2 = \
            config["num_products_at_infeed_index2"]

        self._initialize_machines()
        self._initialize_sink()
        self._initialize_conveyor_buffers()
        self._initialize_downtime_tracker()

        self.processes_generator()
        self.get_conveyor_level() # determine the level of conveyors - prior to applying machines' speeds
        # self.startup_generator() # determine whether the machine have finished being in startup mode or not
        # self.get_conveyor_level_estimate_initally()
        self.actual_machine_speeds() # determine the actual machines' speeds based on conveyor levels
        self.accumulate_conveyor_bins() # update the conveyors level and acccumulate the conveyor bins - after applying actual machines' speeds
        self.plc_control_machine_speed() # determine whether machines need to go to idle mode
        # self.store_bin_levels()
        self.downtime_estimator()

    def step(self, brain_actions):
        '''
        run through the simulator at each brain iteration step
        '''
        self.iteration += 1
        # update the speed dictionary for those comming from the brain
        self.brain_speed = []
        for key in General.machine_list:
            self.components_speed[key] = brain_actions.get(key, 0)
            self.brain_speed.append(brain_actions.get(key, 0))
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
            # step through other events until a controllable event occurs.
            while self.is_control_downtime_event != 1:
                # step through events until a control event, such as downtime, occurs
                # some events such as time laps are not control events and are excluded by the flag
                self.env.step()
        elif self.control_type == 2:
            while (self.is_control_frequency_event == 0 and self.is_control_downtime_event == 0):
                self.env.step()
        else:
            raise ValueError(f'unknown control type: {self.control_type}. \
                available modes: -1: fixed time no downtime, 0:fixed time, 1: downtime event, 2: both at fixed time and downtime event')

        # register the time of the controllable event: for use in calculation of delta-t.
        self.track_control_frequency()
        # track product accumulation in sinks once a new control event is triggered.
        self.track_sinks_throughput()

    def get_states(self):
        '''
        get the states from the simulator that will be sent to the Bonsai platform
        (1) machine speed, an array indicating speed of all the machines
        (2) conveyor speed, an array indicating speed of all the conveyors
        (3) proxes, amount of product accumulations in each bin (Note: Not available in real world)
        (4) status of proxes
        (5) throughput, i.e. the production rate from sink, i.e the speed of the last machine (will be used as reward)
        '''
        # machine speed and state
        machines_state = []
        machines_speed = []
        for machine in General.machine_list:
            machines_speed.append(self.actual_speeds[machine])
            state = getattr(eval('self.' + machine), 'state')
            # Bonsai platform can only handle numerical values
            # assigning integer values to the states
            if state == "active":
                machines_state.append(1)
            elif state == "startup":
                machines_state.append(2)
            elif state == "idle":
                machines_state.append(0)
            elif state == "down":
                machines_state.append(-1)

        # conveyor speed and state
        conveyors_speed = []
        conveyors_state = []
        for conveyor in General.conveyors:
            conveyors_speed.append(getattr(eval('self.' + conveyor), 'speed'))
            conveyors_state.append(getattr(eval('self.' + conveyor), 'state'))

        # conveyor level status
        conveyor_buffers = []
        conveyor_buffers_full = []
        conveyor_buffers_previous = []

        # primary/secondary infeed prox status
        conveyor_infeed_m1_prox_empty = []
        conveyor_infeed_m2_prox_empty = []
        conveyor_previous_infeed_m1_prox_empty = []
        conveyor_previous_infeed_m2_prox_empty = []

        # primary/secondary discharge prox status
        conveyor_discharge_p1_prox_full = []
        conveyor_discharge_p2_prox_full = []
        conveyor_previous_discharge_p1_prox_full = []
        conveyor_previous_discharge_p2_prox_full = []

        for conveyor in General.conveyor_list:
            buffer = []
            buffer_previous = []
            buffer_full = []
            bin_capacity = getattr(getattr(self, conveyor), "bins_capacity")
            # for each bin in the conveyor, check whether the bin is full or not - full refers to bin maximum capacity
            for bin_num in range(0, self.num_conveyor_bins):
                # current level of the bin
                buffer.append(
                    getattr(getattr(self, conveyor), "bin" + str(bin_num)))
                # previous level of the bin
                buffer_previous.append(
                    getattr(getattr(self, conveyor), "previous_bin_level" + str(bin_num)))
                buffer_full.append(
                    int(getattr(getattr(self, conveyor), "bin" + str(bin_num)) == bin_capacity))

            # the primary infeed prox status for current iteration
            current_infeed_m1_level = getattr(
                getattr(self, conveyor), "bin" + str(self.num_conveyor_bins-self.infeedProx_index1))
            if current_infeed_m1_level <= self.infeed_prox_lower_limit:
                conveyor_infeed_m1_prox_empty.append(1)
            else:
                conveyor_infeed_m1_prox_empty.append(0)

            # the secondary infeed prox status for current iteration
            current_infeed_m2_level = getattr(
                getattr(self, conveyor), "bin" + str(self.num_conveyor_bins-self.infeedProx_index2))
            if current_infeed_m2_level <= self.infeed_prox_upper_limit:
                conveyor_infeed_m2_prox_empty.append(1)
            else:
                conveyor_infeed_m2_prox_empty.append(0)

            # the primary discharge prox status for current iteration
            current_discharge_p1_level = getattr(getattr(self, conveyor), "bin" + str(self.dischargeProx_index1))
            if current_discharge_p1_level >= self.discharge_prox_lower_limit:
                conveyor_discharge_p1_prox_full.append(1)
            else:
                conveyor_discharge_p1_prox_full.append(0)

            # the secondary discharge prox status for current iteration
            current_discharge_p2_level = getattr(getattr(self, conveyor), "bin" + str(self.dischargeProx_index2))
            if current_discharge_p2_level >= self.discharge_prox_upper_limit:
                conveyor_discharge_p2_prox_full.append(1)
            else:
                conveyor_discharge_p2_prox_full.append(0)

            # primary/secondary infeed prox status for previous iteration
            conveyor_previous_infeed_m1_prox_empty.append(int(getattr(
                getattr(self, conveyor), "previous_bin_level" + str(self.num_conveyor_bins-self.infeedProx_index1))) <= self.infeed_prox_lower_limit)
            conveyor_previous_infeed_m2_prox_empty.append(int(getattr(
                getattr(self, conveyor), "previous_bin_level" + str(self.num_conveyor_bins-self.infeedProx_index2))) <= self.infeed_prox_upper_limit)                

            # primary/secondary discharge proxstatus for previous iteration
            conveyor_previous_discharge_p1_prox_full.append(
                int(getattr(getattr(self, conveyor), "previous_bin_level" + str(self.dischargeProx_index1))) >= self.discharge_prox_lower_limit)
            conveyor_previous_discharge_p2_prox_full.append(
                int(getattr(getattr(self, conveyor), "previous_bin_level" + str(self.dischargeProx_index2))) >= self.discharge_prox_upper_limit)            

            conveyor_buffers.append(buffer)
            conveyor_buffers_full.append(buffer_full)
            conveyor_buffers_previous.append(buffer_previous)

            conveyor_buffers_array = np.array(conveyor_buffers)
            conveyors_level = conveyor_buffers_array.sum(axis=1).tolist()

            conveyor_previous_buffers_array = np.array(conveyor_buffers_previous)
            conveyors_previous_level = conveyor_previous_buffers_array.sum(axis=1).tolist()           

        # throughput rate which is most useful for fixed control frequency
        sink_machines_rate = []
        for machine in adj.keys():
            adj_conveyors = adj[machine]
            infeed = adj_conveyors[0]
            discharge = adj_conveyors[1]
            if 'sink' in discharge: # if it is the last machine in the line
                sink_machines_rate.append(
                    getattr(eval('self.' + machine), 'speed'))

        # sink inter-event product accumulation - throughput change between control actions
        sinks_throughput_delta = []
        # absolute value of throughput
        sinks_throughput_abs = []

        for sink in General.sinks:
            s = eval('self.' + sink)
            delta = s.count_history[-1] - s.count_history[-2]
            sinks_throughput_delta.append(delta)
            sinks_throughput_abs.append(s.count_history[-1])

        self.sinks_throughput_abs = sum(sinks_throughput_abs)
        
        # illegal actions
        illegal_machine_actions = self.check_illegal_actions()

        control_delta_t = self.calculate_control_frequency_delta_time()
       
        states = {'machines_state': machines_state,
                  'machines_actual_speed': machines_speed, # actual speed used by the machines
                  'brain_speed': self.brain_speed, # brain choice of speed that can be over-written by the simulator
                  'iteration_count': self.iteration,
                  'conveyors_speed': conveyors_speed,
                  'conveyors_state': conveyors_state,
                  'conveyor_buffers': conveyor_buffers,
                  'conveyor_buffers_full': conveyor_buffers_full,
                  'conveyors_level': conveyors_level,
                  'conveyor_infeed_m1_prox_empty': [int(val) for val in conveyor_infeed_m1_prox_empty],
                  'conveyor_infeed_m2_prox_empty': [int(val) for val in conveyor_infeed_m2_prox_empty],
                  'conveyor_discharge_p1_prox_full': [int(val) for val in conveyor_discharge_p1_prox_full],
                  'conveyor_discharge_p2_prox_full': [int(val) for val in conveyor_discharge_p2_prox_full],
                  'illegal_machine_actions': illegal_machine_actions,
                  'sink_machines_rate': sink_machines_rate,
                  'sink_machines_rate_sum': sum(sink_machines_rate),
                  'sink_throughput_delta': sinks_throughput_delta,
                  'sink_throughput_delta_sum': sum(sinks_throughput_delta),
                  'sink_throughput_absolute_sum': sum(sinks_throughput_abs),
                  'control_delta_t': control_delta_t,
                  'env_time': self.env.now,
                  'all_conveyor_levels': self.all_conveyor_levels,
                  'mean_downtime_offset': self.mean_downtime_offset,
                  'max_downtime_offset': self.max_downtime_offset
                #   'all_conveyor_levels_estimate': self.all_conveyor_levels_estimate,
                #   'conveyors_previous_level': conveyors_previous_level,
                #   'conveyor_previous_infeed_m1_prox_empty': [int(val) for val in conveyor_previous_infeed_m1_prox_empty],
                #   'conveyor_previous_infeed_m2_prox_empty': [int(val) for val in conveyor_previous_infeed_m2_prox_empty],
                #   'conveyor_previous_discharge_p1_prox_full': [int(val) for val in conveyor_previous_discharge_p1_prox_full],
                #   'conveyor_previous_discharge_p2_prox_full': [int(val) for val in conveyor_previous_discharge_p2_prox_full],
                  }

        return states

    def animation_concurrent_run(self):
        """
        Multi-threading for concurrent run of rendering
        supported for the default config
        """
        print('Rendering ....')
        print('Please note that rendering is only functional for the default line config.')

        plt.style.use('fivethirtyeight')

        # [x,y] position of the line elements in the plot.
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
        "interval_first_down_event": 30,
        "interval_downtime_event_mean": 100,
        "interval_downtime_event_dev": 20,
        "number_parallel_downtime_events": 1,
        "layout_configuration": 1,
        "down_machine_index": 2, 
        "initial_bin_level": 10,
        "bin_maximum_capacity": 100,
        "num_conveyor_bins": 10,
        "conveyor_capacity": 1000,
        "machine0_initial_speed": 1,
        "machine1_initial_speed": 2,
        "machine2_initial_speed": 3,
        "machine3_initial_speed": 4,
        "machine4_initial_speed": 5,
        "machine5_initial_speed": 6,
        "machine6_initial_speed": 1,
        "machine7_initial_speed": 2,
        "machine8_initial_speed": 3,
        "machine9_initial_speed": 4,
        "machine10_initial_speed": 5,
        "machine11_initial_speed": 6,
        "infeed_prox_upper_limit": 50,
        "infeed_prox_lower_limit": 50,
        "discharge_prox_upper_limit": 50,
        "discharge_prox_lower_limit": 50,
        "infeedProx_index1": 1,
        "infeedProx_index2": 4, 
        "dischargeProx_index1": 0, 
        "dischargeProx_index2": 3,
        "num_products_at_discharge_index1": 950 , 
        "num_products_at_discharge_index2": 650 ,
        "num_products_at_infeed_index1": 350 ,  
        "num_products_at_infeed_index2": 50 ,  
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
