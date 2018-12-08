#!/bin/bash

sshpass -p mininet ssh -o StrictHostKeyChecking=no mininet@192.168.0.201 'sudo reboot'
sshpass -p mininet ssh -o StrictHostKeyChecking=no mininet@192.168.0.202 'sudo reboot'
sshpass -p mininet ssh -o StrictHostKeyChecking=no mininet@192.168.0.203 'sudo reboot'
sshpass -p mininet ssh -o StrictHostKeyChecking=no mininet@192.168.0.204 'sudo reboot'
sshpass -p mininet ssh -o StrictHostKeyChecking=no mininet@192.168.0.205 'sudo reboot'
sshpass -p mininet ssh -o StrictHostKeyChecking=no mininet@192.168.0.206 'sudo reboot'