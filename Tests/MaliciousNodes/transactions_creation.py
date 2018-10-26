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



def get_honest_transactions_tree(num):
    '''
    Returns a list of transactions arranged as directed binary tree (arrows from father to children)
    :param num: Number of transactions to be created, representing the edges in the tree
    :return: list of transactions
    '''
    i = 1 # Incremental ID for the routers
    t = 0 # Number of inserted transactions
    routers = {}
    trans = []
    while (t < num):
        routers['r' + str(i)] = topology_node('r' + str(i), 'R')
        routers['r' + str(2*i)] = topology_node('r' + str(2*i), 'R')
        routers['r' + str(2*i+1)] = topology_node('r' + str(2*i+1), 'R')
        trans.append(transaction(routers['r' + str(i)], routers['r' + str(2*i)]))
        trans.append(transaction(routers['r' + str(i)], routers['r' + str(2*i + 1)]))
        i += 1
        t += 2
    if i == num+1:
        del trans[len(trans)-1]
    return trans
