from matplotlib import pyplot as plt
import networkx as nx

g1 = nx.DiGraph()
g1.add_edges_from([("source1", "m1"), ("m1", "c1"), ("c1", "m2"), ("m2", "c2"), ("c2", "m5"),("source2", "m3"), ("m3", "c3"), ("c3", "m4"), ("m4, c5"), ("c5", "m5")])
nx.is_directed(graph) # => True
nx.is_directed_acyclic_graph(graph) # => True
list(nx.topological_sort(graph))
# plt.tight_layout()
# nx.draw_networkx(g1, arrows=True)
# plt.savefig("line_hybrid.png", format="PNG")
# # tell matplotlib you're done with the plot: https://stackoverflow.com/questions/741877/how-do-i-tell-matplotlib-that-i-am-done-with-a-plot
# plt.clf()