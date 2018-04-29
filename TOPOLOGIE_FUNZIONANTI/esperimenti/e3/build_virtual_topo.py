#!/us5/bin/python

import os
import pdb
from build_topo3 import *

def make_anonymous_and_blocking_routers(net):
    with open("NRR", "r") as nrr_file:
        for line in nrr_file:
            r = line.split(',')
            net[r[0]].cmd(r[1])
       
    
def compute_distances(net):
    with open ("hosts", "r") as hosts_file:
        hosts = hosts_file.read().split()
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
    
def create_traces(net):
    with open ("hosts", "r") as hosts_file:
        hosts = hosts_file.read().split()
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

def create_virtual_topo(alias, net):
    with open ("hosts", "r") as hosts_file:    
        hosts = hosts_file.read().split()
        topo = {}
        x = [0]  # Incremental identifier for non responding routers. x is a list used as single value
        for h1 in hosts:
            for h2 in hosts:
                if h1 != h2:             
                    if get_answer_from_dest(h1,h2): 
                        #TODO manage the cases in which no blocking router is found
                        # could find one or more anonymouse router
                        add_routers(topo, h1, h2, x, alias)
                    else:
                        #TODO Manage the case in which you find at least one blocking router  
                        print "Manage Blocking router case"
    return topo

def get_answer_from_dest(host1,host2):
    count = len(open("traceroute/"+host1+host2).readlines())
    if count <= 30:
        return True
    else:
        return False

def add_routers(topo,host1,host2,x, alias):
    with open("traceroute/"+host1+host2) as trace:
        lines = trace.readlines()
        num_lines = len(lines)
        src = ''
        dst = ''
        for i in range(1, num_lines-2):  #skip first and last line (don't consider hosts)
            src = find_router(lines[i].split(), alias)
            dst = find_router(lines[i+1].split(), alias)
            add_link(topo,(src,dst),x,i)    

def find_router(line,alias):
    i = 1
    while  i <= 3 and line[i]=='*':
        i=i+1
    if i > 3:
        return 'A'
    else:
        return alias[line[i]]

def add_link(topo,(src,dst),x,line):
    #pdb.set_trace()
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
                src = 'X'+str(x[0])
    if dst not in topo:
        if is_responding(dst):   
            topo[dst] = ('R', set())
        else:  
            x[0] = x[0] + 1   
            _type = dst
            dst = 'X'+str(x[0])
            topo[dst] = (_type, set())
    topo[src][1].add(dst)


def is_responding(router):
    if router != 'A' and router != 'H' and router != 'NC' and router != 'B': #TODO controlla di aver messo tutte le condizioni
        return True
    else:
        return False

def print_topo(topo):
    for src in topo:
        for d in topo[src][1]:
            print src + ' -> ' + d

def run():
    os.system('./clean.sh')  #Delete previously generated files..
    topo = NetworkTopo()
    net = Mininet( topo=topo )
    add_static_routes(net)
    net.start()
    compute_distances(net) 
    make_anonymous_and_blocking_routers(net)
    create_traces(net)
    alias = create_alias()
    vtopo = create_virtual_topo(alias, net)
    print_topo(vtopo)
    net.stop()


if __name__ == '__main__':
    setLogLevel( 'info' )
    run()
