#!/bin/bash


sshpass -p mininet ssh -o StrictHostKeyChecking=no mininet@192.168.0.201 'cd guest_share/network-inference-with-Blockchain; git fetch --all; git reset --hard origin/iTopModifications'

sshpass -p mininet ssh -o StrictHostKeyChecking=no mininet@192.168.0.202 'cd guest_share/network-inference-with-Blockchain; git fetch --all; git reset --hard origin/iTopModifications'

sshpass -p mininet ssh -o StrictHostKeyChecking=no mininet@192.168.0.203 'cd guest_share/network-inference-with-Blockchain; git fetch --all; git reset --hard origin/iTopModifications'

sshpass -p mininet ssh -o StrictHostKeyChecking=no mininet@192.168.0.204 'cd guest_share/network-inference-with-Blockchain; git fetch --all; git reset --hard origin/iTopModifications'

sshpass -p mininet ssh -o StrictHostKeyChecking=no mininet@192.168.0.205 'cd guest_share/network-inference-with-Blockchain; git fetch --all; git reset --hard origin/iTopModifications'

sshpass -p mininet ssh -o StrictHostKeyChecking=no mininet@192.168.0.206 'cd guest_share/network-inference-with-Blockchain; git fetch --all; git reset --hard origin/iTopModifications'
