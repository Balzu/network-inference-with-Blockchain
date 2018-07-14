#!/us5/bin/python

import os
import pdb
from build_topo3 import *
from random import randint

def make_anonymous_and_blocking_routers(net):
    with open("NRR", "r") as nrr_file:
        for line in nrr_file:
            r = line.split(',')
            net[r[0]].cmd(r[1])
       
    
def compute_distances(net, hosts):
    distances = {}
    for h1 in hosts:
        for h2 in hosts:
            if h1 != h2:                    
            # For each host different from host1, add a line with the name of the host
            # and the distance from host1 (exploit TTL to derive the distance)
                print "Starting ping from " + h1 + " ... "
                os.system("touch distances/" + h1) 
                os.system("echo -n '" + h2 + " '  >> distances/" + h1)
                net[h1].cmd('ping -c 1 ' + net[h2].IP() + 
                " | grep from | awk '{split($6,a,\"=\"); print 64 - a[2]}'>> distances/" + 
                h1)


def get_hosts(num):
    '''Return "num" random hosts'''
    with open ("hosts", "r") as hosts_file:   
        hosts = hosts_file.read().split()
        r_hosts = []
        for i in range(num):
            r = randint(0, len(hosts)-1)
            r_hosts.append(hosts.pop(r))
        return r_hosts


def create_traces(net, hosts):
    for h1 in hosts:
        for h2 in hosts:
            if h1 != h2:                    
            # For each host different from host1, add a line with the name of the host
            # and the distance from host1 (exploit TTL to derive the distance)
                print "Starting collection of traces from " + h1 + " ... " 
                net[h1].cmd('traceroute -n -w 0.5 ' + net[h2].IP() + ' > traceroute/' + h1 + h2)

def create_alias():
    with open("alias", "r") as alias_file:
        alias = {}
        for line in alias_file:
            l = line.split()
            for address in l[1:]:
                alias[address]=(l[0]) #l[0] is the router name
        return alias

def create_virtual_topo_and_traces(alias, net, hosts):
    topo = {}
    x = [0]  # Incremental identifier for non responding routers. x is a list used as single value
    done = set() # Insert hosts already visited (in case a blocking router is found)
    traces = {}
    for h1 in hosts:
        #pdb.set_trace()
        for h2 in hosts:
            if h1 != h2:
                print 'h1 = ' + h1 + ', h2 =  ' + h2
                print ('A' in topo)
                pdb.set_trace()
                traces[h1+h2] = []
                if get_answer_from_dest(h1,h2): 
                #Manage the cases in which no blocking router is found
                # could find one or more anonymouse router
                    add_routers(topo, h1, h2, x, alias, traces, 100, False)                            
                else:
                    #Manage the case in which you find at least one blocking router  
                    traces[h1+h2].extend(get_responding_routers(h1,h2,alias))
                    numr_h1 = num_responding_routers(h1, h2)
                    numr_h2 = num_responding_routers(h2, h1)
                    num_r = get_real_distance(h1,h2)
                    # Add the the responding routers on the path before the block and save the last                          last_h1 = add_routers(topo, h1, h2, x, alias, traces, numr_h1, True)
                    last_h2 = get_last_responding_router(h2, h1, alias)
                    unobserved = num_r - numr_h1 - numr_h2
                    if unobserved == 1: # Case 1: only one blocking router
                        if last_h1 != None:
                            next = add_router(topo, x, last_h1, 'B') 
                            traces[h1+h2].append(next)                          
                        elif last_h2 != None:
                            next = add_router(topo, x, last_h2, 'B')
                            traces[h1+h2].append(next)                          
                        else:
                            add_only_router(topo, x, 'B')
                        last_h1h2 = get_responding_routers(h2,h1,alias)[::-1]
                        traces[h1+h2].extend(last_h1h2)                            
                    elif unobserved > 1:
                        if last_h1 != None: 
                            last = add_router(topo, x, last_h1, 'NC')
                            traces[h1+h2].append(last)
                        else:
                            last = add_only_router(topo, x, 'NC')    
                            traces[h1+h2].append(last)
                        for i in range(unobserved - 2):
                            last = add_router(topo, x, last, 'H')
                            traces[h1+h2].append(last)
                        ncr_h2 = add_router(topo, x, last, 'NC')
                        traces[h1+h2].append(ncr_h2)
                        if last_h2 != None:
                            add_router(topo, x, last_h2, 'NC', new=False)    
# Complete the traces from h1 to h2 by adding the reverse path (known!) from h2                        
                        last_h1h2 = get_responding_routers(h2,h1,alias)[::-1]
                        traces[h1+h2].extend(last_h1h2)        
    return (topo,traces)


# Simply adds a Non Responding router to the topology, without any link
def add_only_router(topo, x, _type):
    x[0] += 1
    r_x = 'X'+str(x[0])
    topo[r_x] = (_type, set())
    return r_x

# Adds a router to the topology by hand (if new=True), together with the corresponding pair of links
def add_router(topo, x, r, _type, new=True):
    if new:
        x[0] += 1
        r_x = 'X'+str(x[0])
        topo[r_x] = (_type, set())
    r_x = 'X'+str(x[0])
    if r not in topo:
        topo[r] = ('R', set())
    topo[r][1].add(r_x)
    topo[r_x][1].add(r)
    return r_x
   

