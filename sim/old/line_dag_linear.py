from matplotlib import pyplot as plt
import networkx as nx

g1 = nx.DiGraph()
g1.add_edges_from([("source", "m1"), ("m1", "c1"), ("c1", "m2"), ("m2", "c2"), ("c2", "m3"), ("m3", "sink")])
plt.tight_layout()
nx.draw_networkx(g1, arrows=True)
plt.savefig("line_series.png", format="PNG")
# tell matplotlib you're done with the plot: https://stackoverflow.com/questions/741877/how-do-i-tell-matplotlib-that-i-am-done-with-a-plot
plt.clf()