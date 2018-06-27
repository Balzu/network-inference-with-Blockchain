#!/us5/bin/python

from build_virtual_topo import *
from heapq import *
from sys import maxint

#TODO puoi accorparlo con print_traces
def print_table(table):
    for t in table:
        print t + ' : '
        for r in table[t]:
            print r + ' '
# Table s.t. : key = edge, value = list of paths in which that edge appears
def create_paths_table(traces):
    paths = {}
   
    for path_name in traces:
        edges = traces[path_name]
        for i in range(len(edges)-1):
            edge = edges[i] + ' -> ' + edges[i+1]
            edge_r = edges[i+1] + ' -> ' + edges[i]
            if edge not in paths:
                paths[edge] = [path_name]
                paths[edge_r] = [path_name]
            else:
                paths[edge].append(path_name)
                paths[edge_r].append(path_name)
    return paths

def belong_to_same_path(e1, e2, paths):
    for p1 in paths[e1]:
        for p2 in paths[e2]:
            if p1 == p2:
                return True
    return False


def trace_preservation(M, paths):
    for e in M:
        to_remove = []
        for m in M[e]:
            if m == e or belong_to_same_path(m,e, paths):
                to_remove.append(m)    
    for r in to_remove:
        M[e].remove(r)
    return M



def create_merge_options(topo, traces):
    paths = create_paths_table(traces)
    print_table(paths)
    # Merge option table. Initially, each link has the whole set of links as merge options
    M = {} 
    for e in paths:
        M[e] = paths.keys() 
    trace_preservation(M, paths)
    print_table(M)
    #TODO testa dijkstra, poi rimuovi
    dist = compute_shortest_paths(topo,'r1')

def compute_shortest_paths(topo, src):
    dist = {}
    Q_list = []
    Q_heap = []
    dist[src] = 0

    for r in topo.keys():
        
        if r != src:
            dist[r] = maxint
        Q_list.append((dist[r],r)) 
        heappush(Q_heap, (dist[r], r))

    while (len(Q_list) > 0):
        pdb.set_trace() 
        u = heappop(Q_heap)
        Q_list.remove(u)
        for v in topo[u[1]][1]:
            alt = dist[u[1]] + 1    # weight = 1 for each edge
           
            if alt < dist[v]:
                
                Q_list[Q_list.index((dist[v],v))] = (alt, v)
                Q_heap = Q_list
                heapify(Q_heap)

    return dist
                



    
