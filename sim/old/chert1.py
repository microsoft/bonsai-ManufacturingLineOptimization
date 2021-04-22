import networkx as nx 

positions = {'m1': (10, 20), 'm2': (20, 30), 'm3': (30, 30), 'm4': (40, 10)}

X=nx.Graph()
X.add_nodes_from(positions.keys())
for n, p in positions.iteritems():
    X.nodes[n]['pos'] = p

nx.draw(X, positions)
plt.show()