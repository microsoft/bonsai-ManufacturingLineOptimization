from matplotlib import pyplot as plt
import networkx as nx

g1 = nx.DiGraph()
g1.add_edges_from([("root", "m1"), ("m1", "c1"), ("c1", "b1"), ("b1", "c2"), ("c2", "b3"), ("b3", "b4")])
plt.tight_layout()
nx.draw_networkx(g1, arrows=True)
plt.savefig("g1.png", format="PNG")
# tell matplotlib you're done with the plot: https://stackoverflow.com/questions/741877/how-do-i-tell-matplotlib-that-i-am-done-with-a-plot
plt.clf()