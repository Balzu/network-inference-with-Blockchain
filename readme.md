# Discovering and Se4curely storing a Network Topology

## Abstract
We present an automated tool to discover the topology of a network and to securely store it in a Blockchain. Our tool consists of two modules. The first one implements the network topology inference algorithm. This algorithm that has been defined according to state-of-the-art techniques can infer a network topology even in cases where only partial information is available. The second module is the Blockchain related one. It adopts a fast, energy-efficient consensus algorithm and is tailored to store topology information. The two components are independent entities and experimental results confirm that their integration results in an accurate network topology reconstruction which is resilient to tampering attempts.

### Contents

Thesis for the Master Degree in Computer Science and Networking (S.S.Sant' Anna and University of Pisa).
It is presented a tool that is able to reconstruct the topology of a network, store it in a blockchain and resist to attacks consisting in false information about the real topology.
The algorithm used to infer the topology is iTop, and it is able to discover also nodes that do not respond to ping or traceroute.
The Blockchain heavily follows the guidilenes defined in Ripple Topology. It is not based on power-consuming proof-of-work but instead relies on collectively trusted subnetworks and proceeds in rounds of consensus.
The topologies on which the experiments are carried out are built using Mininet.
The architecture is made of three part:
* the Monitors, running iTop and building the first version of the topology
* the Sensors, which are placed inside the network and check both whether the topology nodes are still alive and if new nodes joined the topology
* the Blockchain nodes, that receive the topology and securely store it into a shared and agreed-upon ledger

### Folders Structure

* Blockchain: contains the code to implement the blockchain.
* Docs: contains the full thesis together with a short presentation of the work.
* Miscellaneous: contains some snippets of code and experiments. Can be skipped.
* Sensor: contains the code to implement the sensors
* Tests: contains the code for the experiments carried out in the thesis.
* Topology: contains the code to setup virtual test networks and implement the network discovery tool.
