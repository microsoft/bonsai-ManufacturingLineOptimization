'''
source: Input to all machines with infinite number of products 
sink: Output with infinite capacity where all the made products are accumulated
Example config
Serial setting:
source -> m0 ---c0--- m1 ---c1--- m2 ---c2--- m3 ---c3--- m4 ---c4--- m5 ---sink
'''

# define the adjacent conveyors for each machine and the adjacent machines for each conveyor
# there are K machines and K-1 conveyors
# all machines should be listed as adj dictionary keys 
# all conveyors should be listed as adj_conv dictionary keys

adj = {}
adj_conv = {}
K = 12
for i in range(K):
    if i == 0:
        adj['m' + str(i)] = ('source', 'c' + str(i))
        adj_conv['c' + str(i)] = ('m' + str(i), 'm' + str(i+1))
    elif i == K-1:
        adj['m' + str(i)] = ('c' + str(i-1), 'sink')
    else:
        adj['m' + str(i)] = ('c' + str(i-1), 'c' + str(i))
        adj_conv['c' + str(i)] = ('m' + str(i), 'm' + str(i+1))


def plot():
    pass


if __name__ == "__main__":

    visited = []
    queue = []
