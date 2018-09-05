# coding=utf-8
"""
This module contains utility functions, used to startup the simulation.
"""
import json
import os
from build_topo3 import *
from node import *

def configure_client(config_file):
    '''Uses the parameters defined in the configuration file to create a client and return it.'''
    with open(config_file, 'r') as file:
        obj = json.load(file)
        ip = obj["ip"]
        port = obj["port"]
        validators = []
        for v in obj["validators"]:
            v_id = v["ip"] + ":" + v["port"]
            validators.append(v_id)
        return client(ip, port, validators)

def get_topo_from_json(filename):
    topo = []
    with open(filename, 'r') as file_topo:
        obj = json.load(file_topo)
        topo = obj["topology"]
    return topo

def build_txset_from_topo(topo):
    # First build dictionary having key = node_name, value = node
    nodes = {}
    for n in topo:
        node = topology_node(n["Name"], n["Type"])
        nodes[ n["Name"] ] = node
    # Then create transactions and finally pass them to the transaction_set
    transactions = []
    for n in topo:
        for to in n["Neighbors"]:
            tx = transaction (nodes[n["Name"]], nodes[to])
            transactions.append(tx)
    return transaction_set( transactions)

def get_transactions_from_topo(topo):
    # First build dictionary having key = node_name, value = node
    nodes = {}
    for n in topo:
        node = topology_node(n["Name"], n["Type"])
        nodes[ n["Name"] ] = node
    # Then create transactions and finally pass them to the transaction_set
    transactions = []
    for n in topo:
        for to in n["Neighbors"]:
            tx = transaction(nodes[n["Name"]], nodes[to])
            transactions.append(tx)
    return transactions

#TODO gestisci caso in cui registrazione non va a buon fine(?)
def register_client(c):
    c.ask_client_registration()

def get_topo_filename(config_file):
    with open(config_file, 'r') as file:
        obj = json.load(file)
        return obj["topology_filename"]

def write_topo_to_file(id, mtopo, hosts):
    '''Writes the topology to file (in json) in a format suitable for being delivered to the Blockchain.
    :param id The ID of the node that has triggered iTop
    :param mtopo The 'Merge' Topology produced by iTop
    :param hosts The list of hosts (monitors) that gathered traces
    :return the filename of the topology (written on disk).'''
    out = 'm_topo_' + str(id)
    os.system('touch ' + out)
    topology = {}
    topology["hosts"] = []
    topology["topology"] = []
    for h in hosts:
        topology["hosts"].append(h)
    for src in mtopo:
        item = {}
        name = src
        _type = mtopo[src][0]
        neighbors = []
        for n in mtopo[src][1]:
            neighbors.append(n)
        item["Name"] = name
        item["Type"] = _type
        item["Neighbors"] = neighbors
        topology["topology"].append(item)
    with open(out, "w") as file:
        json.dump(topology, file)

    print '\n\n --------------------------------\n\n' \
          'iTop phase ended. Topology written in Json.\n' \
          'Now send transactions to the ledger\n\n' \
          '------------------------------------\n\n'
    return out

def stop_net(net):
    net.stop()

def start_net():
    ''' Start Mininet Topology'''
    topo = NetworkTopo()
    net = Mininet( topo=topo )
    add_static_routes(net)
    net.start()
    return net