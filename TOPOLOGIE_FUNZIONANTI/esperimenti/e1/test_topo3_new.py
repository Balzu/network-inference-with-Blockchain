#!/us5/bin/python

import os
import pdb
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node
from mininet.log import setLogLevel, info
from mininet.cli import CLI

hosts = []
routers = []
switches = []

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
            #hosts.append(h)
            

def run():
    "Test linux router"
    topo = NetworkTopo()
    net = Mininet( topo=topo )
    add_static_routes(net)
    net.start()
    compute_distances(net) 
    make_anonymous_and_blocking_routers(net)
    create_traces(net)
    alias = create_alias()
    vtopo = create_virtual_topo(alias, net)
    print_topo(vtopo)
    net.stop()


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


def make_anonymous_and_blocking_routers(net):
    net['r3'].cmd('iptables -P OUTPUT DROP')
    
    
    
def compute_distances(net):
    with open ("hosts", "r") as hosts_file:
        hosts = hosts_file.read().split()
        distances = {}
        for h1 in hosts:
            for h2 in hosts:
                if h1 != h2:                    
                # For each host different from host1, add a line with the name of the host
                # and the distance from host1 (exploit TTL to derive the distance)
                    print "Starting ping from " + h1 + " ... " 
                    os.system("echo -n '" + h1 + " '  >> distances/" + h2)
                    net[h1].cmd('ping -c 1 ' + net[h2].IP() + 
                    " | grep from | awk '{split($6,a,\"=\"); print 64 - a[2]}'>> distances/" + 
                    h1)
    
def create_traces(net):
    with open ("hosts", "r") as hosts_file:
        hosts = hosts_file.read().split()
        for h1 in hosts:
            for h2 in hosts:
                if h1 != h2:                    
                # For each host different from host1, add a line with the name of the host
                # and the distance from host1 (exploit TTL to derive the distance)
                    print "Starting collection of traces from " + h1 + " ... " 
                    net[h1].cmd('traceroute -n -w 0.5 ' + net[h2].IP() + ' > traceroute/' + h1 + h2)
 

def create_alias():
    with open("alias", "r") as alias_file:
        alias = {}
        for line in alias_file:
            l = line.split()
            for address in l[1:]:
                alias[address]=(l[0]) #l[0] is the router name
        return alias

def create_virtual_topo(alias, net):
    with open ("hosts", "r") as hosts_file:    
        hosts = hosts_file.read().split()
        topo = {}
        x = [0]  # Incremental identifier for non responding routers. x is a list used as single value
        for h1 in hosts:
            for h2 in hosts:
                if h1 != h2:             
                    if get_answer_from_dest(h1,h2): 
                        #TODO manage the cases in which no blocking router is found
                        # could find one or more anonymouse router
                        add_routers(topo, h1, h2, x, alias)
                    else:
                        #TODO Manage the case in which you find at least one blocking router  
                        print "Manage Blocking router case"
    return topo

def get_answer_from_dest(host1,host2):
    count = len(open("traceroute/"+host1+host2).readlines())
    if count <= 30:
        return True
    else:
        return False

def add_routers(topo,host1,host2,x, alias):
    with open("traceroute/"+host1+host2) as trace:
        lines = trace.readlines()
        num_lines = len(lines)
        src = ''
        dst = ''
        for i in range(1, num_lines-2):  #skip first and last line (don't consider hosts)
            src = find_router(lines[i].split(), alias)
            dst = find_router(lines[i+1].split(), alias)
            add_link(topo,(src,dst),x,i)    

def find_router(line,alias):
    i = 1
    while  i <= 3 and line[i]=='*':
        i=i+1
    if i > 3:
        return 'A'
    else:
        return alias[line[i]]

def add_link(topo,(src,dst),x,line):
    #pdb.set_trace()
    if src not in topo: # A non responding router is NEVER in the topology (don't have as keys 'A', 'B', 'H' or 'NC')
        if is_responding(src):   #If we have a responding router, add it as responding
            topo[src] = ('R', set())
        else:  #Non responding router: the type (anonymous, blocking, hidden, non cooperative) is the name itself
# Non responding routers are called X1, X2, X3, ... we add a virtual router to the topology for each non responding router found.            
# When the src router is a non responding (anonymous in particular) one, we add a NEW (virtual) router only if we are scanning the first
# line. Indeed, in all the other cases we would have already added that non responding router when dealing with the destination
# router of previous iteration.
            if line == 1: 
                x[0] = x[0] + 1   
                _type = src
                src = 'X'+str(x[0])
                topo[src] = (_type, set())
            else:
                src = 'X'+str(x[0])
    if dst not in topo:
        if is_responding(dst):   
            topo[dst] = ('R', set())
        else:  
            x[0] = x[0] + 1   
            _type = dst
            dst = 'X'+str(x[0])
            topo[dst] = (_type, set())
    topo[src][1].add(dst)


def is_responding(router):
    if router != 'A' and router != 'H' and router != 'NC' and router != 'B': #TODO controlla di aver messo tutte le condizioni
        return True
    else:
        return False

def print_topo(topo):
    for src in topo:
        for d in topo[src][1]:
            print src + ' -> ' + d


if __name__ == '__main__':
    setLogLevel( 'info' )
    run()
