#!/us5/bin/python
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
        defaultIP5 = '192.168.10.1/24'  # IP address for r2-eth1
        defaultIP6 = '192.168.12.1/24'
        defaultIP7 = '192.168.13.1/24'
        router1 = self.addNode( 'r1', cls=LinuxRouter, ip=defaultIP1 )
        router2 = self.addNode( 'r2', cls=LinuxRouter, ip=defaultIP2 )
        router3 = self.addNode('r3', cls=LinuxRouter, ip=defaultIP3)
        router4 = self.addNode('r4', cls=LinuxRouter, ip=defaultIP4)
        router5 = self.addNode( 'r5', cls=LinuxRouter, ip=defaultIP5 )
        router6 = self.addNode('r6', cls=LinuxRouter, ip=defaultIP6)
        router7 = self.addNode('r7', cls=LinuxRouter, ip=defaultIP7)

        s1, s2, s11, s21, s31, s3, s41, s42, s4, s5, s6, s61, s71 = \
        [ self.addSwitch( s ) for s in 's1', 's2', 's11', 's21', 's31', 's3', 's41', 's42', 's4',
            's5', 's6', 's61', 's71' ]

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
        self.addLink( s4, router4, intfName2='r4-eth4',
                      params2={ 'ip' : '192.168.9.1/24' } )
     
        self.addLink( s5, router5, intfName2='r5-eth1',
                      params2={ 'ip' : defaultIP5 } )
        self.addLink( s4, router5, intfName2='r5-eth2',
                      params2={ 'ip' : '192.168.9.2/24' } )
        self.addLink( s6, router5, intfName2='r5-eth3',
                      params2={ 'ip' : '192.168.11.1/24' } )

        self.addLink( s61, router6, intfName2='r6-eth1',
                      params2={ 'ip' : defaultIP6 } )
        self.addLink( s5, router6, intfName2='r6-eth2',
                      params2={ 'ip' : '192.168.10.2/24' } )

        self.addLink( s71, router7, intfName2='r7-eth1',
                      params2={ 'ip' : defaultIP7 } )
        self.addLink( s6, router7, intfName2='r7-eth2',
                      params2={ 'ip' : '192.168.11.2/24' } )

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
        h61 = self.addHost( 'h61', ip='192.168.12.2/24',
                           defaultRoute='via 192.168.12.1' )
        h62 = self.addHost( 'h62', ip='192.168.12.3/24',
                           defaultRoute='via 192.168.12.1' )
        h71 = self.addHost( 'h71', ip='192.168.13.2/24',
                           defaultRoute='via 192.168.13.1' )

        for h, s in [ (h11, s11), (h21, s21), (h31, s31), (h41,s41), (h42,s42), (h61,s61),  \
        (h62, s61), (h71, s71) ]:
            self.addLink( h, s )

