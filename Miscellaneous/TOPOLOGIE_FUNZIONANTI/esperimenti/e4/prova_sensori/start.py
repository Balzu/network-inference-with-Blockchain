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
    (vtopo, traces) = create_virtual_topo_and_traces(alias, hosts)
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
    nt = sys.argv[2]
    nh = 0
    hosts = []
    if sys.argv[3].startswith('h'):
        hosts = sys.argv[3:]
    else:
        nh = sys.argv[3]
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
    if len(sys.argv) < 4:
        print """\nUsage: python start.py <full> <nt> < nh | hosts >\n 
        <Full> = 'Y' to start from iTop, 'N' to run only the sensors (use a previously generated topology)\n
        <nt> = number of threads to be used to collect traces\n 
        <nh> = number of random hosts that each thread will use\n 
        [hosts] = optional sequence of hosts, separated by whitespace, that
        each thread will use deterministically\n"""
        sys.exit()
    net = start_net()
    if sys.argv[1] == 'Y' or sys.argv[1] == 'y':
        # Delete previously generated files..
        os.system('./clean.sh')
        (nt, nh, hosts) = parse_cmd_line()
        # Spawn the threads that will run iTop and store the topology induced from each thread in the Blockchain
        startup(nt, nh, hosts)
    #TODO Interfaccia per eseguire sensori va migliorata ( magari la scelta se eseguirli o no, e quali, la fai da CLI)
    choice = raw_input("Type 'Y' to run sensors s1 (on router r1) "
                       "and s4 (on router r4).\nType 'N' to quit the Mininet.\n")
    if choice == 'Y' or choice == 'y' or choice == 'Yes' or choice == 'YES':
        net['r1'].cmd('python start_sensor.py s1 5 file_config_prova/clientR1_config.json')
        net['r4'].cmd('python start_sensor.py s4 5 file_config_prova/clientR4_config.json')
    choice = raw_input("Type 'Q' to quit the Mininet.\n")
    if choice == 'Q' or choice == 'q':
        stop_net(net)
