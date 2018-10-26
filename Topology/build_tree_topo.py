#!/us5/bin/python

import pdb
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node
from mininet.log import setLogLevel, info
from mininet.cli import CLI


class LinuxRouter(Node):
    "A Node with IP forwarding enabled."

    def config(self, **params):
        super(LinuxRouter, self).config(**params)
        # Enable forwarding on the router
        self.cmd('sysctl net.ipv4.ip_forward=1')
        self.cmd('net.ipv4.conf.default.arp_filter=1')
        self.cmd('net.ipv4.conf.all.arp_filter=1')

    def terminate(self):
        self.cmd('sysctl net.ipv4.ip_forward=0')
        super(LinuxRouter, self).terminate()


class NetworkTopo(Topo):
    "A LinuxRouter connecting three IP subnets"



    def build(self, **_opts):
        self.tree = TreeNode('10.1.0.2', 128, 17, 7, self)
        #tree = TreeNode('10.1.0.2', 16, 17, 4, self)
        self.tree.add_links()


class TreeNode():
    '''Build a binary tree and returns a reference to the root. Each node has a reference to its father and to its
     two children. '''
    count = 0

    def __init__(self, defaultIP, increment, subnetMask, level, topo):
        '''Initializes the node and creates recursively the left and the right subtree.
        :param defaultIP: DefaultIP given to this node. It corresponds to the network interface used as default route
        :param increment: Allows to define the ip address towards the right subtree and the range of ip to be
        passed to the right child
        :param subnetMask: subnet mask, used in the added routes
        :param level: specifies how many levels of the tree have to be created from this node on. When level reaches 0
        the recursion is ended
        :param topo: Topology object, used to add routers, switches and links
        '''
        self.defaultIP = defaultIP
        bytes = self.getBytesFromIP(defaultIP)
        self.leftIP = bytes[0] + '.' + bytes[1] + '.' + bytes[2] + '.' + str(int(bytes[3]) + 1)
        self.rightIP = bytes[0] + '.' + bytes[1] + '.' + str(int(bytes[2]) + increment) + '.'  + str(1)
        TreeNode.count += 1
        self.id = 'r' + str(TreeNode.count)
        self.alias = self.id + ' ' + self.defaultIP + ' ' + self.leftIP + ' ' + self.rightIP
        subnet1 = bytes[0] + '.' + bytes[1] + '.' + bytes[2] + '.' + str(0) + '/' + str(subnetMask)
        subnet2 = bytes[0] + '.' + bytes[1] + '.' + str(int(bytes[2]) + increment) + '.' + str(0) + '/' + str(subnetMask)
        fatherIP = bytes[0] + '.' + bytes[1] + '.' + bytes[2] + '.' + str(int(bytes[3])-1) # We exploit the structure..
        self.defaultRoute = 'ip route add default via ' + fatherIP + ' dev ' + self.id + '-eth1'
        # Add router
        self.router = topo.addNode(self.id, cls=LinuxRouter, ip=self.defaultIP)
        self.topo = topo
        self.level = level
        self.submask = str(subnetMask)
        if level != 1: # !=0 and increment/2 > 1:
            # Add switches. Each node carries the two switches to reach its two children.
            self.leftSwitch = topo.addSwitch(self.id + 'left')
            self.rightSwitch = topo.addSwitch(self.id + 'right')
            self.leftChildIP = bytes[0] + '.' + bytes[1] + '.' + bytes[2] + '.' + str(int(bytes[3]) + 2)
            self.rightChildIP = bytes[0] + '.' + bytes[1] + '.' + str(int(bytes[2]) + increment) + '.'  + str(2)
            self.leftChild = TreeNode(self.leftChildIP, increment / 2, subnetMask + 1, level-1, topo)
            self.rightChild = TreeNode(self.rightChildIP, increment / 2, subnetMask + 1, level -1, topo)

    def add_links(self):
        '''
        Add links to the topology to build a binary tree. If this node has children, adds the the links both
        from itself to the switches and from the children to the switches
        '''
        if self.level != 1: # This node is not a leaf
            self.topo.addLink(self.leftSwitch, self.router, intfName2=self.id+'-eth2',
                              params2={'ip': self.leftIP + '/' + self.submask })
            self.topo.addLink(self.rightSwitch, self.router, intfName2=self.id + '-eth3',
                              params2={'ip': self.rightIP + '/' + self.submask})
            self.topo.addLink(self.leftSwitch, self.leftChild.router, intfName2=self.leftChild.id + '-eth1',
                              params2={'ip': self.leftChild.defaultIP + '/' + self.leftChild.submask})
            self.topo.addLink(self.rightSwitch, self.rightChild.router, intfName2=self.rightChild.id + '-eth1',
                              params2={'ip': self.rightChild.defaultIP + '/' + self.rightChild.submask})
            self.leftChild.add_links()
            self.rightChild.add_links()

    def add_static_routes(self, net):
        '''
        Adds to the network nodes the static routes and the default route in a recursive fashion.
        :param net: Mininet network
        '''
        #net[self.id].cmd('ip route flush cache')
        #net[self.id].cmd(self.defaultRoute)
        if self.level != 1:
            lefthosts = self.leftChild.add_static_routes(net)
            righthosts = self.rightChild.add_static_routes(net)
            #net[self.id].cmd('ip route flush dev ' + self.id + '-eth2')
            #net[self.id].cmd('ip route flush dev ' + self.id + '-eth3')
            for l in lefthosts:
                net[self.id].cmd('ip route add ' + l + '/32 via ' + self.leftChildIP + ' dev ' + self.id + '-eth2')
            for r in righthosts:
                net[self.id].cmd('ip route add ' + r + '/32 via ' + self.rightChildIP + ' dev ' + self.id + '-eth3')

            bytes = self.getBytesFromIP(self.leftIP) #TODO va fatto anche per ilc aso base?
            net[self.id].cmd(
                'ip route delete ' + bytes[0] + '.' + bytes[1] + '.' + bytes[2] + '.' + '0/' + self.submask)
            bytes = self.getBytesFromIP(self.rightIP)
            net[self.id].cmd(
                'ip route delete ' + bytes[0] + '.' + bytes[1] + '.' + bytes[2] + '.' + '0/' + self.submask)

            return lefthosts + righthosts + [self.defaultIP,self.leftIP, self.rightIP]
        else: # Base case
            return [self.defaultIP, self.leftIP, self.rightIP]

    def getBytesFromIP(self, IP):
        return IP.split('.')

def add_static_routes(net, topo):
    '''Add static routes to the router for subnets not directly visible'''
    pdb.set_trace()
    topo.tree.add_static_routes(net)

topo = NetworkTopo()
net = Mininet( topo=topo)
add_static_routes(net, topo)
net.start()
CLI(net)


#t1root = TreeNode('10.1.0.2', 128, 17, 7)
#a = []
