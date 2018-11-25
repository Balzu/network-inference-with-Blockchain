# -*- coding: utf-8 -*-

import random, sys, os
from argparse import ArgumentParser
topo_path = os.path.abspath(os.path.join('..', '..', 'Topology'))
sys.path.insert(0, topo_path)
from transactions_creation import *
from malicious_node import *

def get_servers_id():
    '''
    :return: The ID of the servers defined in the configuration files
    '''
    return ["127.0.0.100:10000", "127.0.0.101:10000", "127.0.0.102:10000", "127.0.0.103:10000", "127.0.0.104:10000",
            "127.0.0.105:10000", "127.0.0.106:10000", "127.0.0.107:10000", "127.0.0.108:10000", "127.0.0.109:10000"]

def configure_server(config_file, unl_from_file = True, stop=False, verbose=False, malicious = 0, num_tx = 10, tree_tx = False):
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
        nrr = False if str(obj["non_responding_routers"])=='False' else True
        if unl_from_file:
            unl = load_unl(obj)
        else:
            id = ip + ":" + str(port)
            unl = random_server_selection(get_servers_id(), id)
        if malicious == 1:
            return malicious_server1(ip, port, q, lmc, lmcl, tval, ttimes, lminc, lmaxc, unl=unl, nrr=nrr,
                                     stop_on_consensus=stop, verbose=verbose, fraudolent_tx = num_tx)
        elif malicious==2:
            return malicious_server2(ip, port, q, lmc, lmcl, tval, ttimes, lminc, lmaxc, unl=unl, nrr=nrr,
                                     stop_on_consensus=stop, verbose=verbose, dropped_tx=num_tx, tree_tx=tree_tx)
        return server(ip, port, q, lmc, lmcl, tval, ttimes, lminc, lmaxc, unl=unl, nrr=nrr,
                      stop_on_consensus=stop, verbose=verbose)

def load_unl(json_obj):
    unl = []
    for n in json_obj["unl"]:
        n_id = n["ip"] + ":" + n["port"]
        unl.append(n_id)
    return unl

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

def register_client(c):
    c.ask_client_registration()

def register_observer(s):
    '''Register the provided node as observer of the nodes in its UNL'''
    s.ask_observer_registration()

def random_server_selection(servers, me):
    '''Randomly selects 5 node IDs, different from "me", from the list of servers'''
    selected = set()
    while len(selected) < 5:
        id = random.choice(servers)
        if id not in selected and id != me:
            selected.add(id)
    return selected

def parse_cmd_args():
    parser = ArgumentParser(description = "Runs a single experiment of the simulation")
    parser.add_argument("-t", "--type",
                        dest="type", required = True,
                        help="Type of the experiment to be run."
                             "\n1 = all nodes honest \n2 = Malicious nodes that do not join consensus process"
                             "\n3 = Malicious nodes that join consensus process inserting fraudolent transactions"
                             "\n4 = Malicious nodes that join consensus process dropping honest transactions")
    parser.add_argument("-n", "--number",
                        dest="number", default = 1,
                        help="Number of malicious nodes. If omitted, defaults to one.")
    parser.add_argument("-ns", "--server_number",
                        dest="server_number", default=1,
                        help="Number of the server.")
    parser.add_argument("-nft", "--fraudolent_transactions",
                        dest="fraudolent_transactions", default=10,
                        help="Number of fraudolent transactions inserted or dropped by malicious nodes."
                             "If omitted, defaults to 10.")
    parser.add_argument("-nht", "--honest_transactions",
                        dest="honest_transactions", default=0,
                        help="Number of honest transactions sent to blockchain nodes. If 0, use default transactions.")
    return  parser.parse_args()


def experiment_one_server(i):
    '''
    Runs server number 'i'. Tis function is run on the remote, blockchain host. Servers from 1 to 6 have each other in their UNL.
    Servers from 7 to 10 have an UNL made of random servers. All servers are honest.
    '''
    print '\n----------------- Experiment one ------------------\n'
    if i in range(1, 7):
        server = configure_server('configuration/server' + str(i) + '_config.json', stop=True, verbose=True)
    else:
        server = configure_server('configuration/server' + str(i) + '_config.json', unl_from_file=False, stop=True,
                             verbose=True)
    time.sleep(6 - i * 0.1)  # The last to be run waits less
    register_observer(server)
    time.sleep(5-i*0.1) # The last to be run waits less
    server.start()

def experiment_one_client(num_htx):
    '''
    Configure and run servers for experiment one. Servers from 1 to 6 have each other in their UNL.
    Servers from 7 to 10 have an UNL made of random servers. All servers are honest.
    '''
    print '\n----------------- Experiment one ------------------\n'
    # Create transactions and send them to servers
    trans = get_honest_transactions() if num_htx == 0 else get_honest_transactions_tree(num_htx)
    c = configure_client('configuration/client_config.json')
    i= 1
    pdb.set_trace()
    for sip in c.validators:
        os.system("sshpass -p mininet ssh -o StrictHostKeyChecking=no mininet@" + sip.split(':')[
            0] + " 'cd guest_share/network-inference-with-Blockchain/Tests/MaliciousNodesDistributed/;"
                 "python run.py --type 1s --server_number " + str(i) + " > /dev/null &'")
        i += 1
    time.sleep(5)
    register_client(c)
    c.send_transactions(trans)


