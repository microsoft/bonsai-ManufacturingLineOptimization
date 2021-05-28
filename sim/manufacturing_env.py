from .line_config import adj, con_balance, con_join
# from .line_config import adj # [AJ]: For single line
import json
import os
import time
import random
from collections import OrderedDict, deque
from typing import Dict, Any, Optional
import simpy
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.animation import FuncAnimation
import networkx as nx
from networkx.generators import line
import pandas as pd
import threading
from threading import Lock
# from queue import Queue
lock = Lock()

'''
Simulation environment for multi machine manufacturing line.
'''

random.seed(10)


def get_machines_conveyors_sources_sets(adj):
    adj = OrderedDict(sorted(adj.items()))
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
        adj)
    number_of_machines = len(machines)   # number of General machines
    number_of_conveyors = len(conveyors)
    machine_infeed_buffer = 100 # [AJ]: Number of cans that can be in the infeed buffer
    machine_discharge_buffer = 100 # [AJ]: Number of cans that can be in the discharge buffer
    conveyor_capacity = 1000  # in cans # [AJ]: Number of cans that the conveyor can carry
    # every conveyor is divided into 10 sections. For approximate and connection purpose
    num_conveyor_bins = 10
    machine_min_speed = 10  # cans/second
    machine_max_speed = 100  # cans/second
    conveyor_min_speed = 10
    conveyor_max_speed = 100
    # [AJ]: Added to set up the conveyor to always run at max speed
    conveyor_speed = conveyor_max_speed    
    # warmup_time = 100  # seconds(s)
    # downtime_event_prob = 0.1 # probability applied every "downtime-even_gen_mean" to create downtime on a random machine
    # seconds (s) average time between random downtime events
    interval_downtime_event_mean = 100
    # deviation, a random interval_downtime_event is generated in range [interval_downtime_event_mean - interval_downtime_event_dev, interval_downtime_event_mean + interval_downtime_event_dev]
    interval_downtime_event_dev = 20
    # seconds(s), mean duration of each downtime event
    downtime_event_duration_mean = 10
    # seconds(s), deviation from mean. [downtime_event_duration_mean - downtime_event_duration_std, downtime_event_duration_mean + downtime_event_duration_std]
    downtime_event_duration_dev = 3
    control_frequency = 1  # seconds (s), fixed control frequency duration
    # control type: -1: control at fixed time frequency but no downtime event 0: control at fixed time frequency
    # control type: 1: event driven, i.e. when a downtime occurs, 2: both at fixed control frequency and downtime
    control_type = 1
    number_parallel_downtime_events = 1
    # placeholder for different configurations of machines.
    layout_configuration = 1
    # granularity of simulation updates. Larger values make simulation less accurate. Recommended value: 1.
    simulation_time_step = 1
    # [AJ]: The following is added by Amir
    down_machine_index = -1 # [AJ]: From 0 to 9 to refer to the down machine, -1 for no downtime/random parallel downtime



class Machine(General):
    '''
    This class represents a General machine, i.e. its states and function

    '''

    def __init__(self, id, speed):
        super().__init__()
        self.min_speed = General.machine_min_speed
        self.max_speed = General.machine_max_speed
        self.id = id
        self._speed = speed
        self._state = 'idle' if speed == 0 else 'active'
        # keep track of the down time event times.

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

    def __repr__(self):
        return (f'Machine with id of {self.id} \
                runs at speed of {self.speed} and is in {self.state} mode')


