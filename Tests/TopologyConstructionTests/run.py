# coding=utf-8

import os, sys, pdb, time
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
from argparse import ArgumentParser


def run(i, hosts, net):
    alias = create_alias()
    compute_distances(net, hosts)
    create_traces(net, hosts, src_hosts = [hosts[i]]) # Each sensor collects the traces only from itself
    (vtopo, traces) = create_virtual_topo_and_traces(alias, hosts, src_hosts = [hosts[i]], include_host = True)
    (M,C) = create_merge_options(vtopo, traces)
    (M, mtopo) = create_merge_topology(M, vtopo, C)
    out = write_topo_to_file(i, mtopo, hosts)
    c = configure_client("configuration/client_config.json")
    register_client(c)
    topo = get_topo_from_json(out)
    trans = get_transactions_from_topo(topo)
    c.send_transactions(trans)

def configure_server(config_file, init_unl = True):
    '''Uses the parameters defined in the configuration file to create a server and return it.'''
    with open(config_file, 'r') as file:
        obj = json.load(file)
        ip = obj["ip"]
        port = int(obj["port"])
        q = float(obj["quorum"])
        lmc = float(obj["ledger_min_close"])
        lmcl = float(obj["ledger_max_close"])
        tval = {}
        ttimes = {}
        tmp = obj["threshold_values"]
        for t in tmp:
            tval[t] = float(tmp[t])
        tmp = obj["threshold_times"]
        for t in tmp:
            ttimes[t] = float(tmp[t])
        lminc = float(obj["ledger_min_consensus"])
        lmaxc = float(obj["ledger_max_consensus"])
        nrr = False if str(obj["non_responding_routers"])=='False' else True
        if init_unl:
            unl = load_unl(obj)
            return server(ip, port, q, lmc, lmcl, tval, ttimes, lminc, lmaxc, unl=unl, nrr=nrr)
        return server(ip, port, q, lmc, lmcl, tval, ttimes, lminc, lmaxc, nrr=nrr)

def load_unl(json_obj):
    unl = []
    for n in json_obj["unl"]:
        n_id = n["ip"] + ":" + n["port"]
        unl.append(n_id)
    return unl

def parse_cmd_args():
    parser = ArgumentParser(description = "Runs a simulation on a given Mininet topology")
    parser.add_argument("-n", "--number",  dest="num", required=True, type = int,
                        help="Specify the network topology number to be simulated")
    parser.add_argument("-nh", "--num_hosts",
                        dest="num_hosts", type=int,
                        help="Specify the number of hosts")
    parser.add_argument("-ns", "--num_sensors",
                        dest="num_sensors", type=int,
                        help="Specify the number of sensors")
    parser.add_argument("-s1", "--sensor_1",
                        dest="sensor1", action='store_true', default=False,
                        help="Specify whether to put a sensor 1")
    parser.add_argument("-s2", "--sensor_2",
                        dest="sensor2", action='store_true', default=False,
                        help="Specify whether to put a sensor 2")
    parser.add_argument("-s3", "--sensor_3",
                        dest="sensor3", action='store_true', default=False,
                        help="Specify whether to put a sensor 3")
    parser.add_argument("-s4", "--sensor_4",
                        dest="sensor4", action='store_true', default=False,
                        help="Specify whether to put a sensor 4")
    parser.add_argument("-i", "--interactive",
                        dest="interactive", action='store_true', default=False,
                        help="Specify whether to run this experiment in an interactive way")
    parser.add_argument("-id", "--identifier",
                        dest="id", type = int,
                        help="Specify the id of the experiment")
    parser.add_argument("-sub", "--subfolder",
                        dest="subfolder", type=str, default='',
                        help="Specify the name of the subfolder in which the drawings have to be put")
    return parser.parse_args()

def startup(nt, hosts, net):
    for i in range(int(nt)):
        run(i, hosts, net)

def start_blockchain():
    '''
    Starts the Blockchain. In this case, the blockchain is made of 6 server nodes.
    :returns The list of server comprising the blockchain
    '''
    servers = []
    for i in range (1, 7):
        servers.append(configure_server('configuration/server' + str(i) + '_config.json'))
    for s in servers:
        s.ask_observer_registration()
        s.start()
    return servers

