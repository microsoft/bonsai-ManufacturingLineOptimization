from line_config import adj

def find_num_machine_conveyor():
    machines_set = set()
    conveyor_set = set()
    for machine in adj:
        machines_set.add(machine)
        for conveyor in adj[machine]:
            if ('sink' not in conveyor) and ('source' not in conveyor):
                conveyor_set.add(conveyor)
    return len(machines_set), len(conveyor_set)

if __name__=="__main__":
    print(find_num_machine_conveyor())
    