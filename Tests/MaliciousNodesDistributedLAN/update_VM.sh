#!/bin/bash

ssh mininet@192.168.0.203 'cd network-inference-with-BlockchainNEW; git fetch --all; git reset --hard lan/iTopModifications'

ssh mininet@192.168.0.201 'cd network-inference-with-BlockchainNEW; git fetch --all; git reset --hard lan/iTopModifications'

ssh mininet@192.168.0.202 'cd network-inference-with-BlockchainNEW; git fetch --all; git reset --hard lan/iTopModifications'

ssh mininet@192.168.0.204 'cd network-inference-with-BlockchainNEW; git fetch --all; git reset --hard lan/iTopModifications'

ssh mininet@192.168.0.205 'cd network-inference-with-BlockchainNEW; git fetch --all; git reset --hard lan/iTopModifications'

ssh mininet@192.168.0.206 'cd network-inference-with-BlockchainNEW; git fetch --all; git reset --hard lan/iTopModifications'

