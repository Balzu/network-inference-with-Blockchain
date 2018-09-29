# Optimal Probing Station Number

### Objective

The terms 'Probing Station' and 'Monitor' are equivalent. They both identify a host used to collect 'probes' towards
another host. In our case, a probe is the trace produced by running traceroute. 

In this test we try to select an optimal number of probing station, that is we try to identify
a minimal set of probing stations which are able to cover all the known network components.

First time iTop is run all the available monitors are used, in order to infer the most accurate topology. Next times, 
we try to achieve an optimal selection of monitors through a greedy algorithm. 
The advantage that we get is to avoid to traceroute redundant paths, since tracerouting may take some time.

### Limitations

There are cases in which the use of all monitors is mandatory. These cases are handled in in the code, anyway they are:

1. After a deletion of a node from the topology. The previous traces are no longer valid, so they cannot be used 
   to select the monitors before running the traceroutes. All the monitors must be used instead.
   
2. If some node or link failed. This situation should be recognized by the sensor, anyway if iTop is run before the 
   sensors discover this, a check is done to ensure that we (hopefully) are not missing components. After the 'optimal' 
   selection of monitors is done and traces are collected only from these monitors, we compare the new topology against 
   the old one. Since iTOP is typically run when a new node N was discovered by a sensor, the following is what happens: 

   ```
        1. Find optimal set of monitors S from which collecting probes
        2. Collect probes from each monitor in S towards all other monitors
        3. Run iTop and reconstruct the topology
        4. if NEW_TOPO ⊇ {OLD_TOPO} U {N}
        5.    end
        6. else
        7.    Repeat points 2. and 3. using all the monitors
                 
   ```
3. Even with this further test it is not guaranteed that we will discovered all the links connecting the new discovered 
   node N to the topology. This is a normal thing anyway, since in any case traceroute only covers some paths, so there 
   is no way to be sure that we will cover all the links in the topology.
   
 ### Tests
 
 1. The script "start.py", that you run with `sudo python start.py` runs assuming that a previous execution of iTop, 
 using all the available monitors, was done. If this assumption is true, the folders 'distances' and 'traceroute'
 will contain the proper file. The script makes a selection of the monitors based on the greedy heuristic and finally 
 compares the inferred topology with the one expected (based on the old, known topology). In the comparison, only 
 responding routers are kept into account.
 
 2. The script 'test_on_sensor.py', that you run with `sudo python test_on_sensor.py`, tests the capability of running a fast iTop, making a reduced selection of monitors,
 directly on a sensor. It first builds topology 3, with router R6 down, and runs iTop. Then it starts the sensor.
 After a while router R6 is 'unblocked', and the sensor should be able to see it. When the sensor discoveres this new node,
 it runs iTop to update the topology. Anyway, a fast execution of iTop is triggered (the heuristic in selecting the monitors
 is applied). The test passes if the fast iTop execution is able to discover the expected topology (old topology + R6).
 An 'assert' statement is placed at the end of the script to notify in case the fast execution of iTop fails to produce
 the required results.