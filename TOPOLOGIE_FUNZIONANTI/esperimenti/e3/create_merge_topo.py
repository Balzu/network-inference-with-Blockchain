#!/us5/bin/python

from build_virtual_topo import *
from create_compatibility_table import *
from heapq import *
from sys import maxint

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

def merge(e_i, e_j, topo, copy = True):
    '''Merge the link e_j = (R3, R4) into e_i = (R1, R2)'''    
    if copy:
        m_topo = copy_topo(topo) #TODO non efficiente la copia dell' intera topologia ogni volta    
    else:
        m_topo = topo    
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
    if R4 != R1 and R4 != R2 and R4!=R3: # If R4 = R3, I already deleted it! 
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
              
               m_topo = merge(e_i, e_j, topo)

               if is_distance_preserved(monitors, shortest_dist, m_topo) == False:
                   M[e_i].remove(e_j)

def is_compatible(e_i, e_j, C, topo):
# Ri is a pair = (name, type of router)
    R1 =  e_i.split()[0]
    R2 =  e_i.split()[2]
    R3 =  e_j.split()[0]
    R4 =  e_j.split()[2]
    R1 = (R1, topo[R1][0])
    R2 = (R2, topo[R2][0])
    R3 = (R3, topo[R3][0])
    R4 = (R4, topo[R4][0])
# Check if e_j is a valid option for e_i. Return false if the types or R3 and R4 are not
# valid options for R1 and R3
    try:
        if R3[1] + '-' + R4[1] not in C[R1[1] + '-' + R2[1]]:
            return False
        else:  # If corresponding routers are responding ones, they must be the same
            if is_responding(R1[1]) and is_responding(R3[1]):
                if R1[0] != R3[0]:
                    return False
            if is_responding(R2[1]) and is_responding(R4[1]):
                if R2[0] != R4[0]:
                    return False
    except KeyError, e:
        return False
    return True


def endpoint_compatibility(M,C,topo):
   
    for e_i in M:
        to_remove = []
        for e_j in M[e_i]:
            if is_compatible(e_i, e_j, C, topo) == False:
                to_remove.append(e_j)
        for e in to_remove:
            M[e_i].remove(e)


def create_merge_options(topo, traces):
    paths = create_paths_table(traces)
    # Merge option table. Initially, each link has the whole set of links as merge options
    M = {} 
    for e in paths:
        M[e] = paths.keys() 
    print 'M with Full virtual topo'
    print_table(M)   
    trace_preservation(M, paths)
    print 'M after trace preservation'
    print_table(M)   
    distance_preservation(topo, traces, M)
    print 'M after distance preservation'
    print_table(M)   
    C = get_compatibility_table()
    endpoint_compatibility(M,C,topo) 
    return (M, C)


def get_link_with_min_options(M):
    e_min = None
    min_opt = maxint
    for e in M:
        if len(M[e]) < min_opt and len(M[e]) > 0: 
            min_opt = len(M[e])
            e_min = e
    return e_min

def get_link_with_min_options_from_list(M_ei, M):
    e_min = None
    min_opt = maxint
    to_remove = []
    for e in M_ei:
        try:
            if len(M[e]) < min_opt: 
                min_opt = len(M[e])
                e_min = e
        except KeyError, err:
            to_remove.append(e)
    [M_ei.remove(e) for e in to_remove]
    return e_min  #, min_opt)
    

def get_new_types(e_i, e_j, C, topo):
    R1 =  e_i.split()[0]
    R2 =  e_i.split()[2]
    R3 =  e_j.split()[0]
    R4 =  e_j.split()[2]
    T1 = topo[R1][0]
    T2 = topo[R2][0]
    T3 = topo[R3][0]
    T4 = topo[R4][0]
    return C[T1+'-'+T2][T3+'-'+T4]

def replace_option(M, old_e, new_e):
    lst = M[old_e]
    del M[old_e]
    print 'Deleted in replace_option ' + old_e
    M[new_e] = lst
    for e in M:
        if old_e in M[e]:
            M[e].remove(old_e)
            M[e].append(new_e)

def get_new_endpoints(e, e_i, e_j):
    R1 =  e_i.split()[0]
    R2 =  e_i.split()[2]
    R3 =  e_j.split()[0]
    R4 =  e_j.split()[2]
    Re1 =  e.split()[0]
    Re2 =  e.split()[2]
    if Re1==R3 or Re1==R4 or Re2==R3 or Re2==R4:
        if Re1 == R3:
            Re1 = R1
        elif Re1 == R4:
            Re1 = R2
        if Re2 == R3:
            Re2 = R1
        elif Re2 == R4:
            Re2 = R2
        return (True, Re1, Re2)
    return (False, Re1, Re2)
         
def update_endpoints(M, e_i, e_j):
    for e in M.keys():
        for ee in M[e]:
            (new, Re1, Re2) = get_new_endpoints(ee, e_i, e_j)
            if new: # First: if the case, change the endpoints in the option list of e
                M[e].remove(ee)
                M[e].append(Re1 + ' -> ' + Re2)
        (new, Re1, Re2) = get_new_endpoints(e, e_i, e_j)
        if new: # Second: if the case, change the endpoint of e ( and update the dictionary)
            new_e = Re1 + ' -> ' + Re2
            lst = M[e]
            del M[e]
            M[new_e] = lst
        

def merge_links(e_i, e_j, M, topo, C):
    '''Performs the merge, updating the topology; updates the merge options; updates the router classes'''
    types = get_new_types(e_i, e_j, C, topo) 
    print 'Merge Links: e_i= '+ e_i + ', e_j = ' + e_j
    merge(e_i, e_j, topo, copy = False) #TODO check if correct
    to_remove = []    
    [to_remove.append(e) for e in M[e_i] if e not in M[e_j]]
    [M[e_i].remove(e) for e in to_remove]
    del M[e_j]
    print 'deleted ' + e_j
    edges = M.keys()
    for e in edges: # TODO qui c'era solo M 
# Could use just 2 conditions, leave 3 for readability
# Check ' e in M ' because you actually change the keys in update_endpoints()
        if e != e_i: # and e in M: 
            if e_i in M[e] and e_j in M[e]:
                M[e].remove(e_j) # leave only e_i
            elif e_i in M[e] and e_j not in M[e]:
                M[e].remove(e_i)
            elif e_j in M[e] and e_i not in M[e]:
                M[e].remove(e_j)
            #update_endpoints(M, M[e], e_i, e_j, edges)
  
    update_endpoints(M, e_i, e_j)

    R1 =  e_i.split()[0]
    R2 =  e_i.split()[2]
    T1 = types.split('-')[0]
    T2 = types.split('-')[1]
   
    topo[R1] = (T1, topo[R1][1])
    topo[R2] = (T2, topo[R2][1])


def create_merge_topology(M, topo, C):
    e_i = get_link_with_min_options(M)
    e_j = get_link_with_min_options_from_list(M[e_i], M)
    while e_i != None:
        e_j = get_link_with_min_options_from_list(M[e_i], M)
        try:
            if is_compatible(e_i, e_j, C, topo):     
                merge_links(e_i, e_j, M, topo, C)
            else:
                M[e_i].remove(e_j)
                if e_i in M[e_j]:
                    M[e_j].remove(e_i)
        except AttributeError as e:
            pass
                #del M[e_i] #TODO controlla
        e_i = get_link_with_min_options(M)
    return (M, topo)        


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
                



    
