# coding=utf-8
"""
This module contains utility functions.
"""
import json
import math
import os
import matplotlib.pyplot as plt
from build_topo3 import *
from node import *
from create_merge_topo import *


def get_responding_ips(hosts):
    '''Returns the set of ips that appears in the traces of the provided hosts'''
    ips = set()
    for h1 in hosts:
        for h2 in hosts:
            if h1 != h2:
                ips = ips.union(get_ips_from_trace(h1, h2))
    return list(ips)

def get_ips_from_trace(h1, h2):
    '''Returns the set of ips that appears in the trace from h1 to h2'''
    ips = set()
    with open("traceroute/"+h1+h2, "r") as trace_file:
        trace_lines = trace_file.readlines()
        num_l = len(trace_lines)
        i = 0
        for line in trace_lines:
            i += 1
            l = line.split()
            if (l[1]=='*' and l[2]=='*' and l[3]=='*') or (i==num_l):
                return ips
            if l[0] != 'traceroute':
                last = [e for e in l[1:] if e != '*'][0]
                ips.add(last)
            elif l[0] == 'traceroute': # We also want to know the ips of the host
                ips.add(l[2])
        return ips

def get_hosts_ips_from_traces(hosts):
    '''Returns the set of hosts ips that collected the traces'''
    ips = set()
    for h1 in hosts:
        for h2 in hosts:
            if h1 != h2:
                with open("traceroute/"+h1+h2, "r") as trace_file:
                    trace_lines = trace_file.readlines()
                    for line in trace_lines:
                        l = line.split()
                        if l[0] == 'traceroute': # We also want to know the ips of the host
                            ips.add(l[2])
                        break
    return ips

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

def start_net(num=0):
    '''
    Start Mininet Topology
    :param num: Number of network to be setup
    '''
    if num == 0:
        topo = NetworkTopo()
    elif num == 1:
        topo = NetworkTopo1()
    net = Mininet( topo=topo) #, controller=POX )
    add_static_routes(net)
    net.start()
    return net

def compare_topologies(old_topo, new_topo, new_nodes=[]):
    '''
    Compares the new topology against the old one to decide whether the new topology, obtained with a reduced selection
    of monitors, is sufficient.
    :param old_topo: The topology inferred in previous iteration
    :param new_topo: The topology inferred in current iteration, using a reduced number of monitors
    :param new_nodes: New nodes discovered by the sensor, that are added to the old_topo
    :return: True if the new topology inferred is satisfying, False if another run of iTop, using all the
              monitors, has to be done.
    '''
    onodes = set(old_topo.keys())
    nnodes = new_topo.keys()
    for n in new_nodes:
        onodes.add(n)
    for n in onodes:
        if n.startswith('r'):
            if n not in nnodes:
                return False
    return True

def previous_hosts():
    ''' Retrieve the hosts used in the previous run of traceroute'''
    os.system("ls traceroute | grep h | awk -F\"h\" '{ printf \"%s\\n%s\\n\",$2,$3 }' > traceroute/old")
    hosts = set()
    with open ('traceroute/old', 'r') as hfile:
        for h in hfile:
            hosts.add('h' + str(h).strip())
    return list(hosts)

def get_old_topo(hosts, alias):
    (vtopo, traces) = create_virtual_topo_and_traces(alias, hosts)
    (M, C) = create_merge_options(vtopo, traces)
    (M, mtopo) = create_merge_topology(M, vtopo, C)
    return (M, mtopo, traces)

