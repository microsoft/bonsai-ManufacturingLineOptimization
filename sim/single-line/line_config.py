'''
source: Input to all machines with infinite number of cans 
Example configs
Serial:
source -> m0 ----c0----> m1 ----c1----> m2 ---- c2 ----> m3

Parallel:
source1 -> m0 --c0 -- m1 --c1 --- m2 ---c2 --m3 --c3 --m4 --c4 --m5 --sink
                        con_balance             con_join
source2 -> m6 --c5 -- m7 --c6 --- m8 ---c7 --m9 --c8
'''
## Define the adjacent conveyors for each machine. All machines should be listed as adj dictionary keys 

# [AJ]: Comment the following to only consider single line
# [AJ]: Two lines
# [AJ]: There are 10 machines and 9 conveyors
# adj = {
#     'm0': ('source1', 'c0'),
#     'm1': ('c0', 'c1'),
#     'm2': ('c1', 'c2'),
#     'm3': ('c2', 'c3'),
#     'm4': ('c3', 'c4'),
#     'm5': ('c4', 'sink'),
#     'm6': ('source2', 'c5'),
#     'm7': ('c5', 'c6'),
#     'm8': ('c6', 'c7'),
#     'm9': ('c7', 'c8')
# }

# [AJ]: Comment the following to consider doubele line
# [AJ]: Single line
# [AJ]: There are 6 machines and 5 conveyors
adj = {
    'm0': ('source1', 'c0'),
    'm1': ('c0', 'c1'),
    'm2': ('c1', 'c2'),
    'm3': ('c2', 'c3'),
    'm4': ('c3', 'c4'),
    'm5': ('c4', 'sink')
}

# [AJ]: Comment the following to consider single line without the use of conveyors for load balancing between two lines
# con_balance  = [('c1','c6', 4)]   # balancing load between two conveyors, the last number indicates where cans are added. Use same for both  
# con_join =  [['c8','c3', 4]]   # adding the load from first one on to the second conveyor, the last number indicates the joining on the second conveyor's bin from the last bin of the first conveyor. 

def plot():
    pass


# from collections import defaultdict 

# def transform_adj(adj, con_balance, con_join):
#     adj_conv = defaultdict(tuple)
#     for machine in adj.keys():
#         for conveyor in adj[machine]:
#             if adj_conv[conveyor]:
#                 adj_conv[conveyor]+= (machine,)
#             else: 
#                 adj_conv[conveyor]= (machine,)

#     i = 0 
#     for conveyor in con_balance:
#         adj_conv[balance+str(i)]+= (adj_conv[conveyor][]


# import networkx as nx
# G = nx.Graph()
# for machine in adj.keys():
#     G.add_node(machine)
#     for conveyor in adj[machine]:
        


# visited = []
# queue = []
# def bfs(visited, graph, node):
#     visited.append(node)
#     queue.append(node)

#     while queue:
#         s = queue.pop(0)
#         for neighbor in 




if __name__ == "__main__":

    visited = []
    queue = []






            