# coding=utf-8

import os, sys, pdb
from threading import Thread, Lock, Condition
topo_path = os.path.abspath(os.path.join('..', '..',  'Topology'))
sen_path = os.path.abspath(os.path.join('..', '..',  'Sensor'))
blk_path = os.path.abspath(os.path.join('..', '..',  'Blockchain'))
sys.path.insert(0, topo_path)
sys.path.insert(0, sen_path)
sys.path.insert(0, blk_path)
from create_merge_topo import *
from sensor import *
from client import *

cv = Condition()
lock = Lock()
count = 0
nt = None
discovered_ips = []

def stop_net(net):
    net.stop()

def start_net():
    ''' Start Mininet Topology'''
    topo = NetworkTopo()
    net = Mininet( topo=topo )
    add_static_routes(net)
    net.start()
    return net

def run(i, nh, hosts, lock, cv):
    global count
    global nt
    if len(hosts) == 0:
        hosts = get_hosts(int(nh))
    alias = create_alias()
    lock.acquire()
    compute_distances(net, hosts)
    count += 1
    lock.release()
    cv.acquire()
    if count < int(nt):
        cv.wait()
    else:
        cv.notify_all()
        cv.release()
    lock.acquire()
    create_traces(net, hosts)
    lock.release()
    (vtopo, traces) = create_virtual_topo_and_traces(alias, hosts)
    (M,C) = create_merge_options(vtopo, traces)
    (M, mtopo) = create_merge_topology(M, vtopo, C)
    out = write_topo_to_file(i, mtopo, hosts)
    c = configure_client("client1_config.json")
    register_client(c)
    #tfile = get_topo_filename("client1_config.json")
    topo = get_topo_from_json(out)
    trans = get_transactions_from_topo(topo)
    c.send_transactions(trans)



def parse_cmd_line():
    nt = sys.argv[1]
    nh = 0
    hosts = []
    if sys.argv[2].startswith('h'):
        hosts = sys.argv[2:]
    else:
        nh = sys.argv[2]
    return (nt, nh, hosts)

def startup(nt, nh, hosts):
    threads = []
    for i in range(int(nt)):
        thread = Thread(target=run, args=(i, nh, hosts, lock, cv))
        threads.append(thread)
        thread.start()
    for t in threads:
        t.join()
    print 'Threads finished'

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print """\nUsage: python start.py <nt> < nh | hosts >\n         
        <nt> = number of threads to be used to collect traces\n 
        <nh> = number of random hosts that each thread will use\n 
        [hosts] = optional sequence of hosts, separated by whitespace, that
        each thread will use deterministically\n"""
        sys.exit()
    net = start_net()
    # Delete previously generated files..
    os.system('./init.sh')
    (nt, nh, hosts) = parse_cmd_line()
    # Spawn the threads that will run iTop and store the topology induced from each thread in the Blockchain
    startup(nt, nh, hosts)
    pdb.set_trace()
    ips = get_responding_ips(hosts)
    # Start one sensor
    s = sensor('h11', 5, net, 'sensor_config.json', max_fail=3,
               known_ips=['192.168.1.4', '192.168.12.2', '192.168.1.2'], simulation=True, readmit=False) #TODO Ip li deve ottenere da iTop
    s.start()
    choice = raw_input("\nPress any key when you want to tear down R5\n")
    net.delNode('R5')





