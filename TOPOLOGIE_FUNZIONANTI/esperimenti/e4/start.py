#!/us5/bin/python

import time
import sys
import json
from create_merge_topo import *
from client import *
from util import *
from threading import Thread, Lock, Condition

cv = Condition()
lock = Lock()
count = 0
nt = None

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
    cv.acquire() # Barriera: aggiungi router non rispondenti solo dopo che distanze vere sono state calcolate
    if count < int(nt):
        cv.wait()
    else:
        cv.notify_all()
        cv.release()
    lock.acquire() # Puoi farlo fare a un solo thread portandolo dentro l'else, e evitando uso del lock
    print 'thread ' + str(i) + ' 1'
    make_anonymous_and_blocking_routers(net)
    lock.release()
    lock.acquire()
    print 'thread ' + str(i) + ' 2'
    create_traces(net, hosts)
    lock.release()
    (vtopo, traces) = create_virtual_topo_and_traces(alias, net, hosts)
    (M,C) = create_merge_options(vtopo, traces)
    (M, mtopo) = create_merge_topology(M, vtopo, C)
    print_topo(mtopo)
    out = write_topo_to_file(i, mtopo, hosts)
    c = configure_client("file_config_prova/client1_config.json") #TODO va specificato da linea di comando
    register_client(c)
    tfile = get_topo_filename("file_config_prova/client1_config.json") #TODO idem
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

if __name__ == '__main__':

    if len(sys.argv) < 3:
        print """\nUsage: python start.py <nt> < nh | hosts >\n 
        <nt> = number of threads to be used to collect traces\n 
        <nh> = number of random hosts that each thread will use\n 
        [hosts] = optional sequence of hosts, separated by whitespace, that
        each thread will use deterministically\n"""
        sys.exit()

    # Delete previously generated files..
    os.system('./clean.sh')
    (nt, nh, hosts) = parse_cmd_line()
    net = start_net()
    threads = []
    for i in range(int(nt)):
        thread = Thread(target = run, args = (i, nh, hosts, lock, cv))
        threads.append(thread)
        thread.start()
    for t in threads:
        t.join()
    print 'Threads finished'

