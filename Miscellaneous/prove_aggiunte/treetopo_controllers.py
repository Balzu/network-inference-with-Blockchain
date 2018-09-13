#!/us5/bin/python
# coding=utf-8

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
from mininet.node import Node, Controller, OVSSwitch
from mininet.log import setLogLevel, info
from mininet.cli import CLI

class LinuxRouter( Node ):
    "A Node with IP forwarding enabled."

    def config( net, **params ):
        super( LinuxRouter, net).config( **params )
        # Enable forwarding on the router
        net.cmd( 'sysctl net.ipv4.ip_forward=1' )

    def terminate( net ):
        net.cmd( 'sysctl net.ipv4.ip_forward=0' )
        super( LinuxRouter, net ).terminate()


class createTreeTopo( ):
   
    net = Mininet(controller = Controller, switch=OVSSwitch )
    # Lista degli indirizzi dei router
    a = ['10.0.0.1/8',
         '10.0.1.1/8', '11.0.1.1/8',
         '10.128.1.1/9','10.127.1.1/9','11.128.1.1/9','11.127.1.1/9',            
         '10.192.1.1/10','10.191.1.1/10','10.64.1.1/10','10.63.1.1/10','11.192.1.1/10','11.191.1.1/10','11.64.1.1/10','11.63.1.1/10' 
        ]
    # Rename: non è la lista degli host, ma la lista degli indirizzi degli host, con gateway associato
    h = [('10.192.1.101/10','10.192.1.102/10','10.192.1.1/10'), ('10.191.1.101/10','10.191.102.1/10','10.191.1.1/10'),
         ('10.64.1.101/10','10.64.1.102/10','10.64.1.1/10'),('10.63.1.101/10','10.63.1.102/10','10.63.1.1/10'),
         ('11.192.1.101/10','11.192.1.102/10','11.192.1.1/10'),('11.191.1.101/10','11.191.1.102/10','11.191.1.1/10'),
         ('11.64.1.101/10','11.64.1.102/10','11.64.1.1/10'),('11.63.1.101/10','11.63.1.102/10','11.63.1.1/10')]
    r = []
    s = []
    c = []
    hosts = []
    for i in range(15):
        s.append(net.addSwitch('s'+str(i)))
        r.append(net.addHost( 'r'+str(i), cls=LinuxRouter, ip=a[i] ))
        c.append(net.addController('c'+str(i), port=6633+i))
    #        s1, s2, s3, s4, s5 = [ net.addSwitch( s ) for s in 's1', 's2', 's3', 's4', 's5' ]

    for i in range(15):
        top = i       # father
        left = i*2 + 1 # left child
        right = i*2 + 2 # right child
        # add upwards interfaces for all nodes
        net.addLink( s[top], r[i], intfName2='r'+str(i)+'-eth1',
                      params2={ 'ip' : a[top] } )
        if (right<=14): #the downward interfaces are only added for internal nodes 
            net.addLink( s[left], r[i], intfName2='r'+str(i)+'-eth2',
                      params2={ 'ip' : a[left].replace('.1/','.2/') } ) 
            net.addLink( s[right], r[i], intfName2='r'+str(i)+'-eth3',
                      params2={ 'ip' : a[right].replace('.1/','.2/') } ) 
       
             
    for i in range(len(h)):
        hosts.append(net.addHost( 'h'+str(i*2), ip=h[i][0], defaltRoute='via '+h[i][2]))
        hosts.append(net.addHost( 'h'+str(i*2+1), ip=h[i][1], defaltRoute='via '+h[i][2]))
           
    # Only leaf switches have to be connected to the hosts
    leaves = s[7:]

    for i in range(len(leaves)):
       net.addLink(hosts[i*2], leaves[i]) 
       net.addLink(hosts[i*2+1], leaves[i]) 

    net.build()
    for co in c:
        co.start()

    for i in range(15):
        s[i].start([ c[i] ])

    #net['r1'].cmd('ip route add 11.0.1.1/8 via 10.0.1.2 dev r1-eth1')
    #net['r0'].cmd('ip route add 11.0.1.1/8 via 11.0.1.1 dev r0-eth3')
    '''   #Add static routes to the router for subnets not directly visible    
    net['r2'].cmd('ip route add 192.168.1.0/24 via 192.168.2.2 dev r2-eth1')
    net['r2'].cmd('ip route add 172.16.0.0/12 via 192.168.2.2 dev r2-eth1')
    net['r2'].cmd('ip route add 10.0.0.0/8 via 192.168.2.2 dev r2-eth1') '''
    #net.start()
    info( '*** Routing Table on Router:\n' )
    print net[ 'r0' ].cmd( 'route' )
    print net[ 'r2' ].cmd( 'route' )
    CLI( net )
    #CLI(h1 traceroute h2)
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    createTreeTopo()
