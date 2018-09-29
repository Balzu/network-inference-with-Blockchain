#!/us5/bin/python

"""
linuxrouter.py: Example network with Linux IP router

This example converts a Node into a router using IP forwarding
already built into Linux.

The example topology creates a router and three IP subnets:

    - 192.168.1.0/24 (r0-eth1, IP: 192.168.1.1)
    - 172.16.0.0/12 (r0-eth2, IP: 172.16.0.1)
    - 10.0.0.0/8 (r0-eth3, IP: 10.0.0.1)

Each subnet consists of a single host connected to
a single switch:

    r0-eth1 - s1-eth1 - h1-eth0 (IP: 192.168.1.100)
    r0-eth2 - s2-eth1 - h2-eth0 (IP: 172.16.0.100)
    r0-eth3 - s3-eth1 - h3-eth0 (IP: 10.0.0.100)

The example relies on default routing entries that are
automatically created for each router interface, as well
as 'defaultRoute' parameters for the host interfaces.

Additional routes may be added to the router or hosts by
executing 'ip route' or 'route' commands on the router or hosts.
"""

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node
from mininet.log import setLogLevel, info
from mininet.cli import CLI

class LinuxRouter( Node ):
    "A Node with IP forwarding enabled."

    def config( self, **params ):
        super( LinuxRouter, self).config( **params )
        # Enable forwarding on the router
        self.cmd( 'sysctl net.ipv4.ip_forward=1' )

    def terminate( self ):
        self.cmd( 'sysctl net.ipv4.ip_forward=0' )
        super( LinuxRouter, self ).terminate()


class NetworkTopo( Topo ):
    "A LinuxRouter connecting three IP subnets"

    def build( self, **_opts ):

        defaultIP1 = '192.168.1.1/24'  # IP address for r1-eth1
        defaultIP2 = '192.168.3.1/24'  # IP address for r2-eth1
        defaultIP3 = '192.168.5.1/24'
        defaultIP4 = '192.168.7.1/24'
        router1 = self.addNode( 'r1', cls=LinuxRouter, ip=defaultIP1 )
        router2 = self.addNode( 'r2', cls=LinuxRouter, ip=defaultIP2 )
        router3 = self.addNode('r3', cls=LinuxRouter, ip=defaultIP3)
        router4 = self.addNode('r4', cls=LinuxRouter, ip=defaultIP4)

        s1, s2, s11, s21, s31, s3, s41, s42 = \
        [ self.addSwitch( s ) for s in 's1', 's2', 's11', 's21', 's31', 's3', 's41', 's42' ]

        self.addLink( s11, router1, intfName2='r1-eth1',
                      params2={ 'ip' : defaultIP1 } )  # for clarity
        self.addLink( s1, router1, intfName2='r1-eth2',
                      params2={ 'ip' : '192.168.2.1/24' } ) 
                   
        self.addLink( s21, router2, intfName2='r2-eth1',
                      params2={ 'ip' : defaultIP2 } )
        self.addLink( s1, router2, intfName2='r2-eth2',
                      params2={ 'ip' : '192.168.2.2/24' } )
        self.addLink( s2, router2, intfName2='r2-eth3',
                      params2={ 'ip' : '192.168.4.1/24' } )
        
        self.addLink( s31, router3, intfName2='r3-eth1',
                      params2={ 'ip' : defaultIP3 } )
        self.addLink( s2, router3, intfName2='r3-eth2',
                      params2={ 'ip' : '192.168.4.2/24' } )
        self.addLink( s3, router3, intfName2='r3-eth3',
                      params2={ 'ip' : '192.168.6.1/24' } )
       
        self.addLink( s41, router4, intfName2='r4-eth1',
                      params2={ 'ip' : defaultIP4 } )
        self.addLink( s3, router4, intfName2='r4-eth2',
                      params2={ 'ip' : '192.168.6.2/24' } )
        self.addLink( s42, router4, intfName2='r4-eth3',
                      params2={ 'ip' : '192.168.8.1/24' } )
     

        h11 = self.addHost( 'h11', ip='192.168.1.2/24',
                           defaultRoute='via 192.168.1.1' )
        h21 = self.addHost( 'h21', ip='192.168.3.2/24',
                           defaultRoute='via 192.168.3.1' )
        h31 = self.addHost( 'h31', ip='192.168.5.2/24',
                           defaultRoute='via 192.168.5.1' )
        h41 = self.addHost( 'h41', ip='192.168.7.2/24',
                           defaultRoute='via 192.168.7.1' )
        h42 = self.addHost( 'h42', ip='192.168.8.2/24',
                           defaultRoute='via 192.168.8.1' )

        for h, s in [ (h11, s11), (h21, s21), (h31, s31), (h41,s41), (h42,s42) ]:
            self.addLink( h, s )


def run():
    "Test linux router"
    topo = NetworkTopo()
    net = Mininet( topo=topo )  # controller is used by s1-s3
    #Add static routes to the router for subnets not directly visible
    net['r1'].cmd('ip route add 192.168.3.0/24 via 192.168.2.2 dev r1-eth2')
    net['r1'].cmd('ip route add 192.168.4.0/24 via 192.168.2.2 dev r1-eth2')
    net['r1'].cmd('ip route add 192.168.5.0/24 via 192.168.2.2 dev r1-eth2')
    net['r1'].cmd('ip route add 192.168.6.0/24 via 192.168.2.2 dev r1-eth2')
    net['r1'].cmd('ip route add 192.168.7.0/24 via 192.168.2.2 dev r1-eth2')
    net['r1'].cmd('ip route add 192.168.8.0/24 via 192.168.2.2 dev r1-eth2')
    net['r2'].cmd('ip route add 192.168.1.0/24 via 192.168.2.1 dev r2-eth2')
    net['r2'].cmd('ip route add 192.168.5.0/24 via 192.168.4.2 dev r2-eth3')  
    net['r2'].cmd('ip route add 192.168.6.0/24 via 192.168.4.2 dev r2-eth3')  
    net['r2'].cmd('ip route add 192.168.7.0/24 via 192.168.4.2 dev r2-eth3')  
    net['r2'].cmd('ip route add 192.168.8.0/24 via 192.168.4.2 dev r2-eth3')  
    net['r3'].cmd('ip route add 192.168.1.0/24 via 192.168.4.1 dev r3-eth2')
    net['r3'].cmd('ip route add 192.168.2.0/24 via 192.168.4.1 dev r3-eth2')
    net['r3'].cmd('ip route add 192.168.3.0/24 via 192.168.4.1 dev r3-eth2')
    net['r3'].cmd('ip route add 192.168.7.0/24 via 192.168.6.2 dev r3-eth3')
    net['r3'].cmd('ip route add 192.168.8.0/24 via 192.168.6.2 dev r3-eth3')
    net['r4'].cmd('ip route add 192.168.1.0/24 via 192.168.6.1 dev r4-eth2')
    net['r4'].cmd('ip route add 192.168.2.0/24 via 192.168.6.1 dev r4-eth2')
    net['r4'].cmd('ip route add 192.168.3.0/24 via 192.168.6.1 dev r4-eth2')
    net['r4'].cmd('ip route add 192.168.4.0/24 via 192.168.6.1 dev r4-eth2')
    net['r4'].cmd('ip route add 192.168.5.0/24 via 192.168.6.1 dev r4-eth2')
   
    net.start()
    info( '*** Routing Table on Router:\n' )
    print net[ 'r1' ].cmd( 'route' )
    print net[ 'r2' ].cmd( 'route' )
    print net[ 'r3' ].cmd( 'route' )
    CLI( net )
    #CLI(h1 traceroute h2)
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    run()