def stop_blockchain(servers):
    '''
    Stops the Blockchain.
    :param servers: The list of servers comprising the blockchain
    '''
    for s in servers:
        s.stop()


def experiment_one(id):
    '''
    Sets up NetworkTopo1 with two sensors.
    :param id: (Incremental) Identifier of the experiment
    :return: Saves the topology stored in the ledger in a file called print_topo[id].png
    '''
    servers = start_blockchain()
    (net, topo) = start_network_number(1, sensor1=True, sensor2=True)
    os.system('./init.sh')
    topo.create_alias_file()
    asnames = topo.active_sensors
    psnames = topo.passive_sensors
    msnames = topo.monitor_sensors
    startup(2, msnames, net)
    ips = get_responding_ips(msnames)
    sensors = []
    clean_cmd_base = 'rm -rf traceroute/'
    for i in range(len(psnames)):
        clean_cmd = [clean_cmd_base + msnames[i] + '/*']
        os.system('mkdir traceroute/' + msnames[i])
        sensors.append(sensor(psnames[i], len(msnames), net, 'configuration/sensor_config' + str(i+1) + '.json', hosts = msnames, max_fail=3, clean_cmd=clean_cmd,
                   known_ips=ips, simulation=True, verbose=False, asid=asnames[i], msid=msnames[i], include_hosts=True, intf=psnames[i]+'-eth0'))
    [s.start() for s in sensors]
    #CLI(net)
    time.sleep(10)
    # Ping toward the sensor on the other subnet
    hosts = [net['h3'], net['h4'], net['h5'], net['h1'],net['h2'], net['h0'] ]
    net.ping(hosts=hosts)
    '''
    net['h3'].cmd('ping -c 1 192.168.1.102 ')  # hps1
    net['h4'].cmd('ping -c 1 192.168.1.102 ')  # hps1
    net['h5'].cmd('ping -c 1 192.168.1.102 ')  # hps1
    net['h1'].cmd('ping -c 1 192.168.2.102 ')  # hps2
    net['h2'].cmd('ping -c 1 192.168.2.102  ')  # hps2
    net['h0'].cmd('ping -c 1 192.168.2.102  ')  # hps2
    '''
    time.sleep(120)
    [s.stop() for s in sensors]
    servers[3].draw_topology(prefix = 'topo_exp1/', suffix = str(id))
    stop_blockchain(servers)

def experiment_two(id):
    '''
    Sets up NetworkTopo2 with two sensors.
    :param id: (Incremental) Identifier of the experiment
    :return: Saves the topology stored in the ledger in a file called print_topo[id].png
    '''
    servers = start_blockchain()
    (net, topo) = start_network_number(2, sensor1=True, sensor2=True)
    os.system('./init.sh')
    topo.create_alias_file()
    asnames = topo.active_sensors
    psnames = topo.passive_sensors
    msnames = topo.monitor_sensors
    startup(2, msnames, net)
    ips = get_responding_ips(msnames)
    sensors = []
    clean_cmd_base = 'rm -rf traceroute/'
    for i in range(len(psnames)):
        clean_cmd = [clean_cmd_base + msnames[i] + '/*']
        os.system('mkdir traceroute/' + msnames[i])
        sensors.append(sensor(psnames[i], len(msnames), net, 'configuration/sensor_config' + str(i+1) + '.json', hosts = msnames, max_fail=3, clean_cmd=clean_cmd,
                   known_ips=ips, simulation=True, verbose=False, asid=asnames[i], msid=msnames[i], include_hosts=True, intf=psnames[i]+'-eth0'))
    [s.start() for s in sensors]
    time.sleep(10)
    # Ping toward the sensor on the other subnet
    for i in range(10):
        hid = 'h' + str(i)
        net[hid].cmd('ping -c 2 192.168.2.102 ')  # hps2
    for i in range(10, 20):
        hid = 'h' + str(i)
        net[hid].cmd('ping -c 1 192.168.1.102 ')  # hps1
    time.sleep(240)
    for s in sensors:
        s.stop()
    servers[3].draw_topology(prefix = 'topo_exp2/', suffix = str(id))
    stop_blockchain(servers)

