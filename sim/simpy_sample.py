from random import seed, randint
seed(23)

import simpy

class EV:
    def __init__(self, env):
        self.env = env
        self.drive_proc = self.env.process(self.drive())
        self.bat_ctrl_proc = self.env.process(self.bat_ctrl())
        #self.bat_ctrl_reactivate = self.env.event()

    def drive(self):
        while True:
            # Drive for 20-40 min
            yield self.env.timeout(randint(20, 40))

            # Park for 1–6 hours
            print('Start parking at', env.now)
            #self.bat_ctrl_reactivate.succeed()  # "reactivate"
            #self.bat_ctrl_reactivate = env.event()
            yield self.env.timeout(randint(60, 360))
            print('Stop parking at', self.env.now)

    def bat_ctrl(self):
        while True:
            # print('Bat. ctrl. passivating at', env.now)
            # yield self.bat_ctrl_reactivate  # "passivate"
            # print('Bat. ctrl. reactivated at', env.now)

            # Intelligent charging behavior here …
            yield env.timeout(randint(30, 90))
            print('printed the event')

env = simpy.Environment()
ev = EV(env)
while True:
    print(ev.env.now)
    env.step()