def num_responding_routers(h1,h2):
    num = 0
    with open ("traceroute/"+h1+h2, "r") as trace_file:
        for line in trace_file.readlines():
            l = line.split()
            if (l[1]=='*' and l[2]=='*' and l[3]=='*'):
                return num-1 #Don't count first line because is not referred to a router, but to the host itself
            num += 1
        return 100 # An impossible number, since max number of routers is 30  

def get_responding_routers(h1,h2,alias):
    lst = []
    with open ("traceroute/"+h1+h2, "r") as trace_file:
        trace_lines = trace_file.readlines()
        num_l = len(trace_lines)
        i = 0
        for line in trace_lines:
            i += 1
            l = line.split()
            if (l[1]=='*' and l[2]=='*' and l[3]=='*') or (i==num_l):
                return lst
            if l[0] != 'traceroute': # skip first line
                last = [e for e in l[1:] if e != '*'][0] 
                lst.append(alias[last])
        return lst  

def get_last_responding_router(h1,h2,alias):
    last = None
    with open ("traceroute/"+h1+h2, "r") as trace_file:
        trace_lines = trace_file.readlines()
        num_l = len(trace_lines)
        i = 0
        for line in trace_lines:
            i += 1
            l = line.split()
            if (l[1]=='*' and l[2]=='*' and l[3]=='*') or (i==num_l): # last line contains info on final host
                return (alias[last] if i>2 else None )
            last = [e for e in l[1:] if e != '*'][0]
        return alias[last]  

def get_real_distance(h1,h2):
    with open ("distances/"+h1, "r") as dist_file:
        for line in dist_file.readlines():
            l = line.split()
            if l[0]== h2:
                return int(l[1])
        return 100 # Impossible distance
        


def get_answer_from_dest(host1,host2):
    count = len(open("traceroute/"+host1+host2).readlines())
    if count <= 30:
        return True
    else:
        return False

# Adds to the virtual topology the routers found in the traces and returns the last added router
# Works by scanning a trace line by line. If this method is not invoked in the blocking case,
# It also takes care of creating the traces from host1 to host2
def add_routers(topo, host1, host2, x, alias, traces, max_iter, blocking_case):
    with open("traceroute/"+host1+host2) as trace:
        lines = trace.readlines()        
        src = None
        dst = None
        if max_iter == 100:
            num_lines = len(lines)
            max_iter = num_lines -2 #skip first and last line (don't consider hosts)
        if max_iter == 1: # Only add the router to the virtual topo and return it
            dst = find_router(lines[1].split(), alias)
            if dst not in topo:
                if dst == 'A':
                    dst = add_only_router(topo, x, dst)
                else:
                    topo[dst] = ('R', set())
            if not blocking_case: #TODO Questo if era annidato, ma credo sia giusto ora. Controlloa
                traces[host1+host2].append(dst)
        for i in range(1, max_iter):
            src = find_router(lines[i].split(), alias)
            dst = find_router(lines[i+1].split(), alias)
            (src,dst) = add_link(topo,(src,dst) ,x ,i)
            if not blocking_case:
                if i==1:
                    traces[host1+host2].append(src)
                traces[host1+host2].append(dst)
    return dst   

def find_router(line,alias):
    i = 1
    while  i <= 3 and line[i]=='*':
        i=i+1
    if i > 3:
        return 'A'
    else:
        return alias[line[i]]

# Adds a directed link and returns the pair (src,dst) with their real name
def add_link(topo, (src,dst),x,line=100, bidirectional=True):  # line=100 is an impossible value. Keep this default when you insert links by hand and not by scanning the lines
    
    if src not in topo: # A non responding router is NEVER in the topology (don't have as keys 'A', 'B', 'H' or 'NC')
        if is_responding(src):   #If we have a responding router, add it as responding
            topo[src] = ('R', set())
        else:  #Non responding router: the type (anonymous, blocking, hidden, non cooperative) is the name itself
# Non responding routers are called X1, X2, X3, ... we add a virtual router to the topology for each non responding router found.            
# When the src router is a non responding (anonymous in particular) one, we add a NEW (virtual) router only if we are scanning the first
# line. Indeed, in all the other cases we would have already added that non responding router when dealing with the destination
# router of previous iteration.
            if line == 1: 
                x[0] = x[0] + 1   
                _type = src
                src = 'X'+str(x[0])
                topo[src] = (_type, set())
            else:
                src = 'X'+str(x[0])  #Added the virtual router to the topology in previous iteration
    if dst not in topo:
        if is_responding(dst):   
            topo[dst] = ('R', set())
        else:  
            x[0] = x[0] + 1   
            _type = dst
            dst = 'X'+str(x[0])
            topo[dst] = (_type, set())
            #traces[h1+h2].append(dst) # Add the anonymous router to the trace
    topo[src][1].add(dst)
    if bidirectional == True:
        topo[dst][1].add(src)
    return (src,dst)


def is_responding(router):
    if router != 'A' and router != 'H' and router != 'NC' and router != 'B': #TODO controlla di aver messo tutte le condizioni
        return True
    else:
        return False

def print_topo(topo):
    print "\n--- TOPOLOGY ---\n"
    for src in topo:
        for d in topo[src][1]:
            print src + ' -> ' + d
    print "\n--- END TOPOLOGY ---\n"

def print_nodes(topo):
    for src in topo:
        print src + ' : ' + topo[src][0]

def print_traces(traces):
    for t in traces:
        print t + ' : '
        for r in traces[t]:
            print r + ' '

