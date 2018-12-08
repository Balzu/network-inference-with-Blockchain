# coding=utf-8

import subprocess
import re, os, sys, pdb, time
topo_path = os.path.abspath(os.path.join('..', '..', 'Topology'))
sys.path.insert(0, topo_path)
from util import *
from create_merge_topo import *
from build_virtual_topo import *
import logging
from threading import Lock
from datetime import datetime


class sensor(object):

    lock=Lock()

    def __init__(self, id, nh, net, config_file, hosts=[], active = True, passive = True, full = False, ignored_ips=[],
                 known_ips = [], max_fail = 5, simulation=False, readmit=True, verbose=False, interactive=False,
                 include_hosts=False, asid=None, msid=None, intf = 'any', clean_cmd = [], sleep_time = 10,
                 subnets = '192.168.0.0/16', nrr=True, pattern='', **pattern_params):
        '''
        :param id: the id of this sensor. It must be the ID of the node on which the sensor is placed.
        :param nh: the number of hosts (monitors) to be used when they are chosen randomly to run iTop(if hosts=[])
        :param net: Mininet network reference
        :param config_file: Configuration file for the blockchain client run by this sensor
        :param hosts: the list of hosts (monitors) to be used to run iTop
        :param active: tell whether the sensor should have active capabilities (e.g. ping)
        :param passive: tell whether the sensor should have passive capabilities (sniff traffic)
        :param full: if False, run iTop with reduced monitors selection; else run iTop with all available monitors
        :param ignored_ips: list of ips that the sensor should ignore (ex.: the hosts that do not belong to topology)
        :param known_ips: list of known ips. Could even start a sensor with empty list
        :param max_fail: maximum number of consecutive PING failures that is tollerated before declaring a node dead
        :param simulation: True if the sensor has to be run on a Mininet host. The active sensor capabilities change.
        :param readmit: If set to False, an ip will never be readmitted in the topology after it has been declared
               'dead'. Set to False when the sensor is used in Mininet. Default: 'True'.
        :param verbose: Set True if you wish to print verbose information
        :param interactive: If the sensor is run in interactive mode, the stop signal can be sent via user input.
        :param include_hosts: When collecting traces, consider also final hosts
        :param asid: Active Sensor ID. Used when the simulation is run on Mininet. In that case, the active and the
                passive sensor capabilities may be run on two different hosts. This happens if asid is different from None.
        :param msid: Monitor Sensor ID. Used when the simulation is run on Mininet. In that case, the sensor uses a
                third, dedicated host to run the topology inference algorithm (only one command at a time can be run on
                Mininet hosts..)
        :param intf: Capture interface. Default: any.
        :param clean_cmd: List of commands to be executed by this sensor to clean previously generated traces
        :param sleep_time: time to wait before the next cycle of alive/dead nodes checks is started from the sensor
        :param subnets: The network or combination of networks to which packet sniffing is restricted to (only applies if simulation=True)
        :param nrr: Set to False if you want to skip Non Responding Routers (NRR) from the topology. The transactions
               are rearranged to reflect this modification to the topology.
        :param pattern: The pattern to which the induced topology should fit
        :param **pattern_params: The parameters passed to manage the specific pattern
        '''
        setup_logger('sensor ' + id + '.log', 'sensor ' + id + '.log')
        self.__logger = logging.getLogger('sensor ' + id + '.log')
        self.__id = id
        self.__active = active
        self.__passive = passive
        self.__full = full
        self.__known_ips = list(known_ips)
        self.__fail_count = {} # Counts the number of unsuccessful, consecutive ping replies for each known ip
        for ip in known_ips:
            self.__fail_count[ip] = 0
        self.__max_fail = max_fail
        self.__end = False # Flag to tell sensor to end
        self.__ended = False # Flag set to True when the sensor really ended
        self.__simulation = simulation
        self.__verbose = verbose
        self.__readmit = readmit
        self.__dead = [] # Updated when found a dead node. Set empty soon after the dead node has been managed.
        self.__banned = ignored_ips
        self.__new = [] # Updated when found a new node. Set empty soon after the new node has been managed.
        self.__nh = nh
        self.__hosts = hosts
        self.__net = net
        self.__interactive = interactive
        self.__with_hosts = include_hosts
        self.__asid = asid if asid is not None else id
        self.__msid = msid # If msid is different from None, run iTop using only this (monitor) sensor as source
        self.__alias = create_alias()
        self.__intf = intf
        self.__clean_cmd = clean_cmd
        self.__intercycles_time = sleep_time
        self.__subnets = subnets
        self.__nrr = nrr
        self.__pattern = pattern
        self.__pattern_params = pattern_params
        self.__c = configure_client(config_file)
        register_client(self.__c)
        #self.impose_pattern() #TODO
