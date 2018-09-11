# Up and Down 

### Objective

The present test is aimed at showing that the system is able to infer a topology and to promptly recognize
changes. Namely, we want to show that if a node goes down, the system is able to recognize it and
to remove the proper transactions from the Blockchain. When such a node re-joins actively the network,
the system is able to recognize it and to update the topology in the Blockchain accordingly.

### Steps

1. The Mininet Topology #3 is started. All routers are Responding.
2. iTop is run and the inferred topology is stored into the Blockchain. Typing 'd' on the CLI
of a Blockchain server should print the whole topology.
3. The router R5 is torn down
4. After a series of unsuccessful PING to R5, the sensor(s) declare it dead, and updates the Blockchain
removing all the transactions in which R5 appears. Typing 'd' on the CLI of a Blockchain server should 
print the topology without R5.
5. Node R5 rejoins actively the network, and a PINGALL (each host pings each other) command is 
run on Mininet. The sensor should be able to detect R5 again. At this point iTop is run
again and the new inferred topology is sent to the Blockchain. Typing 'd' on the CLI
of a Blockchain server should print the whole topology.