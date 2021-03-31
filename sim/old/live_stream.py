import random
from itertools import count
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np
plt.style.use('fivethirtyeight')

x_vals = []
y_vals = []

index = count()


def animate(i):

    x = [i for i in range(0,100)]
    y1 = np.random.randint(0,100,100)
    y2 = np.random.randint(100,200,100)

    plt.cla()

    plt.plot(x, y1, label='Channel 1')
    plt.plot(x, y2, label='Channel 2')

    plt.legend(loc='upper left')
    plt.tight_layout()
    plt.text(10, 20, str(np.random.randint(1,10,3)), fontsize=12)

ani = FuncAnimation(plt.gcf(), animate, interval=100)

plt.tight_layout()
plt.show()