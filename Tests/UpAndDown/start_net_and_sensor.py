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

def run(i, hosts, lock, cv):
    global count
    global nt
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
    hosts = sys.argv[2:]
    return (nt, hosts)

def startup(nt, hosts):
    threads = []
    for i in range(int(nt)):
        thread = Thread(target=run, args=(i, hosts, lock, cv))
        threads.append(thread)
        thread.start()
    for t in threads:
        t.join()
    print 'Threads finished'

def block_router(net, r):
    cmd1 = 'iptables -P OUTPUT DROP'
    cmd2 = 'iptables -P INPUT DROP'
    cmd3 = 'iptables -P FORWARD DROP'
    net[r].cmd(cmd1)
    net[r].cmd(cmd2)
    net[r].cmd(cmd3)
    print '\nBlocked router ' + net[r].IP()

def unblock_router(net, r):
    cmd1 = 'iptables -P OUTPUT ACCEPT'
    cmd2 = 'iptables -P INPUT ACCEPT'
    cmd3 = 'iptables -P FORWARD ACCEPT'
    net[r].cmd(cmd1)
    net[r].cmd(cmd2)
    net[r].cmd(cmd3)
    print '\nUnBlocked router ' + net[r].IP()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print """\nUsage: python start.py <nt> <hosts>\n         
        <nt> = number of threads to be used to collect traces\n     
        <hosts> = sequence of hosts, separated by whitespace, that
        each thread will use deterministically\n"""
        sys.exit()
    net = start_net()
    # Delete previously generated files..
    os.system('./init.sh')
    (nt, hosts) = parse_cmd_line()
    # Spawn the threads that will run iTop and store the topology induced from each thread in the Blockchain
    startup(nt, hosts)
    ips = get_responding_ips(hosts)
    # Start one sensor
    s = sensor('r3', 5, net, 'sensor_config.json', max_fail=3,
               known_ips=ips, simulation=True, verbose=False)
    s.start()
    raw_input("\n\nPress any key when you want to tear down R5\n\n")
    print '\nTearing down router R5...\n'
    block_router(net, 'r5')
    raw_input("\n\nPress any key when you want to run again R5\n\n")
    unblock_router(net, 'r5')
    time.sleep(5)
    net.pingAll()
    raw_input("\n\nPress any key when you want to quit\n\n")
    s.stop()





