# -*- coding: utf-8 -*-

import os
import sys
blk_path = os.path.abspath(os.path.join('..', '..',  'Blockchain'))
sys.path.insert(0, blk_path)
from node import *
from transaction import *

#TODO: se serve, puoi parametrizzare mesh con numero righe e numero colonne
def get_honest_transactions():
    '''
    Returns the list of (104) honest transactions to be inserted in the blockchain.
    The topology is a directed Mesh (from r1 you reach r60):
    r1 -> r2 -> r3 -> ... -> r10
     |     |    |     ...     |
    v     v     v     ...     v
        ................
    r51 -> r52 -> r53 -> ... -> r60
    '''
    routers = {}
    for i in range(1, 61):
        routers['r'+str(i)] = topology_node('r'+str(i), 'R')
    trans = []
    #Add orizzontal transactions
    for i in range(1, 60):
        if i % 10 != 0: # Add orizontal edge
            trans.append(transaction(routers['r'+str(i)], routers['r'+str(i+1)]))
        if i <= 50: # Add vertical edge
            trans.append(transaction(routers['r' + str(i)], routers['r' + str(i + 10)]))
    return trans