def add_static_routes(net):
    '''Add static routes to the router for subnets not directly visible'''
    net['r1'].cmd('ip route add 192.168.3.0/24 via 192.168.2.2 dev r1-eth2')
    net['r1'].cmd('ip route add 192.168.4.0/24 via 192.168.2.2 dev r1-eth2')
    net['r1'].cmd('ip route add 192.168.5.0/24 via 192.168.2.2 dev r1-eth2')
    net['r1'].cmd('ip route add 192.168.6.0/24 via 192.168.2.2 dev r1-eth2')
    net['r1'].cmd('ip route add 192.168.7.0/24 via 192.168.2.2 dev r1-eth2')
    net['r1'].cmd('ip route add 192.168.8.0/24 via 192.168.2.2 dev r1-eth2')
    net['r1'].cmd('ip route add 192.168.9.0/24 via 192.168.2.2 dev r1-eth2')
    net['r1'].cmd('ip route add 192.168.10.0/24 via 192.168.2.2 dev r1-eth2')
    net['r1'].cmd('ip route add 192.168.11.0/24 via 192.168.2.2 dev r1-eth2')
    net['r1'].cmd('ip route add 192.168.12.0/24 via 192.168.2.2 dev r1-eth2')
    net['r1'].cmd('ip route add 192.168.13.0/24 via 192.168.2.2 dev r1-eth2')
    net['r2'].cmd('ip route add 192.168.1.0/24 via 192.168.2.1 dev r2-eth2')
    net['r2'].cmd('ip route add 192.168.5.0/24 via 192.168.4.2 dev r2-eth3')  
    net['r2'].cmd('ip route add 192.168.6.0/24 via 192.168.4.2 dev r2-eth3')  
    net['r2'].cmd('ip route add 192.168.7.0/24 via 192.168.4.2 dev r2-eth3')  
    net['r2'].cmd('ip route add 192.168.8.0/24 via 192.168.4.2 dev r2-eth3')  
    net['r2'].cmd('ip route add 192.168.9.0/24 via 192.168.4.2 dev r2-eth3')  
    net['r2'].cmd('ip route add 192.168.10.0/24 via 192.168.4.2 dev r2-eth3')  
    net['r2'].cmd('ip route add 192.168.11.0/24 via 192.168.4.2 dev r2-eth3')  
    net['r2'].cmd('ip route add 192.168.12.0/24 via 192.168.4.2 dev r2-eth3')  
    net['r2'].cmd('ip route add 192.168.13.0/24 via 192.168.4.2 dev r2-eth3')  
    net['r3'].cmd('ip route add 192.168.1.0/24 via 192.168.4.1 dev r3-eth2')
    net['r3'].cmd('ip route add 192.168.2.0/24 via 192.168.4.1 dev r3-eth2')
    net['r3'].cmd('ip route add 192.168.3.0/24 via 192.168.4.1 dev r3-eth2')
    net['r3'].cmd('ip route add 192.168.7.0/24 via 192.168.6.2 dev r3-eth3')
    net['r3'].cmd('ip route add 192.168.8.0/24 via 192.168.6.2 dev r3-eth3')
    net['r3'].cmd('ip route add 192.168.9.0/24 via 192.168.6.2 dev r3-eth3')
    net['r3'].cmd('ip route add 192.168.10.0/24 via 192.168.6.2 dev r3-eth3')
    net['r3'].cmd('ip route add 192.168.11.0/24 via 192.168.6.2 dev r3-eth3')
    net['r3'].cmd('ip route add 192.168.12.0/24 via 192.168.6.2 dev r3-eth3')
    net['r3'].cmd('ip route add 192.168.13.0/24 via 192.168.6.2 dev r3-eth3')
    net['r4'].cmd('ip route add 192.168.1.0/24 via 192.168.6.1 dev r4-eth2')
    net['r4'].cmd('ip route add 192.168.2.0/24 via 192.168.6.1 dev r4-eth2')
    net['r4'].cmd('ip route add 192.168.3.0/24 via 192.168.6.1 dev r4-eth2')
    net['r4'].cmd('ip route add 192.168.4.0/24 via 192.168.6.1 dev r4-eth2')
    net['r4'].cmd('ip route add 192.168.5.0/24 via 192.168.6.1 dev r4-eth2')
    net['r4'].cmd('ip route add 192.168.10.0/24 via 192.168.9.2 dev r4-eth4')
    net['r4'].cmd('ip route add 192.168.11.0/24 via 192.168.9.2 dev r4-eth4')
    net['r4'].cmd('ip route add 192.168.12.0/24 via 192.168.9.2 dev r4-eth4')
    net['r4'].cmd('ip route add 192.168.13.0/24 via 192.168.9.2 dev r4-eth4')
    net['r5'].cmd('ip route add 192.168.1.0/24 via 192.168.9.1 dev r5-eth2')
    net['r5'].cmd('ip route add 192.168.2.0/24 via 192.168.9.1 dev r5-eth2')
    net['r5'].cmd('ip route add 192.168.3.0/24 via 192.168.9.1 dev r5-eth2')
    net['r5'].cmd('ip route add 192.168.4.0/24 via 192.168.9.1 dev r5-eth2')
    net['r5'].cmd('ip route add 192.168.5.0/24 via 192.168.9.1 dev r5-eth2')
    net['r5'].cmd('ip route add 192.168.6.0/24 via 192.168.9.1 dev r5-eth2')
    net['r5'].cmd('ip route add 192.168.7.0/24 via 192.168.9.1 dev r5-eth2')
    net['r5'].cmd('ip route add 192.168.8.0/24 via 192.168.9.1 dev r5-eth2')
    net['r5'].cmd('ip route add 192.168.12.0/24 via 192.168.10.2 dev r5-eth1')
    net['r5'].cmd('ip route add 192.168.13.0/24 via 192.168.11.2 dev r5-eth3')
    net['r6'].cmd('ip route add 192.168.0.0/16 via 192.168.10.1 dev r6-eth2')
    net['r7'].cmd('ip route add 192.168.0.0/16 via 192.168.11.1 dev r7-eth2')

