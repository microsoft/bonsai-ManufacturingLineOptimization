## MLO Capstone Spec
Company 1 line overview: ABC Canning is a can manufacturing company.  

Process summary: Products are ingested onto the Manufacturing Line Conveyor belt from left to right. Each product passes through a machine and each machine have an infeed and discharge sensor that monitors product count to maximize machine operation. The goal of this simulation is to optimize machine speed while reducing “illegal actions” of the machine (i.e., passing products through the conveyor line while a machine is idle). 

How is it controlled today: Currently, Machine actions behave independent of each other with each machine intaking only the information from its respective sensor. As product accumulation is most likely to behave at the end of the line, final machines are likely to shut off due to machine overload with previous machines continuing to push products through to the next machine. This increases the frequency of products being sent to an idle machine, product accumulation getting exasperated and inefficient processes.  

What makes it difficult to control: The number of products on the conveyor line are only counted at machine sensor points. At each sensor point, decisions are made to either shut off a machine if a conveyor line has too few products on the line, keep a machine on if the conveyor line has enough products, or turn a machine off if there are too many products on the line to avoid over-loading the conveyor.  

Simulation: A Python Simulator is being used.  

Project objective: The objective of this project is to train a brain(s) to control machine functionality based on the influx of products to reduce instances product accumulation, adapt in instances of product under flow and optimize for machine speed.  

