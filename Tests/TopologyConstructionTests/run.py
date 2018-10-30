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
ns = None
discovered_ips = []


def run(i, hosts, lock, cv):
    global count
    global ns
    alias = create_alias()
    lock.acquire()
    compute_distances(net, hosts)
    count += 1
    lock.release()
    cv.acquire()
    if count < int(ns):
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
    pdb.set_trace()
    c.send_transactions(trans)

def parse_cmd_line():
    nh = sys.argv[1]
    ns = sys.argv[2]
    return (nh, ns)


def startup(nt, hosts):
    threads = []
    for i in range(int(nt)):
        thread = Thread(target=run, args=(i, hosts, lock, cv))
        threads.append(thread)
        thread.start()
    for t in threads:
        t.join()
    print 'Threads finished'

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print """\nUsage: python run.py <nh> <ns>\n   
        <nh> = number of hosts to be inserted in the topology\n       
        <ns> = number of sensor threads to be used. Each sensor uses three hosts: one for the passive sensor 
                capabilities (sniff traffic), one for the active sensor capabilities (look for dead nodes)
                and the last to run iTop (Mininet does not allow to run two concurrent commands on same host)\n      
        """
        sys.exit()
    #pdb.set_trace()
    (nh, ns) = parse_cmd_line()
    (net,topo) = start_network_number(1, int(nh), int(ns))
    # Delete previously generated files..
    os.system('./init.sh')
    topo.create_alias_file()
    # Spawn the threads that will run iTop and store the topology induced from each thread in the Blockchain
    asnames = topo.active_sensors
    psnames = topo.passive_sensors
    msnames = topo.monitor_sensors
    startup(ns, msnames)
    ips = get_responding_ips(psnames)
    #CLI(net)
    # Start sensors
    sensors = []
    for i in range(len(psnames)):
        sensors.append(sensor(psnames[i], msnames, net, 'sensor_config' + str(i+1) + '.json', max_fail=3,
                   known_ips=ips, simulation=True, verbose=False, asid=asnames[i], msid=msnames[i]))
    [s.start() for s in sensors]
    raw_input("\n\nPress any key when you want to run a pingAll\n\n") #TODO  ping all or other metrics?
    hosts = [net[h] for h in topo.net_hosts]
    net.ping(hosts=hosts)
    raw_input("\n\nPress any key when you want to quit\n\n")
    [s.stop() for s in sensors]