def experiment_two(num_htx, num):
    '''
    Runs experiment 2, in which some servers do not participate actively in the consensus process.
    :param num: Number of servers that do not participate in the consensus process. Only the servers belonging to
    the first group (from 1 to 6) are considered. num must be <= |group 1|
    '''
    print '\n----------------- Experiment two ------------------\n'
    servers = []
    for i in range(1, 7):
        servers.append(configure_server('configuration/server' + str(i) + '_config.json', stop=True, verbose=True))
    for i in range(7, 11):
        servers.append(
            configure_server('configuration/server' + str(i) + '_config.json', unl_from_file=False, stop=True,
                             verbose=True))
    for s in servers:
        register_observer(s)
    # Create transactions and send them to servers
    trans = get_honest_transactions() if num_htx == 0 else get_honest_transactions_tree(num_htx)
    c = configure_client('configuration/client_config.json')
    register_client(c)
    #pdb.set_trace()
    c.send_transactions(trans)
    #for i in range(len(servers)):
    for i in range(num, 10):
        servers[i].start()
    while not servers[9].end():  # Consider one server that for sure has been started (servers[9]!)
        time.sleep(5)
    for i in range(0, num):
        servers[i].finalize() # Server socket was started anyway, so have to close it

def experiment_three(num_htx, num, num_ftx):
    '''
    Configure and run servers for experiment three. Servers from 1 to 6 have each other in their UNL.
    Servers from 7 to 10 have an UNL made of random servers.
    :param num: Number of malicious servers that participate in the consensus process inserting also fraudolent transactions.
    Only the servers belonging to the first group (from 1 to 6) are considered. num must be <= |group 1|
    :param num_tx: Number of fraudolent transactions (the same!) inserted by each malicious node
    '''
    print '\n----------------- Experiment three ------------------\n'
    servers = []
    num_mal = num
    for i in range(1, 7):
        if num_mal > 0:
            servers.append(configure_server('configuration/server' + str(i) + '_config.json', stop=True,
                                            verbose=True, malicious=1, num_tx=num_ftx))
            num_mal -= 1
        else:
            servers.append(
                configure_server('configuration/server' + str(i) + '_config.json', stop=True, verbose=True))
    for i in range(7, 11):
        servers.append(
            configure_server('configuration/server' + str(i) + '_config.json', unl_from_file=False, stop=True,
                             verbose=True))
    for s in servers:
        register_observer(s)
    # Create transactions and send them to servers
    trans = get_honest_transactions() if num_htx == 0 else get_honest_transactions_tree(num_htx)
    c = configure_client('configuration/client_config.json')
    register_client(c)
    c.send_transactions(trans)
    for s in servers:
        s.start()


def experiment_four(num_htx, num, num_ftx):
    '''
    Configure and run servers for experiment three. Servers from 1 to 6 have each other in their UNL.
    Servers from 7 to 10 have an UNL made of random servers.
    :param num: Number of malicious servers that participate in the consensus process dropping honest transactions.
    Only the servers belonging to the first group (from 1 to 6) are considered. num must be <= |group 1|
    :param num_ftx: Number of honest transactions (the same!) dropped by each malicious node
    '''
    print '\n----------------- Experiment four ------------------\n'
    servers = []
    num_mal = num
    for i in range(1, 7):
        if num_mal > 0:
            if num_htx == 0:
                servers.append(configure_server('configuration/server' + str(i) + '_config.json', stop=True,
                                            verbose=True, malicious=2, num_tx=num_ftx))
            else:
                servers.append(configure_server('configuration/server' + str(i) + '_config.json', stop=True,
                                                verbose=True, malicious=2, num_tx=num_ftx, tree_tx = True))
            num_mal -= 1
        else:
            servers.append(
                configure_server('configuration/server' + str(i) + '_config.json', stop=True, verbose=True))
    for i in range(7, 11):
        servers.append(
            configure_server('configuration/server' + str(i) + '_config.json', unl_from_file=False, stop=True,
                             verbose=True))
    for s in servers:
        register_observer(s)
    # Create transactions and send them to servers
    trans = get_honest_transactions() if num_htx == 0 else get_honest_transactions_tree(num_htx)
    c = configure_client('configuration/client_config.json')
    register_client(c)
    c.send_transactions(trans)
    for s in servers:
        s.start()

if __name__=='__main__':
    args = parse_cmd_args()
    t = args.type
    n = int(args.number)
    ns = int(args.server_number)
    nft = int(args.fraudolent_transactions)
    nht = int(args.honest_transactions)
    if t == '1':
        experiment_one_client(nht)
    elif t == '1s':
        experiment_one_server(ns)
    elif t == '2':
        experiment_two(nht, n)
    elif t == '3':
        experiment_three(nht, n, nft)
    elif t == '4':
        experiment_four(nht, n, nft)
    else:
        print '\nSpecify an integer type t : 0 < t < 5\n'

