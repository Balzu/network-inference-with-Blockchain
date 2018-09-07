# coding=utf-8

import subprocess
import re
import pdb
from util import *
from create_merge_topo import *

class sensor(object):

    def __init__(self, id, nh, net, config_file, hosts=[], active = True, passive = True,
                 known_ips = [], max_fail = 5, simulation = False, readmit = True):
        '''
        :param id: the id of this sensor. It must be the ID of the node on which the sensor is placed.
        :param nh: the number of hosts (monitors) to be used when they are chosen randomly to run iTop(if hosts=[])
        :param net: Mininet network reference
        :param config_file: Configuration file for the blockchain client run by this sensor
        :param hosts: the list of hosts (monitors) to be used to run iTop
        :param active: tell whether the sensor should have active capabilities (e.g. ping)
        :param passive: tell whether the sensor should have passive capabilities (sniff traffic)
        :param known_ips: list of known ips. Could even start a sensor with empty list
        :param max_fail: maximum number of consecutive PING failures that is tollerated before declaring a node dead
        :param simulation: True if the sensor has to be run on a Mininet host. The active sensor capabilities change.
        :param readmit: If set to False, an ip will never be readmitted in the topology after it has been declared
               'dead'. Set to False when the sensor is used in Mininet. Default: 'True'.
        '''
        self.__id = id
        self.__active = active
        self.__passive = passive
        self.__known_ips = known_ips
        self.__fail_count = {} # Counts the number of unsuccessful, consecutive ping replies for each known ip
        for ip in known_ips:
            self.__fail_count[ip] = 0
        self.__max_fail = max_fail
        self.__end = False
        self.__simulation = simulation
        self.__readmit = readmit
        self.__dead = [] # Updated when found a dead node. Set empty soon after the dead node has been managed.
        self.__banned = []
        self.__new = [] # Updated when found a new node. Set empty soon after the new node has been managed.
        self.__nh = nh
        self.__hosts = hosts
        self.__net = net
        self.__alias = create_alias()
        self.__c = configure_client(config_file)
        #pdb.set_trace()
        register_client(self.__c)
