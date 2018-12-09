#!/bin/bash

ssh mininet@192.168.0.203 'git clone -b iTopModifications mininet@192.168.0.203:/home/mininet/guest_share/network-inference-with-BlockchainNEW'
ssh mininet@192.168.0.203 'cd network-inference-with-BlockchainNEW; git remote add lan mininet@192.168.0.203:/home/mininet/guest_share/network-inference-with-BlockchainNEW; git remote rm origin'
ssh mininet@192.168.0.201 'git clone -b iTopModifications mininet@192.168.0.203:/home/mininet/guest_share/network-inference-with-BlockchainNEW'
ssh mininet@192.168.0.201 'cd network-inference-with-BlockchainNEW; git remote add lan mininet@192.168.0.203:/home/mininet/guest_share/network-inference-with-BlockchainNEW; git remote rm origin'
ssh mininet@192.168.0.202 'git clone -b iTopModifications mininet@192.168.0.203:/home/mininet/guest_share/network-inference-with-BlockchainNEW'
ssh mininet@192.168.0.202 'cd network-inference-with-BlockchainNEW; git remote add lan mininet@192.168.0.203:/home/mininet/guest_share/network-inference-with-BlockchainNEW; git remote rm origin'
ssh mininet@192.168.0.206 'git clone -b iTopModifications mininet@192.168.0.203:/home/mininet/guest_share/network-inference-with-BlockchainNEW'
ssh mininet@192.168.0.206 'cd network-inference-with-BlockchainNEW; git remote add lan mininet@192.168.0.203:/home/mininet/guest_share/network-inference-with-BlockchainNEW; git remote rm origin'
ssh mininet@192.168.0.204 'git clone -b iTopModifications mininet@192.168.0.203:/home/mininet/guest_share/network-inference-with-BlockchainNEW'
ssh mininet@192.168.0.204 'cd network-inference-with-BlockchainNEW; git remote add lan mininet@192.168.0.203:/home/mininet/guest_share/network-inference-with-BlockchainNEW; git remote rm origin'
ssh mininet@192.168.0.205 'git clone -b iTopModifications mininet@192.168.0.203:/home/mininet/guest_share/network-inference-with-BlockchainNEW'
ssh mininet@192.168.0.205 'cd network-inference-with-BlockchainNEW; git remote add lan mininet@192.168.0.203:/home/mininet/guest_share/network-inference-with-BlockchainNEW; git remote rm origin'