def shortest_paths_coverage(src, topo, monitors_pairs):
    '''
    Computes and returns the nodes of the topology covered from the shortest paths originated from node src.
    The shortest paths from src to all other nodes are computed, but only the shortest paths to the monitors
    are considered for the converage.
    If there is a single shortest path towards a node, then all the nodes in the path are added to the coverage.
    If there are multiple shortest paths towards a node, then only the nodes in the intersection of the shortest
    paths are kept.
    Each node is provided a set keeping the nodes in the intersection of the shortest paths towards this node.
    The set is initially empty for all the nodes with the except of the source (it contains only itself).
    The alg. maintains the invariant by updating the set every time a new shortest path is found. If the shortest
    paths has lower cost, then we replace the set; if the shortest path has equal cost, then we update the set
    to contain only the intersections of the two sets.
    '''
    dist = {} # Distances
    C = {}    # Coverage
    Q = []    # Priority queue
    dist[src] = 0
    for r in topo.keys():
        if r != src:
            dist[r] = maxint
        heappush(Q, (dist[r], r))
        C[r] = set()
    C[src].add(src)
    while (len(Q) > 0):
        u = heappop(Q)
        for v in topo[u[1]][1]:
            alt = dist[u[1]] + 1  # weight = 1 for each edge
            if alt < dist[v]:# Found a (new) shortest path
                Q[Q.index((dist[v], v))] = (alt, v)
                dist[v] = alt
                heapify(Q)
                C[v] = C[u[1]].copy()
                C[v].add(v)
            elif alt == dist[v]: # Found shortest path of equal cost
                new = C[u[1]].copy()
                C[v] = C[v].intersection(new)
    tot_cov = set() # total coverage of node src
    for (r, m) in monitors_pairs:
        if r.startswith('r'):
            tot_cov = tot_cov.union(C[r])
    return tot_cov


def compute_monitors_coverage(src_pairs, topo, monitors):
    '''Computes and returns the coverage of the network nodes for each monitor.
    @:param src_pairs: set of pairs (src_router, src_monitor). We need to keep both
    because monitors do not belong to the network topology. Only the coverage of responding routers is considered.
    '''
    C = {}
    for (r, m) in src_pairs:
        if r.startswith('r'):
            C[m] = shortest_paths_coverage(r, topo, src_pairs)
    return C

def monitors_selection(C, topo):
    '''
    Performs a greedy selection of the monitors, trying to discover the minimum set of monitors whose probes are
    able to cover all the network nodes.
    :param C: Coverage dictionary st key = monitor, value = set of nodes covered by that monitor
    :param topo: Network topology
    :return: List of selected monitors
    '''
    A = set() # Set of actually covered nodes
    selection = []
    nodes = topo.keys() # We want to cover only responding routers
    for n in topo.keys():
        if n.startswith('X'):
            nodes.remove(n)
    total = len(nodes)
    while len(A) < total:
        (num, mon) = 0, ''
        for m in C:
            if len(A.union(C[m]).difference(A)) > num:
                num = len(A.union(C[m]).difference(A))
                mon = m
        A = A.union(C[mon])
        selection.append(mon)
        del C[mon]
    return selection

def compare_topologies(old_topo, new_topo, new_nodes=[]):
    '''
    Compares the new topology against the old one to decide whether the new topology, obtained with a reduced selection
    of monitors, is sufficient.
    :param old_topo: The topology inferred in previous iteration
    :param new_topo: The topology inferred in current iteration, using a reduced number of monitors
    :param new_nodes: New nodes discovered by the sensor, that are added to the old_topo
    :return: True if the new topology inferred is satisfying, False if another run of iTop, using all the
              monitors, has to be done.
    '''
    onodes = set(old_topo.keys())
    nnodes = new_topo.keys()
    for n in new_nodes:
        onodes.add(n)
    for n in nnodes:
        if n.startswith('r'):
            if n not in onodes:
                return False
    return True

def setup_logger(logger_name, log_file, level=logging.INFO):
    l = logging.getLogger(logger_name)
    formatter = logging.Formatter('%(message)s')
    fileHandler = logging.FileHandler(log_file, mode='a')
    fileHandler.setFormatter(formatter)
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(formatter)

    l.setLevel(level)
    l.addHandler(fileHandler)
    l.addHandler(streamHandler)

def plot_histogram(times, filename, show=False):
    '''
    Plots the histogram of the completion times of the various phases
    :param times: list of times. The times must be sorted: [open, establish, accept, total]
    :param name: The filename of the plot on disk
    '''
    #pdb.set_trace()
    xvals = range(int(4))
    xnames=["Open","Establish","Accept","Total"]
    yvals = times
    width = 0.25
    yinterval = 10

    figure = plt.figure()
    plt.grid(True)
    plt.xlabel('Phases')
    plt.ylabel('Average Completion Times')

    plt.bar(xvals, yvals, width=width, align='center')
    plt.xticks(xvals, xnames)
    plt.yticks(range(0, int(math.ceil(max(yvals))),yinterval))
    plt.xlim([min(xvals) - 0.5, max(xvals) + 0.5])

    figure.savefig(filename,format="png")
    if show: plt.show()