#TODO conviene avere metodi synchronized per accedere in scrittura a S.D. condivise


    def start(self):
        ''' Starts the sensor.'''
        if self.__passive:
            if self.__simulation:
                threading.Thread(target=self.passive_sensor_on_Mininet).start()
            else:
                threading.Thread(target=self.passive_sensor).start()
        if self.__active:
            if self.__simulation:
                threading.Thread(target=self.active_sensor_on_mininet).start()
            else:
                threading.Thread(target=self.active_sensor).start()
        threading.Thread(target=self.run).start()
        if self.__interactive: threading.Thread(target=self.wait_user_input).start()

    def run(self):
        while not self.__end:
            if self.__active:
                self.check_dead_nodes()
            if self.__passive:
                self.check_new_nodes()
            time.sleep(self.__intercycles_time)
        self.__ended = True

    def active_sensor(self):
        '''Runs active sensor capabilities'''
        while not self.__end:
            for ip in self.__known_ips:
                try:
                    p = subprocess.Popen(['ping', '-c', '1', '-W', '1', ip], stdout=subprocess.PIPE)
                    stdout, stderr = p.communicate()
                    result = p.returncode
                    if result != 0: # Not received correct reply
                        self.handle_unsuccessful_ping(ip)
                    else:
                        self.__fail_count[ip] = 0
                except subprocess.CalledProcessError:
                    print 'Error with the ping subprocess'
            time.sleep(5)

    def active_sensor_on_mininet(self):
        '''Runs active sensor capabilities on a Mininet host'''
        while not self.__end:
            for ip in self.__known_ips:
                s = self.__net[self.__asid]
                result = s.cmd('ping -c 1 -W 1 ' + ip + ' | grep received |  awk \'{print $4}\'') #TODO cmd and not sendCmd
                if self.__verbose: print 'PING ' + s.IP() + ' -> ' + ip + ' : ' + result.rstrip() + '/1 pacchetti ricevuti correttamente\n'
                try:
                    if int(result) != 1: # Not received the correct packet back
                        self.handle_unsuccessful_ping(ip)
                    else:
                        self.__fail_count[ip] = 0
                        if self.__verbose: print '\nAfter Success, Fail count for ' + ip + '= ' + str(self.__fail_count[ip])
                except ValueError:
                    self.handle_unsuccessful_ping(ip)
            time.sleep(5)

    def handle_unsuccessful_ping(self, ip):
        #pdb.set_trace()
        try:
            self.__fail_count[ip] = self.__fail_count[ip] + 1
            if self.__verbose:  print '\n' + self.__msid + ' : Fail count for ' + ip + ' = ' + str(self.__fail_count[ip])
            if self.__fail_count[ip] > self.__max_fail:
                self.__dead.append(ip)
                if not self.__readmit:
                    self.__banned.append(ip)
                    print '\nBanned ' + ip
                self.__known_ips.remove(ip)
                del self.__fail_count[ip]
        except KeyError:
            self.__logger.info('Key error due to ip ' + ip)

    def passive_sensor_on_Mininet(self):
        '''Runs passive sensor capabilities'''
        # Limitazione sulla sottorete se topologia simulata su Mininet. Problema: tcpdump non filtra sia dst che dst network
        tcpdump_cmd = 'sudo timeout 30 tcpdump -l -i ' + self.__intf + ' net ' + self.__subnets + ' >> tcpdump_out'+ self.__id if self.__simulation \
                else 'sudo timeout 30 tcpdump -l -i ' + self.__intf + ' >> tcpdump_out'+ self.__id #TODO TWEAK TIMEOUT '-i', self.__id + '-eth0
        s = self.__net[self.__id]
        threading.Thread(target=self.blocking_cmd_on_Mininet_host, args=(tcpdump_cmd, s,)).start()
        time.sleep(3)
        with open('tcpdump_out'+self.__id, 'r') as file:
            while not self.__end:
                line = file.readline()
                while line != '': # Sensor wrote something there..
                    try:
                        src_ip = line.split()[2]
                        #dst_ip = line.split()[4]
                        s_match = re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", src_ip)
                        #d_match = re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", dst_ip)
                        if s_match:
                            self.handle_match(self.clean_ip(src_ip))
                        #if d_match:
                        #    self.handle_match(self.clean_ip(dst_ip))
                    except IndexError:
                        pass # 'Invalid output from tcpdump'
                    line = file.readline()
                time.sleep(2)

    #TODO sembra che 2 comandi allo stesso host causino errore
    def blocking_cmd_on_Mininet_host(self, command, host):
        '''
        Runs a blocking command (with a TIMEOUT) on a Mininet host using a separate thread of execution.
        Must use if the non blocking sendCmd() causes assertion error.
        '''
        self.__logger.info('Cmd: ' + command)
        while not self.__end:
            host.cmd(command)
        print '\n\nEXITING PASSIVE THREAD\n\n'


    def passive_sensor(self):
        '''Runs passive sensor capabilities'''
        # Limitazione sulla sottorete se topologia simulata su Mininet. Problema: tcpdump non filtra sia dst che dst network
        cmd = ['sudo', 'tcpdump', '-l', '-i', 'any', 'net', '192.168.0.0/16'] if self.__simulation \
            else ['sudo', 'tcpdump', '-l', '-i', 'any']
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        print '------------------- START SNIFFING ----------------------'
        for row in iter(p.stdout.readline, b''):
            try:
                src_ip = row.split()[2]
                #dst_ip = row.split()[4] #TODO tolto indirizzo IP destinazione: non è detto che quell' host esista/sia raggiungibile
                s_match = re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", src_ip)
                #d_match = re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", dst_ip)
                if s_match:
                    self.handle_match(self.clean_ip(src_ip))
                #if d_match:
                #    self.handle_match(self.clean_ip(dst_ip))
            except IndexError:
                print 'Invalid output from tcpdump'
            if self.__end:
                p.terminate()
                break

    def handle_match(self, ip):
        if ip not in self.__banned:
            if ip not in self.__known_ips:
                # Further check, only in case of simulation (limited to subnet 192.168)
                #TODO nei precedenti test c'era l' if, controlla se è sempre ok
                #if (not self.__simulation or (int(ip.split('.')[0])==192 and int(ip.split('.')[1])==168)):
                print '\nNew IP discovered: ' + ip
                self.__new.append(ip)
                self.__known_ips.append(ip)
                self.__fail_count[ip] = 0
                self.__logger.info(datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' : New IP discovered by ' + self.__id + ' : ' + ip)
            #TODO The passive sensor could be used to reset the fail count. It is sufficient to move the last line
            #of the function after the second if (not inside). (now this functionality is disabled, because
            # MIninet has switches that send IP packets but do not respond to ping, and that definetely should not
            # belong to topology)

    def check_new_nodes(self):
        '''Checks whether the passive sensor found traffic dealing with a new, unknown host.
        In such a case, run a new instance of iTop and update the topology in the ledger.'''
        new = list(self.__new)
        if (len(new)) != 0:
            res = False
            if (not self.__full) and (not self.__with_hosts): # fastiTop was tested to work only with routers
                (res, out) = self.fastiTop(self.__new)
            if self.__full or res == False: # if fastiTop is not run it is guaranteed that full iTop is run
                out = self.fulliTop()
            topo = get_topo_from_json(out)
            trans = get_transactions_from_topo(topo) if self.__nrr else create_transactions_for_compacted_topo(topo)
            self.__c.send_transactions(trans)
        self.__new = list(set(self.__new) - set(new)) # In the meantime some new IP could have arrived..


    def check_dead_nodes(self):
        '''Checks whether the active sensor discovered a dead node (ip address non responding to ping for more
        than max times). In that case, tell the Blockchain servers that such a node no longer exists.'''
        trans = []
        for n in self.__dead:
            print '\nDead node: ' + n + '\n'
            try:
                tx = transaction(topology_node(self.__alias[n], 'R'), None, False)
                trans.append(tx)
            except KeyError:
                print '\n' + n + ' does not belong to the topology\n' # Only because we are in a simulation
                self.__dead.remove(n)
        if len(trans) > 0:
            self.__c.send_transactions(trans)
            self.__dead = []
            self.__full = True # Previously gathered traces are no longer valid -> a full run of iTop is required

    def clean_ip(self, raw_ip):
        'Clean the ip. A slightly different cleaning is done based on whether the ip is source or destination.'
        #bytes = raw_ip.split('.')
        bytes = re.split('\.|:', raw_ip)
        return bytes[0] + '.' + bytes[1] + '.' + bytes[2] + '.' + bytes[3]

    def wait_user_input(self):
        while not self.__end:
            #TODO if received user input to stop, stop the sensor. Migliora interfaccia di stop
            choice = raw_input("Type 'Q' to quit the sensor.\n")
            if choice =='Q' or choice == 'q':
                self.stop()


    def fulliTop(self):
        '''
        Runs iTop on the existing topology with all available monitors and returns the filename of the induced topology.
        '''
        # If a simulation involves final hosts, the commands on the hosts must be executed sequentially
        if self.__simulation and self.__with_hosts: sensor.lock.acquire()
        self.clean_traces()
        self.__logger.info('Run full iTop')
        hosts = self.__hosts
        if len(self.__hosts) == 0:
            hosts = get_hosts(int(self.__nh))
        if self.__with_hosts: hosts = self.ips_alias(hosts)
        self.__logger.info('full iTop hosts: ')
        for h in hosts:
            self.__logger.info(h)
        create_traces(self.__net, hosts, src_hosts=[self.__msid], suffix=self.__msid+'/') if self.__msid is not None else \
            create_traces(self.__net, hosts, suffix=self.__msid+'/') # TODO: Non c'era create traces prima
        if self.__msid is not None:
            (vtopo, traces) = create_virtual_topo_and_traces(self.__alias, hosts, src_hosts=[self.__msid], include_host=self.__with_hosts, suffix=self.__msid+'/')
        else:
            (vtopo, traces) = create_virtual_topo_and_traces(self.__alias, hosts, include_host=self.__with_hosts, suffix=self.__msid+'/')
        (M, C) = create_merge_options(vtopo, traces)
        (M, mtopo) = create_merge_topology(M, vtopo, C)
        out = write_topo_to_file(self.__id, mtopo, hosts)
        self.__full = False
        if sensor.lock.locked(): sensor.lock.release()
        return out

    def fastiTop(self, nnodes):
        '''
         Runs iTop with a reduced set of hosts, based on previous inferred topology.
        :return: a pair (result, topology_filename). result is True if the inferred topology is considered satisfying,
         False if a full run of iTop has instead to be done. (Some already known nodes were not discovered..)
        '''
        if self.__simulation and self.__with_hosts: sensor.lock.acquire()
        hosts = previous_hosts()
        alias = create_alias()
        # Reconstruct old topology
        #src_hosts = [self.__msid] if self.__msid is not None else []
        (M, old_topo, traces) = get_old_topo(hosts, alias) #, src_hosts = src_hosts, include_host=self.__with_hosts)
        # Reconstruct new_topo
        src_pairs = find_sources(traces,
                                 monitors=True)  # Returns a pair because the monitor does not belong to topology
        C = compute_monitors_coverage(src_pairs, old_topo, hosts)
        shosts = monitors_selection(C, old_topo)
        # Infer the (new) topology using the (optimal ?) selection of probing stations
        compute_distances(self.__net, hosts, src_hosts=shosts)
        create_traces(self.__net, hosts, src_hosts=shosts, suffix=self.__msid+'/')
        (vtopo, traces) = create_virtual_topo_and_traces(alias, hosts, src_hosts=shosts, suffix=self.__msid+'/')
        '''
        if self.__msid is not None: #TODO CHECK!!!
            (vtopo, traces) = create_virtual_topo_and_traces(self.__alias, hosts, src_hosts=[self.__msid], include_host=self.__with_hosts)
        else:
            (vtopo, traces) = create_virtual_topo_and_traces(self.__alias, hosts, include_host=self.__with_hosts)
        '''
        (M, C) = create_merge_options(vtopo, traces)
        (M, new_topo) = create_merge_topology(M, vtopo, C)
        if sensor.lock.locked(): sensor.lock.release() #Run of iTop ended
        # Compare the old topology against the new one, to see if the gathered traces are enough or all monitors must be used.
        nnalias = []
        for n in nnodes:
            try:
                nnalias.append(alias[n])
            except KeyError:
                print '\n' + n + ' does not belong to the topology, its alias does not exist\n'
        end = compare_topologies(old_topo, new_topo, new_nodes = nnalias)
        if end:
            out = write_topo_to_file(self.__id, new_topo, shosts)
            self.__logger.info('Fast iTop successfully used')
            return (True, out)
        return (False, None)

    def impose_pattern(self):
        '''
        Generates the pattern-specific transactions and sends them to the Blockchain
        '''
        trans = self.pattern_transactions()
        if len(trans) > 0: self.__c.send_transactions(trans)


    def pattern_transactions(self):
        '''
        Returns a list of transactions to be sent to Blockchain nodes to fit the induced topology to the pattern
        :return: List of transactions
        '''
        if self.__pattern == 'tree':
            return self.tree_pattern_transactions()
        else: #TODO each different pattern has a specific handler. Put here a series of 'elif'...
            return []

    def tree_pattern_transactions(self):
        '''
        Returns the pair of transactions needed to fit the induced topology to a tree topology:
        Root -> Child and Child -> Root.
        If Root_IP is specified, the transactions are added only if Root_IP is not a known host, else if Root_IP
        is not specified the transactions are added anyway.
        If child_IP is specified, the child node is the one specified, otherwise we assume this sensor to be the
        child of the root.
        :return: List of two transactions
        '''
        #TODO: va controllato cosa succede se un sensore 'trova' la radice e un altro no
        # After retrieving the 'names' of the nodes, we insert in the Blockchain the transactions Root -> Child and Child -> Root
        root_IP = self.__pattern_params['root_IP'] if 'root_IP' in self.__pattern_params else ''
        child_IP = self.__pattern_params['child_IP'] if 'child_IP' in self.__pattern_params else ''
        if root_IP is not '':
            if root_IP in self.__known_ips:
                return [] # Nothing to do, we already discovered the root
            else:
                alias = create_alias()
                root = topology_node(alias[root_IP], 'P') if root_IP in alias else topology_node('ROOT', 'P')
        else:
            root = topology_node('ROOT', 'P')
        if child_IP is not '':
            alias = create_alias()
            if child_IP in self.__known_ips:
                child = topology_node(alias[child_IP], 'R') if child_IP in alias else topology_node(self.__msid, 'R')
            else:
                child = topology_node(alias[child_IP], 'P') if child_IP in alias else topology_node(self.__msid, 'R')
        else:
            child = topology_node(self.__msid, 'R')
        trx1 = transaction(child, root)
        trx2 = transaction(root, child)
        return [trx1, trx2]


    def ips_alias(self, hosts):
        '''
        Scans the known_ips + host list to create a list of alias. If an IP has no known alias, it does not insert that
        IP in the returned list.
        '''
        alias = create_alias()
        shosts = set()
        for ip in self.__known_ips:
            try:
                a = alias[ip]
                shosts.add(a)
            except KeyError:
                pass # If an IP has no alias, we simply do not return it
        shosts.union(set(hosts)) # Hosts are already aliased
        return list(shosts)

    def clean_traces(self):
        '''
        Runs commands to clean the previously generated traces.
        '''
        if self.__clean_cmd == []:
            os.system('./init.sh')  # Clean traces: use default script
        else:
            for c in self.__clean_cmd:
                os.system(c)

    #TODO lo stoppi in questo modo? Considera se devi proteggere variabili con lock o no
    def stop(self):
        # TODO pattern viene imposto prima di stoppare il sensore per comodità di simulazione, potresti farlo quando vuoi
        #if self.__pattern is not '' : self.impose_pattern()
        self.__end = True

    def wait_end(self):
        while not self.__ended:
            time.sleep(5)

