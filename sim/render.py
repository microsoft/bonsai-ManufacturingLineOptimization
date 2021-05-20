from matplotlib import pyplot as plt
from itertools import count
from networkx.generators import line
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import networkx as nx
import numpy as np
plt.style.use('fivethirtyeight')


x_vals = []
y_vals = []

index = count()


def line_plot():

    plt.figure(1, figsize=(35, 35))

    position = {'Source1': (0, 0.02), 'M0': (5, 0.02), 'M1': (10, 0.02), 'Con1': (12.5, 0.02), 'M2': (15, 0.02),
                'M3': (20, 0.02), 'M4': (25, 0.02), 'Con2': (27.5, 0.02), 'M5': (30, 0.02), 'Sink': (35, 0.02),
                'Source2': (0, 0), 'M6': (5, 0), 'M7': (10, 0), 'Con3': (12.5, 0), 'M8': (15, 0), 'M9': (20, 0)}

    G = nx.Graph()
    G.add_edges_from([("Source1", "M0"), ("M0", "M1"), ("M1", "Con1"), ("Con1", "Con3"), ("Con1", "M2"),
                      ("M2", "M3"), ("M3", "M4"), ("M4",
                                                   "Con2"), ("Con2", "M5"), ("M5", "Sink"),
                      ("Source2", "M6"), ("M6", "M7"), ("M7", "Con3"), ("Con3", "M8"), ("M8", "M9"), ("M9", "Con2")])

    node_sizes = [7500, 7500, 7500, 4000, 4000, 7500, 7500,
                  7500, 4000, 7500, 7500, 7500, 7500, 7500, 7500, 7500]
    node_sizes = [node/10 for node in node_sizes]

    for key, val in position.items():
        G.add_node(str(key), pos=val)
        if key == "Con1" or key == "Con2" or key == "Con3":
            continue
        txt = '(' + str(val[0]) + ',' + str(0) + ')'
        plt.text(val[0]-0.6, val[1] + 0.002, val, fontsize=8)

    nx.draw(G, nx.get_node_attributes(G, 'pos'),
            with_labels=True, node_size=node_sizes, font_size=8)

    nx.draw_networkx_edge_labels(G, position, edge_labels={('M0', 'M1'): 'C0', ('M1', 'Con1'): 'C1', ('Con1', 'M2'): 'C1',
                                                           ('Con3', 'Con1'): 'Load Balancing Conveyor',
                                                           ('M2', 'M3'): 'C2', ('M3', 'M4'): 'C3', ('M4', 'Con2'): 'C4',
                                                           ('Con2', 'M5'): 'C4', ('M6', 'M7'): 'C5', ('M7', 'Con3'): 'C6',
                                                           ('Con3', 'M8'): 'C6', ('M8', 'M9'): 'C7',
                                                           ('M9', 'Con2'): 'Joining Conveyor'}, font_color='red',
                                 font_size=8)

    plt.tight_layout()
    #plt.savefig('Line1-Line2.png', dpi=400, bbox_inches='tight')
    # plt.show()


def animate(i):

    # x = [i for i in range(0,100)]
    # y1 = np.random.randint(0,100,100)
    # y2 = np.random.randint(100,200,100)

    plt.cla()

    # plt.plot(x, y1, label='Channel 1')
    # plt.plot(x, y2, label='Channel 2')

    # plt.legend(loc='upper left')
    plt.tight_layout()
    plt.text(0.1, 0.1, str(np.random.randint(1, 10, 3)), fontsize=12)
    line_plot()


# line_plot()
ani = FuncAnimation(plt.gcf(), animate, interval=1000)

plt.tight_layout()
plt.figure(1, figsize=(35, 35))
print('Rendering...')
plt.show()
