# -*- coding: utf-8 -*-

'''Code for a server node of the blockchain implementing the distributed consensus algorithm'''

from transaction import *
from message import *
import json
import os
from node import *
from argparse import ArgumentParser

def configure_server(config_file, init_unl = True):
    '''Uses the parameters defined in the configuration file to create a server and return it.'''
    with open(config_file, 'r') as file:
        obj = json.load(file)
        ip = obj["ip"]
        port = int(obj["port"])
        q = float(obj["quorum"])
        lmc = float(obj["ledger_min_close"])
        lmcl = float(obj["ledger_max_close"])
        tval = {}
        ttimes = {}
        tmp = obj["threshold_values"]
        for t in tmp:
            tval[t] = float(tmp[t])
        tmp = obj["threshold_times"]
        for t in tmp:
            ttimes[t] = float(tmp[t])
        lminc = float(obj["ledger_min_consensus"])
        lmaxc = float(obj["ledger_max_consensus"])
        if init_unl:
            unl = load_unl(obj)
            return server(ip, port, q, lmc, lmcl, tval, ttimes, lminc, lmaxc, unl=unl)
        return server(ip, port, q, lmc, lmcl, tval, ttimes, lminc, lmaxc)

def load_unl(json_obj):
    unl = []
    for n in json_obj["unl"]:
        n_id = n["ip"] + ":" + n["port"]
        unl.append(n_id)
    return unl


def register_observer(s):
    '''Register the provided node as observer of the nodes in its UNL'''
    s.ask_observer_registration()


def parse_cmd_args():
    parser = ArgumentParser(description = "Instantiates a server node of the blockchain network"
                                          "running the consensus algorithm")
    parser.add_argument("-c", "--configuration_file",
                        dest="config_file", default="server_config.json",
                        help="Specify a custom configuration file for the server node (with path). "
                             "If not provided, the default \"server_config.json\" file will be used")
    parser.add_argument("-i", "--interactive",
                        dest="interactive", action='store_true',
                        help="Specify whether the program must be run in interactive mode."
                             "Default: non interactive.")
    return  parser.parse_args()

def interactive_interface(s):
    '''Defines the choices that the user can make'''
    registration = False
    end = False
    while not end:
        choice = raw_input("\n--------------PROMPT----------------------\n"
                           "\nPress 'r' to register this node to its UNL and start the server"
                           "\nPress 'd' to draw the topology stored in the current ledger"
                           "\nPress 'q' to quit the server program\n"
                           "\n------------------------------------------\n")
        if choice == 'r':
            if registration == True:
                print 'Registration already done'
            else:
                register_observer(s)
                print 'Server node ' + s.id() + ' successfully registered'
                registration = True
                s.start()
                print 'Server node ' + s.id() + ' successfully started'
        elif choice == 'd':
            s.draw_topology()
            os.system('feh print_topo.png --image-bg white')
        elif choice == 'q':
            s.stop()
            end = True
            print 'Server node ' + s.id() + ' successfully stopped'

if __name__=='__main__':
    try:
        args = parse_cmd_args()
        s = configure_server(args.config_file)
        if args.interactive:
            interactive_interface(s)
        else:
            time.sleep(5)
            register_observer(s)
            s.start()
            print 'Server started'
            time.sleep(5)
            s.stop()


    except IOError:
        print 'Provide the configuration file "server_config.json"'