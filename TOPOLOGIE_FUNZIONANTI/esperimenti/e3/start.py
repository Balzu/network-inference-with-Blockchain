#!/us5/bin/python

import time
import sys
from create_merge_topo import *
from threading import Thread, Lock


lock = Lock()

def run(i, nh, hosts, lock):
    if len(hosts) == 0:
        hosts = get_hosts(int(nh))
    alias = create_alias()
    lock.acquire()
    compute_distances(net, hosts) 
    lock.release()
    lock.acquire()
    make_anonymous_and_blocking_routers(net)
    lock.release()
    lock.acquire()
    create_traces(net, hosts)
    lock.release()
    (vtopo, traces) = create_virtual_topo_and_traces(alias, net, hosts)
    (M,C) = create_merge_options(vtopo, traces)
    (M, mtopo) = create_merge_topology(M, vtopo, C)
    print_topo(mtopo)
    out_i = 'm_topo_' + str(i)
    os.system('touch ' + out_i)
    with open(out_i, "w") as file:
        file.write('\nThread ' + str(i) + ' :\n')
        file.write('Hosts che hanno partecipato a raccolta tracce:\n')        
        for h in hosts:
            file.write(h + '\n')
        file.write('Topologia indotta:\n')        
        for src in mtopo:
            for d in mtopo[src][1]:
                file.write(src + ' -> ' + d + '\n')
    
def stop_net(net):
    net.stop()    

def start_net():
    ''' Start Mininet Topology'''
    topo = NetworkTopo()
    net = Mininet( topo=topo )
    add_static_routes(net)
    net.start()
    return net

def parse_cmd_line():
    nt = sys.argv[1]
    nh = 0
    hosts = []
    if sys.argv[2].startswith('h'):
        hosts = sys.argv[2:]
    else:
        nh = sys.argv[2]
    return (nt, nh, hosts)

if __name__ == '__main__':

    if len(sys.argv) < 3:
        print '\nUsage: python start.py <nt> < nh | hosts >\n' 
        '<nt> = number of threads to be used to collect traces\n' 
        '<nh> = number of random hosts that each thread will use\n' 
        '[hosts] = optional sequence of hosts, separated by whitespace, that'
        'each thread will use deterministically'
        sys.exit()

    # Delete previously generated files..
    os.system('./clean.sh')
    (nt, nh, hosts) = parse_cmd_line()
    net = start_net()
    threads = []
    for i in range(int(nt)):
        thread = Thread(target = run, args = (i, nh, hosts, lock))
        threads.append(thread)
        thread.start()
    for t in threads:
        t.join()
    print 'Threads finished'

