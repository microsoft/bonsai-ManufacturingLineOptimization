## Background
While training Brain using both Q and Policy Hidden Layers, Bonsai UI began to stall with background AI Engine unable to identify new iteration champions leading to suboptimal
Brain performance and training progress. 

Bonsai UI Chart looks like this:

<img width="641" alt="mlo_brain_v11" src="https://user-images.githubusercontent.com/48301423/201440173-841821cd-7c0c-41b8-8d5e-453fd0a0ce51.png">


As a result, I conducted an experiment to get to the root of the issue. With the help of Help-Client team, the root cause and solution was found.

## Brains Apart of Experiment


### Brain: MLO-Brain  
> version: v11  
> algorithm: SAC  
> MemoryMode: "state"    
> QHiddenLayers: 1 tanh, 3 relu  
> PolicyHiddenLayers: 1 tanh, 3 relu    
> Train Time: 5h 27 minutes  
> Iterations shown in Chart: 0  
> Total Training Iterations: 728, 745




### Brain: MLO-Scaled
> version: v01  
> algorithm: SAC  
> MemoryMode: "state and action"  
> QHiddenLayers: 1 tanh, 3 relu  
> PolicyHiddenLayers: 1 tanh, 3 relu  
> Train Time: 6 days 19hrs  
> Iterations shown in Chart: 0  
> Total Training Iterations: 8,606,885  




### Brain: MLO-Scaled
> version: v03  
> algorithm: SAC  
> MemoryMode: "none"  
> QHiddenLayers: 1 linear, 3 relu  
> PolicyHiddenLayers: 1 linear, 3 relu  
> Train Time: 8 days 17hrs  
> Iterations shown in Chart: 0  
> Total Training Iterations: 31,797,410  


### Brain: MLO-Scaled
> version: v04  
> algorithm: SAC  
> MemoryMode: "none"  
> QHiddenLayers: NA  
> PolicyHiddenLayers: 1 linear, 3 relu  
> Train Time: 8hrs 37mins  
> Iterations shown in Chart: showing all iterations in chart  
> Total Training Iterations: 3,531,677  


## Solution

Such Brain architecture appears to be exhausting the capacity of the pod. Due to this, move Brain to multi-node cluster by adding the following to the top of 
Brain's inkling file:

```
experiment {
horizontal_scaling: "True",
num_cores_per_ray_node: "2000m",
memory_per_ray_node: "33Gi",
num_workers: "6",
num_rollout_worker_nodes: "6",
rollout_worker_cpu: "2000m",
rollout_worker_memory: "33Gi",
}
```
