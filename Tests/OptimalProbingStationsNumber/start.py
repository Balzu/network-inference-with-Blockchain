# coding=utf-8

import os, sys, pdb
topo_path = os.path.abspath(os.path.join('..', '..',  'Topology'))
sen_path = os.path.abspath(os.path.join('..', '..',  'Sensor'))
blk_path = os.path.abspath(os.path.join('..', '..',  'Blockchain'))
sys.path.insert(0, topo_path)
sys.path.insert(0, sen_path)
sys.path.insert(0, blk_path)
from create_merge_topo import *
from sensor import *
from client import *

#TODO le funzioni seguenti spostale in Topology

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

def stop_net(net):
    net.stop()

def start_net():
    ''' Start Mininet Topology'''
    topo = NetworkTopo()
    net = Mininet( topo=topo )
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
    for n in nnodes:
        if n.startswith('r'):
            if n not in onodes:
                return False
    return True


if __name__ == '__main__':
    hosts = previous_hosts()
    alias = create_alias()
    #Reconstruct old topology
    (M, old_topo, traces) = get_old_topo(hosts, alias)
    # Reconstruct new_topo
    src_pairs = find_sources(traces, monitors=True) # Returns a pair because the monitor does not belong to topology
    C = compute_monitors_coverage(src_pairs, old_topo, hosts)
    shosts = monitors_selection(C, old_topo)
    # Infer the (new) topology using the (optimal ?) selection of probing stations
    os.system('./init.sh')
    net = start_net()
    compute_distances(net, hosts, src_hosts=shosts)
    create_traces(net, hosts, src_hosts=shosts)
    (vtopo, traces) = create_virtual_topo_and_traces(alias, hosts, src_hosts=shosts)
    (M, C) = create_merge_options(vtopo, traces)
    (M, new_topo) = create_merge_topology(M, vtopo, C)
    # Compare the old topology against the new one, to see if the gathered traces are enough or all monitors must be used.
    end = compare_topologies(old_topo, new_topo)
    print end