def experiment_three(id):
    '''
    Sets up NetworkTopo3 with two sensors.
    :param id: (Incremental) Identifier of the experiment
    :return: Saves the topology stored in the ledger in a file called print_topo[id].png
    '''
    servers = start_blockchain()
    (net, topo) = start_network_number(3, sensor1=True, sensor2=True)
    os.system('./init.sh')
    topo.create_alias_file()
    asnames = topo.active_sensors
    psnames = topo.passive_sensors
    msnames = topo.monitor_sensors
    startup(2, msnames, net)
    ips = get_responding_ips(msnames)
    sensors = []
    clean_cmd_base = 'rm -rf traceroute/'
    for i in range(len(psnames)):
        clean_cmd = [clean_cmd_base + msnames[i] + '/*']
        os.system('mkdir traceroute/' + msnames[i])
        sensors.append(sensor(psnames[i], len(msnames), net, 'configuration/sensor_config' + str(i+1) + '.json',
                              hosts = msnames, max_fail=3, clean_cmd=clean_cmd,  known_ips=ips, simulation=True, sleep_time = 30,
                              verbose=False, asid=asnames[i], msid=msnames[i], include_hosts=True, intf=psnames[i]+'-eth0'))
    [s.start() for s in sensors]
    time.sleep(10)
    # Ping toward the sensor on the other subnet
    for i in range(50):
        hid = 'h' + str(i)
        net[hid].cmd('ping -c 2 192.168.2.102 ')  # hps2
    for i in range(50, 100):
        hid = 'h' + str(i)
        net[hid].cmd('ping -c 1 192.168.1.102 ')  # hps1
    time.sleep(900)
    [s.stop() for s in sensors]
    [s.wait_end() for s in sensors]
    servers[3].draw_topology(prefix = 'topo_exp3/', suffix = str(id))
    stop_blockchain(servers)

def experiment_four(id, sensors, subfolder):
    '''
    Sets up NetworkTopo4.
    :param id: (Incremental) Identifier of the experiment
    :param sensors: list of boolean values telling which sensors have to be used
    :return: Saves the topology stored in the ledger in a file called print_topo[id].png
    '''
    servers = start_blockchain()
    (net, topo) = start_network_number(4, sensor1=sensors[0], sensor2=sensors[1], sensor3=sensors[2], sensor4=sensors[3])
    os.system('./init.sh')
    topo.create_alias_file()
    asnames = topo.active_sensors
    psnames = topo.passive_sensors
    msnames = topo.monitor_sensors
    sensors = []
    startup(len(msnames), msnames, net)
    ips = get_responding_ips(msnames)
    clean_cmd_base = 'rm -rf traceroute/'
    for i in range(len(psnames)):
        clean_cmd = [clean_cmd_base + msnames[i] + '/*']
        os.system('mkdir traceroute/' + msnames[i])
        sensors.append(sensor(psnames[i], len(msnames), net, 'configuration/sensor_config' + str(i + 1) + '.json',
                              hosts=msnames, max_fail=3, clean_cmd=clean_cmd, known_ips=ips, simulation=True,
                              sleep_time=30, subnets = '192.168.0.0/16 or 12.0.0.0/8',
                              verbose=False, asid=asnames[i], msid=msnames[i], include_hosts=True,
                              intf=topo.interface_name[i]))
    [s.start() for s in sensors]
    hosts = [net['h1'], net['h2'], net['h3'], net['h4'], net['h5'], net['h6'], net['h7'], net['h8']]
    time.sleep(10)
    print '\n\n ...............  PINGING   .............. \n\n'
    net.ping(hosts=hosts)
    time.sleep(150)
    [s.stop() for s in sensors]
    [s.wait_end() for s in sensors]
    servers[3].draw_topology(prefix='topo_exp4/' + subfolder + '/', suffix=str(id))
    stop_blockchain(servers)

