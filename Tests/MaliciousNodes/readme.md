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
The UNL of each Blockchain server is made of 5 other servers.
Three possible attacks that a malicious server can carry out are assessed:

1. A malicious server does not express its vote 
2. A malicious node expresses its vote. It votes some fraudolent transactions.
3. A malicious node expresses its vote. It omits some honest transactions.