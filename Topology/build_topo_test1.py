#!/us5/bin/python
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node
from mininet.log import setLogLevel, info
from mininet.cli import CLI
import pdb

class LinuxRouter( Node ):
    "A Node with IP forwarding enabled."

    def config( self, **params ):
        super( LinuxRouter, self).config( **params )
        # Enable forwarding on the router
        self.cmd( 'sysctl net.ipv4.ip_forward=1' )

    def terminate( self ):
        self.cmd( 'sysctl net.ipv4.ip_forward=0' )
        super( LinuxRouter, self ).terminate()


class NetworkTopo1( Topo ):
    "This topology simulates a domestic network with more hosts connected to a single router \
    and belonging to the same subnet. A given amount of sensors is inserted to monitor the topology."

    def __init__(self, *args, **params):

        self.num_sensor = params['num_sensor']
        self.num_host = params['num_host']
        self.net_hosts = []
        self.active_sensors = []
        self.passive_sensors = []
        self.monitor_sensors = []
        self.alias = {} # Dictionary st: key = router/host name, value = list of IP addresses of the router/host
        self.sroutes = {} # Key: Router/Host/senor id, value = list of static routes to be setup
        super(NetworkTopo1, self).__init__()
        '''        
        :param num_hosts:  Number of hosts to be inserted in the topology     
        :param num_sensors: Number of sensors to be inserted in the topology
        '''

    def build( self, **_opts ):

        self.router = self.addNode( 'r1', cls=LinuxRouter, ip='192.168.1.1/24' ) #'14.21.5.38/8'
        self.alias['r1'] = []
        self.sroutes['r1'] = []
        ip = 1
        swid = 2
        for i in range(1, self.num_host+1):
            sw = self.addSwitch('s'+str(swid))
            hid = 'h'+str(i)
            rIP = '192.168.' + str(ip) + '.1'
            hIP = '192.168.' + str(ip) + '.2'
            self.net_hosts.append(self.addHost(hid, ip=hIP + '/24', defaultRoute=rIP))
            self.addLink(sw, self.router, intfName2='r1-eth'+ str(swid),
                         params2={'ip': rIP + '/24'})
            self.addLink(hid, sw)
            self.alias[hid] = [hIP]
            self.alias['r1'].append(rIP)
            self.sroutes['r1'].append('ip route add ' + hIP + '/32 via ' + hIP + ' dev r1-eth'+ str(swid))
            self.sroutes[hid] = ['ip route add default via ' + rIP + ' dev ' + hid + '-eth0']
            ip += 1 # era +=2
            swid += 1
        # In Mininet you can't send simultaneously 2 commands to the same host. To circumvent this limitation
        # we create 3 hosts for each sensor, connected to the same switch: the active host looks for dead nodes,
        # The passive host looks for new nodes, the monitor host runs the topology inference algorithm
        for i in range(1, self.num_sensor+1):
            sw = self.addSwitch('s' + str(swid))
            asid = 'has'+str(i)
            psid = 'hps' + str(i)
            msid = 'hms' + str(i)
            rIP = '192.168.' + str(ip) + '.1'
            asIP = '192.168.' + str(ip) + '.2' # Active sensor IP
            psIP = '192.168.' + str(ip) + '.3' # Passive sensor IP
            msIP = '192.168.' + str(ip) + '.4' # Monitor sensor IP (the one that runs iTop)
            self.active_sensors.append(self.addHost(asid, ip=asIP + '/24', defaultRoute=rIP))
            self.passive_sensors.append(self.addHost(psid, ip=psIP + '/24', defaultRoute=rIP))
            self.monitor_sensors.append(self.addHost(msid, ip=msIP + '/24', defaultRoute=rIP))
            self.addLink(sw, self.router, intfName2='r1-eth' + str(swid), params2={'ip': rIP + '/24'})
            self.addLink(asid, sw)
            self.addLink(psid, sw)
            self.addLink(msid, sw)
            self.alias[asid] = [asIP]
            self.alias[psid] = [psIP]
            self.alias[msid] = [msIP]
            self.alias['r1'].append(rIP)
            self.sroutes['r1'].append('ip route add ' + asIP + '/32 via ' + asIP + ' dev r1-eth' + str(swid))
            self.sroutes[asid] = ['ip route add default via ' + rIP + ' dev ' + asid + '-eth0']
            self.sroutes[psid] = ['ip route add default via ' + rIP + ' dev ' + psid + '-eth0']
            self.sroutes[msid] = ['ip route add default via ' + rIP + ' dev ' + msid + '-eth0']
            ip += 1
            swid += 1


    def add_static_routes(self, net):
        '''Add static routes to the router for subnets not directly visible'''
        for k in self.sroutes.keys():
            for r in self.sroutes[k]:
                net[k].cmd(r)

    def create_alias_file(self):
        with open('alias', 'w') as f:
            for k in self.alias.keys():
                f.write(k + ' ')
                for ip in self.alias[k]:
                    f.write(ip + ' ')
                f.write('\n')