def experiment_five(id, sensors, subfolder):
    '''
    Sets up NetworkTopo5.
    :param id: (Incremental) Identifier of the experiment
    :param sensors: list of boolean values telling which sensors have to be used
    :return: Saves the topology stored in the ledger in a file called print_topo[id].png
    '''
    servers = start_blockchain()
    (net, topo) = start_network_number(5, sensor1=sensors[0], sensor2=sensors[1], sensor3=sensors[2], sensor4=sensors[3])
    #CLI(net)
    os.system('./init.sh')
    topo.create_alias_file()
    asnames = topo.active_sensors
    psnames = topo.passive_sensors
    msnames = topo.monitor_sensors
    sensors = []
    startup(len(msnames), msnames, net)
    ips = get_responding_ips(msnames)
    topo.add_firewall_rules(net)
    clean_cmd_base = 'rm -rf traceroute/'
    for i in range(len(psnames)):
        clean_cmd = [clean_cmd_base + msnames[i] + '/*']
        os.system('mkdir traceroute/' + msnames[i])
        sensors.append(sensor(psnames[i], len(msnames), net, 'configuration/sensor_config' + str(i + 1) + '.json',
                              hosts=msnames, max_fail=3, clean_cmd=clean_cmd, known_ips=ips, simulation=True,
                              sleep_time=30, subnets = '192.168.0.0/16 or 12.0.0.0/8',
                              verbose=False, asid=asnames[i], msid=msnames[i], include_hosts=True,
                              intf=topo.interface_name[i]))
    [s.start() for s in sensors]
    hosts = [net['h1'], net['h2'], net['h3'], net['h4'], net['h5'], net['h6'], net['h7'], net['h8']]
    time.sleep(10)
    print '\n\n ...............  PINGING   .............. \n\n'
    net.ping(hosts=hosts)
    time.sleep(200)
    [s.stop() for s in sensors]
    [s.wait_end() for s in sensors]
    servers[3].draw_topology(prefix='topo_exp5/' + subfolder + '/', suffix=str(id))
    stop_blockchain(servers)

def experiment_six(id, sensors, subfolder):
    '''
    Sets up NetworkTopo6.
    :param id: (Incremental) Identifier of the experiment
    :param sensors: list of boolean values telling which sensors have to be used
    :return: Saves the topology stored in the ledger in a file called print_topo[id].png
    '''
    servers = start_blockchain()
    (net, topo) = start_network_number(6, sensor1=sensors[0], sensor2=sensors[1], sensor3=sensors[2])
    os.system('./init.sh')
    topo.create_alias_file()
    asnames = topo.active_sensors
    psnames = topo.passive_sensors
    msnames = topo.monitor_sensors
    sensors = []
    startup(len(msnames), msnames, net)
    ips = get_responding_ips(msnames)
    clean_cmd_base = 'rm -rf traceroute/'
    for i in range(len(psnames)):
        clean_cmd = [clean_cmd_base + msnames[i] + '/*']
        os.system('mkdir traceroute/' + msnames[i])
        sensors.append(sensor(psnames[i], len(msnames), net, 'configuration/sensor_config' + str(i + 1) + '.json',
                              hosts=msnames, max_fail=3, clean_cmd=clean_cmd, known_ips=ips, simulation=True,
                              sleep_time=30, subnets = '192.168.0.0/16 or 12.0.0.0/8',
                              verbose=False, asid=asnames[i], msid=msnames[i], include_hosts=True,
                              intf=topo.interface_name[i]))
    [s.start() for s in sensors]
    hosts = [net['h1'], net['h2'], net['h3'], net['h4'], net['h5'], net['h6'], net['h7'], net['h8'], net['h9']]
    time.sleep(10)
    print '\n\n ...............  PINGING   .............. \n\n'
    net.ping(hosts=hosts)
    time.sleep(150)
    [s.stop() for s in sensors]
    [s.wait_end() for s in sensors]
    servers[3].draw_topology(prefix='topo_exp6/' + subfolder + '/', suffix=str(id))
    stop_blockchain(servers)

