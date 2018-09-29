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

def stop_net(net):
    net.stop()

def start_net():
    ''' Start Mininet Topology'''
    topo = NetworkTopo()
    net = Mininet( topo=topo )
    add_static_routes(net)
    net.start()
    return net

def run(hosts):
    #pdb.set_trace()
    alias = create_alias()
    compute_distances(net, hosts)
    print '\nTearing down router R6...\n'
    block_router(net, 'r6')
    create_traces(net, hosts)
    (vtopo, traces) = create_virtual_topo_and_traces(alias, hosts)
    (M,C) = create_merge_options(vtopo, traces)
    (M, mtopo) = create_merge_topology(M, vtopo, C)
    out = write_topo_to_file('t1', mtopo, hosts)
    c = configure_client("../../Blockchain/file_config_prova/client1_config.json")
    register_client(c)
    topo = get_topo_from_json(out)
    trans = get_transactions_from_topo(topo)
    c.send_transactions(trans)

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
    net = start_net()
    os.system('./init.sh')
    os.system('rm -f sensor.log > /dev/null') # Previous log deleted in this test, not in general case
    hosts = ['h11', 'h21', 'h31', 'h41', 'h42', 'h61', 'h62', 'h71']
    print '\nCollecting traces, running iTop, sending transactions to the Blockchain servers..\n'
    run(hosts)
    ips = get_responding_ips(hosts)
    # Start one sensor
    ignored = get_hosts_ips_from_traces(hosts)
    s = sensor('r3', 5, net, 'sensor_config.json', max_fail=3, ignored_ips = ignored,
               known_ips=ips, simulation=True, verbose=False)
    s.start()
    raw_input("\n\nPress any key when you want to run R6\n\n")
    unblock_router(net, 'r6')
    print '\nSensor should discover the new router and run iTop with reduced selection of monitors\n'
    time.sleep(10)
    mhosts = []
    mhosts.append(net['h11'])
    mhosts.append(net['r6'])
    for h in range(10):
        time.sleep(1)
        net.ping(mhosts)
    raw_input("\n\nPress any key when you want to quit\n\n")
    s.stop()
    # Assertion: was fast iTop successfully run?
    run = False
    with open('sensor.log', 'r') as file:
        for line in file:
            if 'Fast iTop successfully' in line:
                run = True
    assert run is True, "Fast iTop not successfully run"



