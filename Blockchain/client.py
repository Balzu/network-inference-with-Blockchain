# -*- coding: utf-8 -*-

'''Code for a client node sending transactions to the server nodes that comprise the blockchain'''

from transaction import *
from message import *
from node import *
import json
import time
from argparse import ArgumentParser

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
    return transaction_set('id', transactions)

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
            tx = transaction (nodes[n["Name"]], nodes[to])
            transactions.append(tx)
    return transactions

#TODO gestisci caso in cui registrazione non va a buon fine(?)
def register_client(c):
    c.ask_client_registration()

def get_topo_filename(config_file):
    with open(config_file, 'r') as file:
        obj = json.load(file)
        return obj["topology_filename"]

def parse_cmd_args():
    parser = ArgumentParser(description = "Instantiates a client node of the blockchain network"
                                          "sending transactions to the servers.")
    parser.add_argument("-c", "--configuration_file",
                        dest="config_file", default="client_config.json",
                        help="Specify a custom configuration file for the client node (with path). "
                             "If not provided, the default \"client_config.json\" file will be used")
    return  parser.parse_args()






if __name__=='__main__':
    try:
        args = parse_cmd_args()
        c = configure_client(args.config_file)
        register_client(c)
        tfile = get_topo_filename(args.config_file)
        topo = get_topo_from_json(tfile)
        trans = get_transactions_from_topo(topo)
        c.send_transactions(trans)
        #TODO Primo scambio di transazioni da client a server
        # Poi pensa che conviene fare: questo thread muore (se è solo client di startup)
        # oppure, se è anche un sensore, comincia ciclo while(true) e invia periodicamente
        # le transazioni

    except IOError:
        print 'Provide the configuration file "client_config.json"'
