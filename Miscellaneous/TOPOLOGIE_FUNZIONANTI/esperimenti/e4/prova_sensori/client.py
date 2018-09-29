# -*- coding: utf-8 -*-

'''Code for a client node sending transactions to the server nodes that comprise the blockchain'''

from argparse import ArgumentParser
from util import *

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
