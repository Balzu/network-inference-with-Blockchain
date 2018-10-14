# Malicious Nodes

### Objective

The effect of malicious servers in the Blockchain is assessed.
Initially all the servers in the Blockchain are honest, and the completion times of the various phases
(open, establish, and accept phase) are measured.
Then malicious nodes are inserted. Initially only one and then increasing in number.
The effects of such malicious nodes are assessed, in particular we expect that a single malicious nodes will slow 
down the consensus process, while when malicios nodes are above a given threshold the consensus process will be impaired.

### Tests
 
Initially 100 'honest' transactions are inserted into the Blockchain.
There are 10 Blockchain servers:
 * For Servers 1 to 6, the UNL of each Blockchain server is made of the other 5 servers.
  * For Servers 7 to 10, the UNL of each Blockchain server is made of 5 random servers.
  
Three possible attacks that a malicious server can carry out are assessed:

1. A malicious server does not express its vote 
2. A malicious node expresses its vote. It votes some fraudolent transactions.
3. A malicious node expresses its vote. It omits some honest transactions.

### Run

Run the simulation with `sudo python start_simulation.py`.
It will run the four simulations defined in the file "start_simulation.py". Each simulation is made of 20 indipendent experiments
run with the same parameters. It is possible to define different parameters providing different arguments 
to the functions that start the simulations.
