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



def find_sources(traces): 
    sources = set()
    for path in traces:
        sources.add(traces[path][0])
    return sources  

def copy_topo(topo):
    tmp = {}
    for k in topo:
        tmp[k] = (topo[k][0], set())
        for r in topo[k][1]:
            tmp[k][1].add(r)
    return tmp

def merge(e_i, e_j, topo):
    '''Merge the link e_j = (R3, R4) into e_i = (R1, R2)'''
    
    m_topo = copy_topo(topo) #TODO non efficiente la copia dell' intera topologia ogni volta
    #pdb.set_trace() 
    R1 = e_i.split()[0]
    R2 = e_i.split()[2]
    R3 = e_j.split()[0]
    R4 = e_j.split()[2]
    for r in m_topo.keys():
        if r == R3:
            for rr in m_topo[R3][1]:
                if rr != R3 and rr != R4:
                    m_topo[R1][1].add(rr)
        elif r == R4:
            for rr in m_topo[R4][1]:
                if rr != R3 and rr != R4:
                    m_topo[R2][1].add(rr)
        
        if R3 in m_topo[r][1]:
            m_topo[r][1].remove(R3)
            m_topo[r][1].add(R1)
        if R4 in m_topo[r][1]:
            m_topo[r][1].remove(R4)
            m_topo[r][1].add(R2)
    #The two links could have an endpoint in common
    if R3 != R1 and R3 != R2: 
        del m_topo[R3]
    if R4 != R1 and R4 != R2: 
        del m_topo[R4]
    return m_topo

def is_distance_preserved(monitors, shortest_dist, m_topo):
    for src in monitors:
        dist = compute_shortest_paths(m_topo, src)
        for dest in monitors:
            if src != dest and dest in dist: # Router 'dest' could have been removed in the merged topology 
                if shortest_dist[src+dest] != dist[dest]:
                    return False
    return True


def distance_preservation(topo, traces, M):
# Can't compute the distance between monitors (hosts), because they don't belong to topology.
# So, compute the distance between the routers they're attached to (call them monitors anyway)
   monitors = find_sources(traces)
   shortest_dist = {}
   for src in monitors:
       dist = compute_shortest_paths(topo, src)
       for dest in monitors: 
#Dijkstra finds shortest path from a source to all other destination routers
# Since links are unidirectional, dist(src->dst) could be different from dist(dst->src) (never happens)
           if src != dest:
               shortest_dist[src+dest] = dist[dest] 
   for e_i in M:
       for e_j in M[e_i]:
           if e_i != e_j:
               #pdb.set_trace()             
               m_topo = merge(e_i, e_j, topo)

               if is_distance_preserved(monitors, shortest_dist, m_topo) == False:
                   M[e_i].remove(e_j)


def create_merge_options(topo, traces):
    paths = create_paths_table(traces)
    print_table(paths)
    # Merge option table. Initially, each link has the whole set of links as merge options
    M = {} 
    for e in paths:
        M[e] = paths.keys() 
    print 'M with Full virtual topo'
    print_table(M)
    pdb.set_trace()
    trace_preservation(M, paths)
    print 'M after trace preservation'
    print_table(M)   
    distance_preservation(topo, traces, M)
    print 'M after trace preservation'
    print_table(M)   
   

def compute_shortest_paths(topo, src):
   
    dist = {}
    Q = []
    dist[src] = 0
  
    for r in topo.keys():
        if r != src:
            dist[r] = maxint
        heappush(Q, (dist[r], r))
  
    while (len(Q) > 0):
       
        u = heappop(Q)
        for v in topo[u[1]][1]:
            alt = dist[u[1]] + 1    # weight = 1 for each edge   
            if alt < dist[v]:
                Q[Q.index((dist[v],v))] = (alt, v)
                dist[v] = alt 
                heapify(Q)

    return dist
                



    
