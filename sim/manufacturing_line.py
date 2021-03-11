import simpy
import numpy as np 

# this is an example consists of 5 machines 



class general:
    number_of_machines = 3
    machine_infeed_buffer = 100
    machine_discharge_buffer = 100 # 
    conveyor_capacity = 1000  # in cans 

    warmup_time = 100 # in seconds 

    downtime_generation_m4 = 100 # every 100 seconds machine 1 goes down
    downtime_m4 = 10 # in seconds 


    

class sku:
    def __init__(self, id):
        '''
        Not implemented. 
        '''

    


class Machine():

    def __init__(self):
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

    
class Conveyor():
    def __init__(self,)



class DES():
    def __init__(self):
        #input->m1->c1->m2->c2->m3->c3->m4->c4-> output 
        self.env = simpy.Environment()

        self._initialize_buffers(self)
        self._initialize_macines(self)

        def _initialize_buffers(self):
        #There is no input buffer for machine 1. We can safely assume that it is infinity 
            self.m1bin = simpy.Container(self.env, init = float('inf'), capacity = general.machine_infeed_buffer)  # machine 1, infeed buffer 
            self.m1bout = simpy.Container(self.evn, init = general.machine_discharge_buffer, capacity= general.machine_discharge_buffer)

            self.c1 = simpy.Container(self.env, init = general.conveyor_capacity//2,  capacity = general.conveyor_capacity)

            self.m2bin = simpy.Container(self.env, init = general.machine_infeed_buffer//3, capacity = general.machine_infeed_buffer)  # machine 1, infeed buffer 
            self.m2bout = simpy.Container(self.evn, init = general.machine_discharge_buffer//3, capacity= general.machine_discharge_buffer)

            self.c2 = simpy.Container(self.env, init = general.conveyor_capacity//2,  capacity =  general.conveyor_capacity)

            self.m3bin = simpy.Container(self.env, init = general.machine_infeed_buffer//3, capacity = general.machine_infeed_buffer)  # machine 1, infeed buffer 
            self.m3bout = simpy.Container(self.evn, init = general.machine_discharge_buffer//3, capacity= general.machine_discharge_buffer)

            self.c3 = simpy.Container(self.env, init = general.conveyor_capacity//2,  capacity=  = general.conveyor_capacity)

            self.m4bin = simpy.Container(self.env, init = general.machine_infeed_buffer//3, capacity = general.machine_infeed_buffer)  # machine 1, infeed buffer 
            self.m4bout = simpy.Container(self.evn, init = general.machine_discharge_buffer//3, capacity= general.machine_discharge_buffer)

            self.c4 = simpy.Container(self.env, init = general.conveyor_capacity//2,  capacit y=  general.conveyor_capacity)

            self.m5bin = simpy.Container(self.env, init = general.machine_infeed_buffer//3, capacity = general.machine_infeed_buffer)  # machine 1, infeed buffer 
        # There is no output buffer it can safely be assumed to be infinity
    
        def _initialize_macines(self):
        # create instance of each machine 
            self.m1 = Machine(id = 1, speed = 10)
            self.m2 = Machine(id = 2, speed = 10)
            self.m3 = Machine(id = 3, speed = 10)
            self.m4 = Machine(id = 4, speed = 10)
            self.m5 = Machine(id = 5, speed = 10)


    def downtime_generator(self):
         
        while True:
            print('started can processing. All machines working ')
            self.env.process(self.can_processor)

            yield Timeout()



    def can_processor_machines(self):
        '''
        The idea is to take machine speed and update accumulation of cans at discharge of the each machine  

        '''

        control_frequency = 1 
        yield self.env.timeout(control_frequency)  # every 1 control frequency, we will pause 
                                                    # and calculate the can accumulation in the buffer and in the conveyor 
                                                    # we may think of a lag as well. 
        yield self.m1bout += self.m1.speed*control_frequency 
        if self.m1bout == self.general.capacity:
                ## then machine speed wills be set to zero 
        yield self.m2bout += self.m2.speed*control_frequency
            
        yield self.m3bout += self.m3.speed*control_frequency
        yield self.m4bout += self.m4.speed*control_frequency
        yield self.m5bout += self.m5.speed*control_frequency

    

    def can_processor_conveyor(self):
        '''
        The idea is to take conveyor speed and 
        '''
        


    def activity_m1(self):
        time_machine_started = self.env.now

        yield 