#TODO conviene avere metodi synchronized per accedere in scrittura a S.D. condivise


    def start(self):
        ''' Starts the sensor.'''
        if self.__active:
            if self.__simulation:
                threading.Thread(target=self.active_sensor_on_mininet).start()
            else:
                threading.Thread(target=self.active_sensor).start()
        if self.__passive:
            threading.Thread(target=self.passive_sensor).start()
        threading.Thread(target=self.run).start()
        threading.Thread(target=self.wait_user_input).start()


    def run(self):
        while not self.__end:
            if self.__active:
                self.check_dead_nodes()
            if self.__passive:
                self.check_new_nodes()
            time.sleep(10)

    def active_sensor(self):
        '''Runs active sensor capabilities'''
        while not self.__end:
            for ip in self.__known_ips:
                try:
                    p = subprocess.Popen(['ping', '-c', '1', ip], stdout=subprocess.PIPE)
                    stdout, stderr = p.communicate()
                    result = p.returncode
                    if result != 0: # Not received correct reply
                        self.handle_unsuccessful_ping(ip)
                    else:
                        self.__fail_count[ip] = 0
                except subprocess.CalledProcessError:
                    print 'Error with the ping subprocess'
            time.sleep(10)

    def active_sensor_on_mininet(self):
        '''Runs active sensor capabilities on a Mininet host'''
        while not self.__end:
            for ip in self.__known_ips:
                #pdb.set_trace()
                s = self.__net[self.__id]
                result = s.cmd('ping -c 1 ' + ip + ' | grep received |  awk \'{print $4}\'')
                print 'PING ' + s.IP() + ' -> ' + ip + ' : ' + result.rstrip() + '/1 pacchetti ricevuti correttamente\n'
                try:
                    if int(result) != 1: # Not received the correct packet back
                        self.handle_unsuccessful_ping(ip)
                    else:
                        print self.__fail_count
                        self.__fail_count[ip] = 0
                        print '\nAfter Success, Fail count for ' + ip + '= ' + str(self.__fail_count[ip])
                        print self.__fail_count
                except ValueError:
                    self.handle_unsuccessful_ping(ip)
            time.sleep(10)

    def handle_unsuccessful_ping(self, ip):
        self.__fail_count[ip] = self.__fail_count[ip] + 1
        print '\nFail count for ' + ip + ' = ' + str(self.__fail_count[ip])
        if self.__fail_count[ip] > self.__max_fail:
            self.__dead.append(ip)
            if not self.__readmit:
                self.__banned.append(ip)
                print '\nBanned ' + ip
            self.__known_ips.remove(ip)
            del self.__fail_count[ip]

    def passive_sensor(self):
        '''Runs passive sensor capabilities'''
        # Limitazione sulla sottorete se topologia simulata su Mininet
        cmd = ['sudo', 'tcpdump', '-l', '-i', 'any', 'net',  '192.168.0.0/16'] if self.__simulation \
                else ['sudo', 'tcpdump', '-l', '-i', 'any']
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        print '------------------- START SNIFFING ----------------------'
        for row in iter(p.stdout.readline, b''):
            src_ip = row.split()[2]
            dst_ip = row.split()[4]
            s_match = re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", src_ip)
            d_match = re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", dst_ip)
            if s_match:
                self.handle_match(self.clean_ip(src_ip))
            if d_match:
                self.handle_match(self.clean_ip(dst_ip))
            if self.__end:
                p.terminate()
                break

    def handle_match(self, ip):
        if ip not in self.__banned:
            if ip not in self.__known_ips:
                print '\nNew IP discovered: ' + ip
                self.__new.append(ip)
                self.__known_ips.append(ip)
                self.__fail_count[ip] = 0
            #TODO Thw passive sensor could be used to reset the fail count. It is sufficient to move the last line
            #of the function after the second if (not inside). Anyway, now this functionality is disabled, because
            # MIninet has switches that send IP packets but do not respond to ping, and that definetely should not
            # belong to topology

    def check_new_nodes(self):
        '''Checks whether the passive sensor found traffic dealing with a new, unknown host.
        In such a case, run a new instance of iTop and update the topology in the ledger.'''
        if (len(self.__new)) != 0:
            out = self.iTop()
            topo = get_topo_from_json(out)
            trans = get_transactions_from_topo(topo)
            self.__c.send_transactions(trans)
        self.__new = []

    def check_dead_nodes(self):
        '''Checks whether the active sensor discovered a dead node (ip address non responding to ping for more
        than max times). In that case, tell the Blockchain servers that such a node no longer exists.'''
        trans = []
        for n in self.__dead:
            print '\nDead node: ' + n + '\n'
            try:
                tx = transaction(self.__alias[n], None)
                trans.append(tx)
            except KeyError:
                print '\n' + n + ' does not belong to the topology\n' # Only because we are in a simulation
                self.__dead.remove(n)
            #finally:
            #    if not self.__readmit:
            #        self.__banned.append(n)
            #        print '\nBanned ' + n
        if len(trans) > 0:
            self.__c.send_transactions(trans)
            self.__dead = []

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


    def iTop(self):
        '''Runs iTop on the existing topology and returns the filename of the induced topology.'''
        hosts = self.__hosts
        if len(self.__hosts) == 0:
            hosts = get_hosts(int(self.__nh))
        (vtopo, traces) = create_virtual_topo_and_traces(self.__alias, hosts)
        (M, C) = create_merge_options(vtopo, traces)
        (M, mtopo) = create_merge_topology(M, vtopo, C)
        #print_topo(mtopo)
        out = write_topo_to_file(self.__id, mtopo, hosts)
        return out

    #TODO lo stoppi in questo modo? Considera se devi proteggere variabili con lock o no
    def stop(self):
        self.__end = True

 
