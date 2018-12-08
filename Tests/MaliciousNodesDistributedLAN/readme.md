# Malicious Nodes

### Objective

This test is analogous to the test 'Malicious Nodes', with the difference that in this case each server is a separate
virtual machine. 

In this case the client resides in the local machine and its  job is to
1) Start the server computation on each of the remote server nodes
2) Send the transactions to the servers
3) Collect the results and plot the graphs

With respect to 'MaliciousNodesDistributed', which is a test that should run on cloud (ex. AWS), 
in this case the virtual machines are instantiated on a proprietary LAN.

### Dependencies

For this test to run, it is necessary to have `sshpass` installed in the local machine.
This in not an optimal solution, and in production I would use a pair of RSA keys, nevertheless is an acceptable
compromise in test phase.