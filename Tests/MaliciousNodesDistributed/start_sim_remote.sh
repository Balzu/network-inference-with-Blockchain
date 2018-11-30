#!/bin/bash

sshpass -p mininet ssh -o StrictHostKeyChecking=no mininet@34.254.252.97 'cd guest_share/network-inference-with-Blockchain/Tests/MaliciousNodesDistributed/; python start_simulation.py'