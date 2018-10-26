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
        self.sensors = []
        super(NetworkTopo, self).__init__()
        '''        
        :param num_hosts:  Number of hosts to be inserted in the topology     
        :param num_sensors: Number of sensors to be inserted in the topology
        '''

    def build( self, **_opts ):

        ip_template = ['192.168.1.', '/24']
        self.router = self.addNode( 'r1', cls=LinuxRouter, ip='14.21.5.38/8' )
        sI = self.addSwitch('s1')
        sL = self.addSwitch('s2')
        self.addLink( sI, self.router, intfName2='r1-eth1',
                      params2={ 'ip' : '14.21.5.38/8' } )
        self.addLink(sL, self.router, intfName2='r1-eth2',
                     params2={'ip': '192.168.1.1/24'})

        ip = 1
        for i in range(1, self.num_host+1):
            ip += 1
            self.net_hosts.append(self.addHost( 'h'+str(i), ip='192.168.1.' + str(ip) +'/24',
                           defaultRoute='via 192.168.1.1' ))
        for i in range(1, self.num_sensor+1):
            ip += 1
            self.sensors.append(self.addHost( 'hs'+str(i), ip='192.168.1.' + str(ip) +'/24',
                           defaultRoute='via 192.168.1.1' ))

        for h in self.net_hosts:
            self.addLink(h, sL)
        for s in self.sensors:
            self.addLink(s, sL)


def add_static_routes(net):
    '''Add static routes to the router for subnets not directly visible'''
    pass #TODO

topo = NetworkTopo1(num_host =5, num_sensor = 1)
net = Mininet( topo=topo)
add_static_routes(net)
net.start()
CLI(net)
