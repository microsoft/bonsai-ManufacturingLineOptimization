class general:
    min_speed = 10 
    max_speed = 100

class Machine():

    def __init__(self):
        self._speed = 0 
        self._state = 'idle'
        self.min_speed = general.min_speed
        self.max_speed = general.max_speed
        for i in range(1, 10):
            setattr(self, "bin" + str(i), 2*i)

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

    def get_bin(self, i):
        return getattr(self, "bin" + str(i))

    


    