class Conveyor(General):

    def __init__(self, id, speed, number_of_bins, env):
        super().__init__()
        self.min_speed = General.conveyor_min_speed
        self.max_speed = General.conveyor_max_speed
        # [AJ]: Adding general conveyor speed
        self.conv_speed = General.conveyor_speed
        self._speed = speed
        self.id = id
        self._state = 'idle' if self._speed == 0 else 'active'
        self.capcity = General.conveyor_capacity
        self.number_of_bins = General.num_conveyor_bins
        # self.number_of_bins*[bin_capacity]
        self.bins_capacity = self.capcity/self.number_of_bins
        # each bin is a container and has a capacity and initial value
        for i in range(0, self.number_of_bins):
            # setattr(self, "bin" + str(i), simpy.Container(env, init = self.bins_capacity/2,  capacity = self.bins_capacity))
            setattr(self, "bin" + str(i), self.bins_capacity/2)

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
        self._initialize_conveyor_buffers()
        self._initialize_machines()
        self._initialize_sink()
        self.episode_end = False
        # a flag to identify events that require control
        self.is_control_downtime_event = 0
        self.is_control_frequency_event = 0
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
            # [AJ]: Comment the following
            # setattr(self, conveyor,  Conveyor(id = id, speed = General.conveyor_min_speed, number_of_bins = General.num_conveyor_bins, env = self.env))
            # [AJ]: Set the conveyor speed at the general conveyor speed which is the max speed
            setattr(self, conveyor,  Conveyor(id = id, speed = General.conveyor_speed, number_of_bins = General.num_conveyor_bins, env = self.env))
            #print(getattr(self, conveyor))
            # [AJ]: Comment the following
            # self.components_speed[conveyor] = General.conveyor_min_speed
            # [AJ]: Set the component speed at the general conveyor speed which is the max speed
            self.components_speed[conveyor] = General.conveyor_speed

            id += 1

    def _initialize_machines(self):
        # create instance of each machine
        id = 0
        for machine in General.machines:
            setattr(self, machine,  Machine(
                id=id, speed=General.machine_min_speed))
            # print(getattr(self, machine))
            self.components_speed[machine] = General.machine_min_speed
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
        while True:
            # define event type as control frequency event a ahead of the event
            self.is_control_frequency_event = 1
            self.is_control_downtime_event = 0
            print(
                f'................ control at {self.env.now} and event requires control: {self.is_control_frequency_event}...')
            yield self.env.timeout(self.control_frequency)
            self.is_control_frequency_event = 0
            # change the flag to zero, in case other events occur.
            print('-------------------------------------------')
            print(f'control freq event at {self.env.now} s ...')

    def update_line_simulation_time_step(self):
        '''
        Updating can accumulation at fixed time interval, i.e General.simulation_time_step
        '''
        while True:
            self.is_control_frequency_event = 0
            self.is_control_downtime_event = 0
            yield self.env.timeout(self.simulation_time_step)
            print(f'----simulation update at {self.env.now}')
            self.update_line()

    def downtime_generator(self):
        '''
        Parameters used in General will be used to generate downtime events on a random machine.
        '''
        while True:
            # randomly pick a machine
            # [AJ]: Pick a machine randomly from the list of machines
            # [AJ]: The following is added by Amir
            machines_list = list(General.machines) # [AJ]: Added by Amir
            if self.down_machine_index == -1:
                self.random_down_machine = random.choice(list(General.machines))
            else:
                self.down_machine = machines_list[self.down_machine_index] # [AJ]: Added by Amir
                self.random_down_machine = self.down_machine # [AJ]: Added by Amir
            self.is_control_frequency_event = 0
            print(
                f'................ now machine {self.random_down_machine} goes down at {self.env.now} and event requires control: {self.is_control_downtime_event}...')
            setattr(eval('self.' + self.random_down_machine), 'state', 'down')
            # track current downtime event for the specific machine
            self.random_downtime_duration = random.randint(self.downtime_event_duration_mean-self.downtime_event_duration_dev,
                                                           self.downtime_event_duration_mean + self.downtime_event_duration_dev)
            # only add control events to a deque
            self.track_event()
            yield self.env.timeout(self.random_downtime_duration)
            setattr(eval('self.' + self.random_down_machine), 'state', 'idle')
            print(
                f'................ now machine {self.random_down_machine} is up at {self.env.now} and event requires control: {self.is_control_downtime_event}...')
            print(
                f'................ let machines run for a given period of time without any downtime event')
            self.is_control_downtime_event = 0
            self.is_control_frequency_event = 0
            interval_downtime_event_duration = random.randint(self.interval_downtime_event_mean - self.interval_downtime_event_dev,
                                                              self.interval_downtime_event_mean + self.interval_downtime_event_dev)
            yield self.env.timeout(interval_downtime_event_duration)

    def update_line(self):
        # now moved to step
        # # using brain actions
        # self.update_machines_speed()
        # # using brain actions
        # self.update_conveyors_speed()

        # enforcing PLC rules to prevent jamming. This may ignore brain actions if buffers are full.
        self.plc_control_machine_speed()
        self.update_machine_adjacent_buffers()
        self.update_conveyors_buffers()
        # [AJ]: Comment following to only consider single line without conveyor balancing load between two lines       
        self.update_conveyor_junctions()
        self.update_sinks_product_accumulation()

    def update_sinks_product_accumulation(self):
        '''
        For each machine, we will check if to is connected to sink, then accumulate product according to machine speed .
        '''
        # update machine infeed and discharge buffers according to machine speed
        for machine in adj.keys():
            adj_conveyors = adj[machine]
            infeed = adj_conveyors[0]
            discharge = adj_conveyors[1]
            # amount of cans going from one side to the other side
            delta = getattr(eval('self.' + machine), 'speed') * \
                self.simulation_time_step

            if 'sink' in discharge:
                # now check buffer full  ....................................TODO:
                level = getattr(getattr(self, discharge), "product_count")
                setattr(eval('self.' + discharge),
                        "product_count", level + delta)

    def track_event(self):
        '''
        Once called, will add current simulation time and also
        It will be used to track the occurrence time of downtime events
        '''
        self.downtime_event_times_history.append(self.env.now)
        self.downtime_machine_history.append(
            (self.env.now, self.random_down_machine, self.random_downtime_duration))

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

    # def update_conveyors_speed(self):
    #     '''
    #     update the speed of the conveyors using brain actions that has written in components_speed[machine] dictionary
    #     '''
    #     for conveyor in General.conveyors:
    #         # print(f'now at {self.env.now} s updating conveyor speed')
    #         updated_speed = self.components_speed[conveyor]
    #         setattr(eval('self.' + conveyor), 'speed', updated_speed)
    #         # print(eval('self.' + conveyor))

    def update_machine_adjacent_buffers(self):
        '''
        For each machine, we will look at the adj matrix and update number of cans in their buffers. If the buffer is full, we need to shut down the machine.
        '''
        # update machine infeed and discharge buffers according to machine speed
        for machine in adj.keys():
            adj_conveyors = adj[machine]
            infeed = adj_conveyors[0]
            discharge = adj_conveyors[1]
            # amount of cans going from one side to the other side
            delta = getattr(eval('self.' + machine), 'speed') * \
                self.simulation_time_step
            if 'source' not in infeed:

                level = getattr(getattr(self, infeed), "bin" +
                                str(General.num_conveyor_bins-1))
                level -= delta
                if level <= 0:
                    level = 0
                    # TODO: prox empty machine speed = 0
                setattr(eval('self.' + infeed), "bin" +
                        str(General.num_conveyor_bins-1), level)

            if 'sink' not in discharge:
                # now check buffer full  ....................................TODO:
                level = getattr(getattr(self, discharge), "bin" + str(0))
                capacity = getattr(getattr(self, discharge), "bins_capacity")

                level += delta

                if level >= capacity:
                    level = capacity
                    # TODO: trigger discharge prox full
                setattr(eval('self.' + discharge), "bin" + str(0), level)

    def update_conveyors_buffers(self):
        for conveyor in General.conveyors:
            for bin_num in range(1, General.num_conveyor_bins):
                delta2 = getattr(eval('self.' + conveyor),
                                 'speed') * self.simulation_time_step
                bin_level = getattr(getattr(self, conveyor),
                                    "bin" + str(bin_num))
                previous_bin_level = getattr(
                    getattr(self, conveyor), "bin" + str(bin_num - 1))

                # now take from previous bin and add to the next bin
                capacity = getattr(getattr(self, conveyor), "bins_capacity")

                # check if enough cans is available
                if previous_bin_level < delta2:
                    delta2 = previous_bin_level

                # check not to overflow the cans
                if bin_level + delta2 > capacity:
                    delta2 = capacity - bin_level

                # update the buffers
                bin_level += delta2
                previous_bin_level -= delta2
                setattr(eval('self.' + conveyor),
                        "bin" + str(bin_num), bin_level)
                setattr(eval('self.' + conveyor), "bin" +
                        str(bin_num - 1), previous_bin_level)

    # [AJ]: Comment since there is no conveyor balancing between two lines
    def update_conveyor_junctions(self):
        '''
        Rules for the junctions: mainly balancing the load between lines.
        If a junction bin gets full, it can push cans to the neighbor conveyor.
        '''
        for junction in con_balance:    # balancing load between two line
            conveyor1 = junction[0]
            conveyor2 = junction[1]
            join_bin = junction[2]
            bin_1_level = getattr(
                getattr(self, conveyor1), "bin" + str(join_bin))
            bin_1_capacity = getattr(getattr(self, conveyor1), "bins_capacity")

            bin_2_level = getattr(
                getattr(self, conveyor2), "bin" + str(join_bin))
            bin_2_capacity = getattr(getattr(self, conveyor2), "bins_capacity")

            if bin_1_level < bin_1_capacity and bin_2_level < bin_2_capacity:
                # don't do any thing if both conveyors are operating below the capacity
                pass
            elif bin_1_level == bin_1_capacity and bin_2_level < bin_2_capacity:
                # push cans from bin_1 to bin_2
                delta = min(getattr(eval('self.' + conveyor1), 'speed')
                            * self.simulation_time_step, bin_2_capacity-bin_2_level)
                setattr(eval('self.' + conveyor2), "bin" +
                        str(join_bin), delta + bin_2_level)
                setattr(eval('self.' + conveyor1), "bin" +
                        str(join_bin), bin_1_level - delta)

            elif bin_2_level == bin_2_capacity and bin_1_level < bin_1_capacity:
                # do the opposite
                delta = min(getattr(eval('self.' + conveyor2), 'speed')
                            * self.simulation_time_step, bin_1_capacity-bin_1_level)
                setattr(eval('self.' + conveyor1), "bin" +
                        str(join_bin), delta + bin_1_level)
                setattr(eval('self.' + conveyor2), "bin" +
                        str(join_bin), bin_2_level - delta)
            else:
                # bin_2.level == bin_2.capacity and bin_2.level == bin_2.capcity:
                # do nothing
                pass

        for junction in con_join:
            conveyor1 = junction[0]
            conveyor2 = junction[1]
            join_bin = junction[2]
            bin_1_level = getattr(getattr(self, conveyor1),
                                  "bin" + str(General.num_conveyor_bins-1))
            bin_1_capacity = getattr(getattr(self, conveyor1), "bins_capacity")

            bin_2_level = getattr(
                getattr(self, conveyor2), "bin" + str(join_bin))
            bin_2_capacity = getattr(getattr(self, conveyor2), "bins_capacity")
            if bin_2_level < bin_2_capacity:
                # always add from first one to the second one if there is room
                delta = min(getattr(eval('self.' + conveyor1), 'speed')
                            * self.simulation_time_step, bin_2_capacity-bin_2_level)

                setattr(eval('self.' + conveyor1), "bin" +
                        str(join_bin), bin_1_level - delta)
                setattr(eval('self.' + conveyor2), "bin" +
                        str(join_bin), bin_2_level + delta)
            else:
                pass

    def plc_control_machine_speed(self):
        '''
        rule1: machine should stop, i.e. speed = 0, if its discharge prox is full
        rule2: machine should stop, i.e. speed = 0, if its infeed prox is empty
        '''
        for machine in adj.keys():
            adj_conveyors = adj[machine]
            infeed = adj_conveyors[0]
            discharge = adj_conveyors[1]
            if 'source' not in infeed:
                level = getattr(getattr(self, infeed), "bin" +
                                str(General.num_conveyor_bins-1))
                if level == 0:
                    print(
                        f'stopping machine {machine} as infeed prox is empty, i.e the whole conveyor is empty')
                    setattr(eval('self.' + machine), "speed", 0)
                    print(eval('self.' + machine))

            if 'sink' not in discharge:
                level = getattr(getattr(self, discharge), "bin" + str(0))
                capacity = getattr(getattr(self, discharge), "bins_capacity")

                if level == capacity:
                    print(
                        f'stopping machine {machine} as discharge prox is full, i.e. the whole conveyor is full')
                    setattr(eval('self.' + machine), "speed", 0)
                    print(eval('self.' + machine))

    def check_illegal_actions(self):
        '''
        We will compare brain action (component action) with actual speed. If different then brain action was illegal.
        '''
        illegal_machine_actions = []
        # [AJ]: Comment the following as there is no illegal conveyor's actions
        # illegal_conveyor_actions = []

        for machine in General.machines:
            speed = getattr(eval('self.' + machine), 'speed')
            illegal_machine_actions.append(
                int(speed != self.components_speed[machine]))

        # [AJ]: Comment the following
        # [AJ]: Brain is not supposed to decide on conveyors' speeds
        # for conveyor in General.conveyors:
        #     speed = getattr(eval('self.' + conveyor),'speed')
        #     illegal_conveyor_actions.append(int(speed != self.components_speed[conveyor]))

        # [AJ]: Comment the following
        # return illegal_machine_actions, illegal_conveyor_actions
        return illegal_machine_actions

    def calculate_downtime_remaining_time(self):
        # first calculated the delta time elapsed since previous event
        delta_t = self.calculate_inter_event_delta_time()

        # update the machine and conveyor downtime tracker using the delta t
        for machine in General.machines:
            self.downtime_tracker_machines[machine] = max(
                self.downtime_tracker_machines[machine]-delta_t, 0)

        for conveyor in General.conveyors:
            self.downtime_tracker_conveyors[conveyor] = max(
                self.downtime_tracker_machines[machine]-delta_t, 0)

        # add/update the latest downtime event to the tracker
        # currently only machines downtime is considered.
        try:
            self.downtime_tracker_machines[self.random_down_machine] = self.random_downtime_duration
        except:
            print(
                'Could not update downtime_tracker_machines dict. Ok for iteration zero!')

        remaining_downtime_machines = []

        for machine in General.machines:
            remaining_downtime_machines.append(
                self.downtime_tracker_machines[machine])

        return remaining_downtime_machines, delta_t

    def reset(self):
        # self.episode_end = False
        self.processes_generator()

    def step(self, brain_actions):

        # update the speed dictionary for those comming from the brain
        for key in list(brain_actions.keys()):
            self.components_speed[key] = brain_actions[key]
        # # update line using self.component_speed
        # self.update_line()

        # using brain actions
        self.update_machines_speed()
        # [AJ]: Comment the following because brain is not supposed to determine coneyors speeds
        # using brain actions 
        # self.update_conveyors_speed()

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
            elif state == 'idle':
                machines_state.append(0)
            elif state == 'down':
                machines_state.append(-1)

        # 2
        conveyors_speed = []
        conveyors_state = []
        for conveyor in General.conveyors:
            # [AJ]: Used to double check the following since conveyors' speed must be constant
            conveyors_speed.append(getattr(eval('self.' + conveyor), 'speed'))
            conveyors_state.append(getattr(eval('self.' + conveyor), 'state'))

        # 3,4
        conveyor_buffers = []
        conveyor_buffers_full = []

        # minus 1, minus2
        conveyor_infeed_m1_prox_empty = []
        conveyor_infeed_m2_prox_empty = []

        # plus 1, plus2
        conveyor_discharge_p1_prox_full = []
        conveyor_discharge_p2_prox_full = []

        for conveyor in General.conveyors:
            buffer = []
            buffer_full = []
            bin_capacity = getattr(getattr(self, conveyor), "bins_capacity")
            for bin_num in range(0, General.num_conveyor_bins):
                buffer.append(
                    getattr(getattr(self, conveyor), "bin" + str(bin_num)))
                buffer_full.append(
                    int(getattr(getattr(self, conveyor), "bin" + str(bin_num)) == bin_capacity))

            conveyor_infeed_m1_prox_empty.append(int(getattr(
                getattr(self, conveyor), "bin" + str(General.num_conveyor_bins-1))) == 0)
            conveyor_infeed_m2_prox_empty.append(int(getattr(
                getattr(self, conveyor), "bin" + str(General.num_conveyor_bins-2))) == 0)

            conveyor_discharge_p1_prox_full.append(
                int(getattr(getattr(self, conveyor), "bin" + str(0))) == bin_capacity)
            conveyor_discharge_p2_prox_full.append(
                int(getattr(getattr(self, conveyor), "bin" + str(1))) == bin_capacity)

            conveyor_buffers.append(buffer)
            conveyor_buffers_full.append(buffer_full)

        # throughput rate: 5
        # Most useful for fixed control frequency
        sink_machines_rate = []
        for machine in adj.keys():
            adj_conveyors = adj[machine]
            infeed = adj_conveyors[0]
            discharge = adj_conveyors[1]
            if 'sink' in discharge:
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
            sinks_throughput_abs.append(s.count_history[-1])

        self.sinks_throughput_abs = sum(sinks_throughput_abs)
        
        ## illegal actions: 7
        # [AJ]: Comment following since there is no illegal conveyor actions
        # illegal_machine_actions, illegal_conveyor_actions = self.check_illegal_actions()
        illegal_machine_actions = self.check_illegal_actions()

        # downtime remaining time: 8
        remaining_downtime_machines, downtime_event_delta_t = self.calculate_downtime_remaining_time()

        control_delta_t = self.calculate_control_frequency_delta_time()

        states = {'machines_speed': machines_speed,
                  'machines_state': machines_state,
                  'machines_state_sum': sum(machines_state),
                  'conveyors_speed': conveyors_speed,
                  'conveyors_state': conveyors_state,
                  'conveyor_buffers': conveyor_buffers,
                  'conveyor_buffers_full': conveyor_buffers_full,
                  'sink_machines_rate': sink_machines_rate,
                  'sink_machines_rate_sum': sum(sink_machines_rate),
                  'sink_throughput_delta': sinks_throughput_delta,
                  'sink_throughput_delta_sum': sum(sinks_throughput_delta),
                  'sink_throughput_absolute_sum': sum(sinks_throughput_abs),
                  'conveyor_infeed_m1_prox_empty': conveyor_infeed_m1_prox_empty,
                  'conveyor_infeed_m2_prox_empty': conveyor_infeed_m2_prox_empty,
                  'conveyor_discharge_p1_prox_full': conveyor_discharge_p1_prox_full,
                  'conveyor_discharge_p2_prox_full': conveyor_discharge_p2_prox_full,
                  'illegal_machine_actions': illegal_machine_actions,
                  # [AJ]: Comment the following since there is no illegal conveyo action                  
                #   'illegal_conveyor_actions': illegal_conveyor_actions,
                  'remaining_downtime_machines': remaining_downtime_machines,
                  'control_delta_t': control_delta_t,
                  'env_time': self.env.now
                  }

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
    my_env.reset()
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
