# train brain for an optimal control of a Manufacturing line 

## Bussiness problem
Train brain to control machine and conveyor speed of a manufacturing line for maximum throughput.

## Objectives
Maximize production in a manufacturing line.  

|                        | Definition                                                   | Notes |
| ---------------------- | ------------------------------------------------------------ | ----- |
| Objective              | maximize product production     |   Example: For a can manufacturing line, the goal is to maximize can production                        |
| Constraints            |   NA |
| Observations           | Conveyors speed, machines speed, infeed and discharge proxes, line throughput | Proxes are sensors that yield a binary value. When product accumulates on the conveyor and covers the location of the prox sensor, its value becomes 1, otherwise it's value is zero  |
| Actions                |  Machines and conveyors speed | Speeds are in cans/second units |
| Control Frequency      | Fixed control frequency | User can specify control frequency inside the sim |
| Episode configurations | currently fixed | TODO: will add various configs such as downtime events |

## Solution approach

### Detailed overview of the solution 

### TODO


## Brain experimental card 

|                        | Definition                                                   | Notes |
| ---------------------- | ------------------------------------------------------------ | ----- |
| State                  |       |
| Terminal               |          |       |
| Action                 |                   |       |
| Reward or Goal         |       |     |
| Episode configurations |                      |       |

*note: Episode configurations are described more in the results section  



## Results of brain training
### Create a new brain on bonsai platfrom  
Use machine_teacher.ink that employs the following example configuration:

|   Episode configuration parameter                     | value                                                 | Notes |
| ---------------------- | ------------------------------------------------------------ | ----- |
|            |      |                        |


### Dockerize Simulator for Scaling and add the sim package

```
docker build -t <IMAGE_NAME> -f Dockerfile .
az acr login --subscription <SUBSCRIPTION_ID> --name <ACR_REGISTRY_NAME
docker tag <IMAGE_NAME> <ACR_REGISTRY_NAME>.azurecr.io/bonsai/<IMAGE_NAME>
docker push <ACR_REGSITRY_NAME>.azurecr.io/bonsai/<IMAGE_NAME>
```
Add the simulator in the Web UI. To scale with multiple simulators, one can select the simulation to scale in two ways:

1) write `package "<SimName>"` in the simulator clause in inkling
2) click the Train button and select the simulator
   
### Train Brain

<img src="img/.PNG" alt="drawing" width="900"/>


### Assess the results
(see assessment section in the appendix for details of the process)

#### Comparison with Benchmark 


<img src="img/.PNG" alt="drawing" width="900"/>



### Assessment

You can use custom assessment found in `assess_configs/myConfig.json`. 


TODO: Run the simulation with rendering using the following flag. If you add the `--test` flag, you will run using an exported brain with `http://localhost:5000`.

```sh
docker run -d -p 5000:5000 <acr_name>.azurecr.io/<workspace_id>/<brain_name>:<version>
python bonsai_integration.py --render --test
```