def experiment_seven(id, sensors, subfolder):
    '''
    Sets up NetworkTopo7.
    :param id: (Incremental) Identifier of the experiment
    :param sensors: list of boolean values telling which sensors have to be used
    :return: Saves the topology stored in the ledger in a file called print_topo[id].png
    '''
    servers = start_blockchain()
    (net, topo) = start_network_number(7, sensor1=sensors[0], sensor2=sensors[1], sensor3=sensors[2])
    os.system('./init.sh')
    topo.create_alias_file()
    asnames = topo.active_sensors
    psnames = topo.passive_sensors
    msnames = topo.monitor_sensors
    sensors = []
    startup(len(msnames), msnames, net)
    ips = get_responding_ips(msnames)
    topo.add_firewall_rules(net)
    #CLI(net)
    clean_cmd_base = 'rm -rf traceroute/'
    for i in range(len(psnames)):
        clean_cmd = [clean_cmd_base + msnames[i] + '/*']
        os.system('mkdir traceroute/' + msnames[i])
        sensors.append(sensor(psnames[i], len(msnames), net, 'configuration/sensor_config' + str(i + 1) + '.json',
                              hosts=msnames, max_fail=3, clean_cmd=clean_cmd, known_ips=ips, simulation=True,
                              sleep_time=30, subnets = '192.168.0.0/16 or 12.0.0.0/8',
                              verbose=False, asid=asnames[i], msid=msnames[i], include_hosts=True,
                              intf=topo.interface_name[i]))
    [s.start() for s in sensors]
    hosts = [net['h1'], net['h2'], net['h3'], net['h4'], net['h5'], net['h6'], net['h7'], net['h8'], net['h9']]
    net['h7'].cmd('ping -c 1 -W 1 ' + net['h1'].IP())
    net['h8'].cmd('ping -c 1 -W 1 ' + net['h1'].IP())
    net['h9'].cmd('ping -c 1 -W 1 ' + net['h1'].IP())
    net['h4'].cmd('ping -c 1 -W 1 ' + net['h1'].IP())
    net['h5'].cmd('ping -c 1 -W 1 ' + net['h1'].IP())
    net['h6'].cmd('ping -c 1 -W 1 ' + net['h1'].IP())
    time.sleep(10)
    print '\n\n ...............  PINGING   .............. \n\n'
    net.ping(hosts=hosts)
    time.sleep(200)
    [s.stop() for s in sensors]
    [s.wait_end() for s in sensors]
    servers[3].draw_topology(prefix='topo_exp7/' + subfolder + '/', suffix=str(id))
    stop_blockchain(servers)

def experiment_eight(id, sensors, subfolder):
    '''
    Sets up NetworkTopo8.
    :param id: (Incremental) Identifier of the experiment
    :param sensors: list of boolean values telling which sensors have to be used
    :return: Saves the topology stored in the ledger in a file called print_topo[id].png
    '''
    #servers = start_blockchain()
    (net, topo) = start_network_number(8, sensor1=sensors[0], sensor2=sensors[1], sensor3=sensors[2], sensor4=sensors[3])
    os.system('./init.sh')
    topo.create_alias_file()
    asnames = topo.active_sensors
    psnames = topo.passive_sensors
    msnames = topo.monitor_sensors
    sensors = []
    startup(len(msnames), msnames, net)
    ips = get_responding_ips(msnames)
    topo.add_firewall_rules(net)
    clean_cmd_base = 'rm -rf traceroute/'
    for i in range(len(psnames)):
        clean_cmd = [clean_cmd_base + msnames[i] + '/*']
        os.system('mkdir traceroute/' + msnames[i])
        sensors.append(sensor(psnames[i], len(msnames), net, 'configuration/sensor_config' + str(i + 1) + '.json',
                              hosts=msnames, max_fail=3, clean_cmd=clean_cmd, known_ips=ips, simulation=True,
                              sleep_time=30, subnets = '192.168.0.0/16 or 12.0.0.0/8',
                              verbose=False, asid=asnames[i], msid=msnames[i], include_hosts=True,
                              intf=topo.interface_name[i]))
    [s.start() for s in sensors]
    hosts = [net['h1'], net['h2'], net['h3'], net['h4'], net['h5'], net['h6'], net['h7'], net['h8']]
    net['h3'].cmd('ping -c 1 -W 1 ' + net['h1'].IP())
    net['h4'].cmd('ping -c 1 -W 1 ' + net['h1'].IP())
    time.sleep(10)
    print '\n\n ...............  PINGING   .............. \n\n'
    net.ping(hosts=hosts)
    time.sleep(200)
    [s.stop() for s in sensors]
    [s.wait_end() for s in sensors]
    servers[3].draw_topology(prefix='topo_exp8/' + subfolder + '/', suffix=str(id))
    stop_blockchain(servers)

