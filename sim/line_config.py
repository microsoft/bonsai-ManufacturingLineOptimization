'''
source: Input to all machines with infinite number of cans 
Example configs
Serial:
source1 -> m0 --c0 -- m1 --c1 --- m2 ---c2 --m3 --c3 --m4 --c4 --m5 --sink

'''
## Define the adjacent conveyors for each machine and the adjacent machines for each conveyor. All machines should be listed as adj dictionary keys 

# [AJ]: There are 6 machines and 5 conveyors

adj = {
    'm0': ('source1', 'c0'),
    'm1': ('c0', 'c1'),
    'm2': ('c1', 'c2'),
    'm3': ('c2', 'c3'),
    'm4': ('c3', 'c4'),
    'm5': ('c4', 'sink')
}
adj_conv = {
    'c0': ('m0', 'm1'),
    'c1': ('m1', 'm2'),
    'c2': ('m2', 'm3'),
    'c3': ('m3', 'm4'),
    'c4': ('m4', 'm5')
}

def plot():
    pass


if __name__ == "__main__":

    visited = []
    queue = []
