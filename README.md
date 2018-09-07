# network-inference-with-Blockchain

Thesis for the Master Degree in Computer Science and Networking (S.S.Sant' Anna and University of Pisa).
It is presented a tool that is able to reconstruct the topology of a network, store it in a blockchain and resist to attacks consisting in false information about the real topology.
The algorithm used to infer the topology is iTop, and it is able to discover also nodes that do not respond to ping or traceroute.
The Blockchain heavily follows the guidilenes defined in Ripple Topology. It is not based on power-consuming proof-of-work but instead relies on collectively trusted subnetworks and proceeds in rounds of consensus.
The topologies on which the experiments are carried out are built using Mininet.
The architecture is made of three part:
..* the Monitors, running iTop and building the first version of the topology
..* the Blockchain nodes, that receive the topology and securely store it into a shared and agreed-upon ledger
..* the sensor, which are placed inside the network and check both wheter the topology nodes are still alive and if new nodes joined the topology


### TODO
1. Automatically generate graphical representation of the Topology, expoiting Graph-Tool
2. Solve the following error on the Ledger, appearing some times..
Exception in thread Thread-499:
Traceback (most recent call last):
  File "/usr/lib/python2.7/threading.py", line 810, in __bootstrap_inner
    self.run()
  File "/usr/lib/python2.7/threading.py", line 763, in run
    self.__target(*self.__args, **self.__kwargs)
  File "/home/mininet/guest_share/network-inference-with-BlockchainNEW/Blockchain/node.py", line 255, in send
    ack = sender.recv(1024)
error: [Errno 104] Connection reset by peer
4. Reorganize the folders: create 3 separate directories with updated files for Blockchain, Topology creation with Mininet and Sensor. 
5. Prepare a full experiment
6. Add a simple GUI
7. Start Blockchain attacks 