def experiment_nine(id, sensors, subfolder):
    '''
    Sets up NetworkTopo9.
    :param id: (Incremental) Identifier of the experiment
    :param sensors: list of boolean values telling which sensors have to be used
    :return: Saves the topology stored in the ledger in a file called print_topo[id].png
    '''
    servers = start_blockchain()
    (net, topo) = start_network_number(9, sensor1=sensors[0], sensor2=sensors[1], sensor3=sensors[2], sensor4=sensors[3])
    os.system('./init.sh')
    topo.create_alias_file()
    asnames = topo.active_sensors
    psnames = topo.passive_sensors
    msnames = topo.monitor_sensors
    sensors = []
    startup(len(msnames), msnames, net)
    ips = get_responding_ips(msnames)
    topo.add_firewall_rules(net)
    clean_cmd_base = 'rm -rf traceroute/'
    for i in range(len(psnames)):
        clean_cmd = [clean_cmd_base + msnames[i] + '/*']
        os.system('mkdir traceroute/' + msnames[i])
        sensors.append(sensor(psnames[i], len(msnames), net, 'configuration/sensor_config' + str(i + 1) + '.json',
                              hosts=msnames, max_fail=3, clean_cmd=clean_cmd, known_ips=ips, simulation=True,
                              sleep_time=30, subnets = '192.168.0.0/16 or 12.0.0.0/8',
                              verbose=False, asid=asnames[i], msid=msnames[i], include_hosts=True,
                              intf=topo.interface_name[i]))
    [s.start() for s in sensors]
    hosts = [net['h1'], net['h2'], net['h3'], net['h4'], net['h5'], net['h6'], net['h7'], net['h8']]
    net['h3'].cmd('ping -c 1 -W 1 ' + net['h1'].IP())
    net['h4'].cmd('ping -c 1 -W 1 ' + net['h1'].IP())
    time.sleep(10)
    print '\n\n ...............  PINGING   .............. \n\n'
    net.ping(hosts=hosts)
    time.sleep(200)
    [s.stop() for s in sensors]
    [s.wait_end() for s in sensors]
    servers[3].draw_topology(prefix='topo_exp9/' + subfolder + '/', suffix=str(id))
    stop_blockchain(servers)

if __name__ == '__main__':
    args = parse_cmd_args()
    num = args.num
    id = args.id
    s1 = args.sensor1
    s2 = args.sensor2
    s3 = args.sensor3
    s4 = args.sensor4
    sub = args.subfolder
    if num == 1:
        experiment_one(id)
    elif num == 2:
        experiment_two(id)
    elif num == 3:
        experiment_three(id)
    elif num == 4:
        experiment_four(id, [s1, s2, s3, s4], subfolder=sub)
    elif num == 5:
        experiment_five(id, [s1, s2, s3, s4], subfolder=sub)
    elif num == 6:
        experiment_six(id, [s1, s2, s3], subfolder=sub)
    elif num == 7:
        experiment_seven(id, [s1, s2, s3], subfolder=sub)
    elif num == 8:
        experiment_eight(id, [s1, s2, s3, s4], subfolder=sub)
    elif num == 9:
        experiment_nine(id, [s1, s2, s3, s4], subfolder=sub)






