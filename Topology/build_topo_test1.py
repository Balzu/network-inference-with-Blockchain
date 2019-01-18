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
    """
    This topology simulates a network with 6 hosts: 3 belongs to subnet 192.168.1.0/24 and the other three
    belong to subnet 192.168.2.0/24. The two subnets are linked together with a router.
    3 options are available:
    one sensor in first subnet,
    one sensor in second subnet,
    one sensor in both subnets.
    """

    def __init__(self, *args, **params):
        '''
        :param sensor1: True if a sensor has to be placed in subnet 192.168.1.0/24
        :param sensor2: True if a sensor has to be placed in subnet 192.168.2.0/24
        '''
        self.sensor1 = False if (params['sensor1'] is None or params['sensor1'] is False) else True # Boolean
        self.sensor2 = False if (params['sensor2'] is None or params['sensor2'] is False) else True  # Boolean
        self.swc = {} # Key: Number of switch, value: switch
        self.net_hosts = []
        self.active_sensors = []
        self.passive_sensors = []
        self.monitor_sensors = []
        self.alias = {} # Dictionary st: key = router/host name, value = list of IP addresses of the router/host
        self.sroutes = {} # Key: Router/Host/sensor id, value = list of static routes to be setup
        super(NetworkTopo1, self).__init__()

    def build( self, **_opts ):

        self.router = self.addNode( 'r1', cls=LinuxRouter, ip='192.168.1.1/24' ) #'14.21.5.38/8'
        self.alias['r1'] = []
        self.sroutes['r1'] = []

        for i in range(1, 3): # 2 subnets
            self.swc[i] = self.addSwitch('s'+str(i))
            hid1 = 'h'+str((i-1)*3)
            hid2 = 'h' + str((i-1)*3+1)
            hid3 = 'h' + str((i-1)*3+2)
            rIP = '192.168.' + str(i) + '.1'
            hIP1 = '192.168.' + str(i) + '.2'
            hIP2 = '192.168.' + str(i) + '.3'
            hIP3 = '192.168.' + str(i) + '.4'
            self.net_hosts.append(self.addHost(hid1, ip=hIP1 + '/24', defaultRoute=rIP))
            self.net_hosts.append(self.addHost(hid2, ip=hIP2 + '/24', defaultRoute=rIP))
            self.net_hosts.append(self.addHost(hid3, ip=hIP3 + '/24', defaultRoute=rIP))
            self.addLink(self.swc[i], self.router, intfName2='r1-eth'+ str(i),
                         params2={'ip': rIP + '/24'})
            self.addLink(hid1, self.swc[i])
            self.addLink(hid2, self.swc[i])
            self.addLink(hid3, self.swc[i])
            self.alias[hid1] = [hIP1]
            self.alias[hid2] = [hIP2]
            self.alias[hid3] = [hIP3]
            self.alias['r1'].append(rIP)
            self.sroutes['r1'].append('ip route add ' + hIP1  + '/32 via ' + hIP1 + ' dev r1-eth'+ str(i))
            self.sroutes['r1'].append('ip route add ' + hIP2  + '/32 via ' + hIP2 + ' dev r1-eth'+ str(i))
            self.sroutes['r1'].append('ip route add ' + hIP3  + '/32 via ' + hIP3 + ' dev r1-eth'+ str(i))
            self.sroutes[hid1] = ['ip route add default via ' + rIP + ' dev ' + hid1 + '-eth0']
            self.sroutes[hid2] = ['ip route add default via ' + rIP + ' dev ' + hid2 + '-eth0']
            self.sroutes[hid3] = ['ip route add default via ' + rIP + ' dev ' + hid3 + '-eth0']

        # In Mininet you can't send simultaneously 2 commands to the same host. To circumvent this limitation
        # we create 3 hosts for each sensor, connected to the same switch: the active host looks for dead nodes,
        # The passive host looks for new nodes, the monitor host runs the topology inference algorithm
        for i in range(1, 3):
            if i == 1:
                if self.sensor1 == True:
                    self.add_sensor(1)
            elif i == 2:
                if self.sensor2 == True:
                    self.add_sensor(2)

    def add_sensor(self,i):
        asid = 'has'+str(i)
        psid = 'hps' + str(i)
        msid = 'hms' + str(i)
        rIP = '192.168.' + str(i) + '.1'
        asIP = '192.168.' + str(i) + '.101' # Active sensor IP
        psIP = '192.168.' + str(i) + '.102' # Passive sensor IP
        msIP = '192.168.' + str(i) + '.103' # Monitor sensor IP (the one that runs iTop)
        self.active_sensors.append(self.addHost(asid, ip=asIP + '/24', defaultRoute=rIP))
        self.passive_sensors.append(self.addHost(psid, ip=psIP + '/24', defaultRoute=rIP))
        self.monitor_sensors.append(self.addHost(msid, ip=msIP + '/24', defaultRoute=rIP))
        self.addLink(asid, self.swc[i])
        self.addLink(psid, self.swc[i])
        self.addLink(msid, self.swc[i])
# The three IP address of the sensor are referred to the monitor sensor, because it is the only one that can actively ask
        self.alias[msid] = [asIP]
        self.alias[msid].append(psIP)
        self.alias[msid].append(msIP)
        self.sroutes['r1'].append('ip route add ' + msIP + '/32 via ' + msIP + ' dev r1-eth' + str(i))
        self.sroutes[asid] = ['ip route add default via ' + rIP + ' dev ' + asid + '-eth0']
        self.sroutes[psid] = ['ip route add default via ' + rIP + ' dev ' + psid + '-eth0']
        self.sroutes[msid] = ['ip route add default via ' + rIP + ' dev ' + msid + '-eth0']


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


class NetworkTopo2( Topo ):
    """
    This topology simulates a network with 20 hosts: ten belong to subnet 192.168.1.0/24 and the other ten
    belong to subnet 192.168.2.0/24. The two subnets are linked together with a router.
    3 options are available:
    one sensor in first subnet,
    one sensor in second subnet,
    one sensor in both subnets.
    """

    def __init__(self, *args, **params):
        '''
        :param sensor1: True if a sensor has to be placed in subnet 192.168.1.0/24
        :param sensor2: True if a sensor has to be placed in subnet 192.168.2.0/24
        '''
        self.sensor1 = False if (params['sensor1'] is None or params['sensor1'] is False) else True # Boolean
        self.sensor2 = False if (params['sensor2'] is None or params['sensor2'] is False) else True  # Boolean
        self.swc = {} # Key: Number of switch, value: switch
        self.net_hosts = []
        self.active_sensors = []
        self.passive_sensors = []
        self.monitor_sensors = []
        self.alias = {} # Dictionary st: key = router/host name, value = list of IP addresses of the router/host
        self.sroutes = {} # Key: Router/Host/sensor id, value = list of static routes to be setup
        super(NetworkTopo2, self).__init__()

    def build( self, **_opts ):

        self.router = self.addNode( 'r1', cls=LinuxRouter, ip='192.168.1.1/24' ) #'14.21.5.38/8'
        self.alias['r1'] = []
        self.sroutes['r1'] = []

        for i in range(1, 3): # 2 subnets
            # Add the switch
            self.swc[i] = self.addSwitch('s'+str(i))
            # Add the router
            rIP = '192.168.' + str(i) + '.1'
            self.addLink(self.swc[i], self.router, intfName2='r1-eth' + str(i),
                         params2={'ip': rIP + '/24'})
            self.alias['r1'].append(rIP)
            # Add the hosts
            for j in range(1,11):
                hid = 'h'+str(((i-1)*10) + j-1)  # Just to make hosts start from zero..
                hIP = '192.168.' + str(i) + '.' + str(j+1)
                self.net_hosts.append(self.addHost(hid, ip=hIP + '/24', defaultRoute=rIP))
                self.addLink(hid, self.swc[i])
                self.alias[hid] = [hIP]
                self.sroutes['r1'].append('ip route add ' + hIP + '/32 via ' + hIP + ' dev r1-eth' + str(i))
                self.sroutes[hid] = ['ip route add default via ' + rIP + ' dev ' + hid + '-eth0']

        # In Mininet you can't send simultaneously 2 commands to the same host. To circumvent this limitation
        # we create 3 hosts for each sensor, connected to the same switch: the active host looks for dead nodes,
        # The passive host looks for new nodes, the monitor host runs the topology inference algorithm
        if self.sensor1 == True:
            self.add_sensor(1)
        if self.sensor2 == True:
            self.add_sensor(2)

    def add_sensor(self,i):
        asid = 'has'+str(i)
        psid = 'hps' + str(i)
        msid = 'hms' + str(i)
        rIP = '192.168.' + str(i) + '.1'
        asIP = '192.168.' + str(i) + '.101' # Active sensor IP
        psIP = '192.168.' + str(i) + '.102' # Passive sensor IP
        msIP = '192.168.' + str(i) + '.103' # Monitor sensor IP (the one that runs iTop)
        self.active_sensors.append(self.addHost(asid, ip=asIP + '/24', defaultRoute=rIP))
        self.passive_sensors.append(self.addHost(psid, ip=psIP + '/24', defaultRoute=rIP))
        self.monitor_sensors.append(self.addHost(msid, ip=msIP + '/24', defaultRoute=rIP))
        self.addLink(asid, self.swc[i])
        self.addLink(psid, self.swc[i])
        self.addLink(msid, self.swc[i])
# The three IP address of the sensor are referred to the monitor sensor, because it is the only one that can actively ask
        self.alias[msid] = [asIP]
        self.alias[msid].append(psIP)
        self.alias[msid].append(msIP)
        self.sroutes['r1'].append('ip route add ' + msIP + '/32 via ' + msIP + ' dev r1-eth' + str(i))
        self.sroutes[asid] = ['ip route add default via ' + rIP + ' dev ' + asid + '-eth0']
        self.sroutes[psid] = ['ip route add default via ' + rIP + ' dev ' + psid + '-eth0']
        self.sroutes[msid] = ['ip route add default via ' + rIP + ' dev ' + msid + '-eth0']


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


class NetworkTopo3( Topo ):
    """
    This topology simulates a network with 100 hosts: 50 belong to subnet 192.168.1.0/24 and the other 50
    belong to subnet 192.168.2.0/24. The two subnets are linked together with a router.
    3 options are available:
    one sensor in first subnet,
    one sensor in second subnet,
    one sensor in both subnets.
    """

    def __init__(self, *args, **params):
        '''
        :param sensor1: True if a sensor has to be placed in subnet 192.168.1.0/24
        :param sensor2: True if a sensor has to be placed in subnet 192.168.2.0/24
        '''
        self.sensor1 = False if (params['sensor1'] is None or params['sensor1'] is False) else True # Boolean
        self.sensor2 = False if (params['sensor2'] is None or params['sensor2'] is False) else True  # Boolean
        self.swc = {} # Key: Number of switch, value: switch
        self.net_hosts = []
        self.active_sensors = []
        self.passive_sensors = []
        self.monitor_sensors = []
        self.alias = {} # Dictionary st: key = router/host name, value = list of IP addresses of the router/host
        self.sroutes = {} # Key: Router/Host/sensor id, value = list of static routes to be setup
        super(NetworkTopo3, self).__init__()

    def build( self, **_opts ):

        self.router = self.addNode( 'r1', cls=LinuxRouter, ip='192.168.1.1/24' ) #'14.21.5.38/8'
        self.alias['r1'] = []
        self.sroutes['r1'] = []

        for i in range(1, 3): # 2 subnets
            # Add the switch
            self.swc[i] = self.addSwitch('s'+str(i))
            # Add the router
            rIP = '192.168.' + str(i) + '.1'
            self.addLink(self.swc[i], self.router, intfName2='r1-eth' + str(i),
                         params2={'ip': rIP + '/24'})
            self.alias['r1'].append(rIP)
            # Add the hosts
            for j in range(1,51):
                hid = 'h'+str(((i-1)*50) + j-1)  # Just to make hosts start from zero..
                hIP = '192.168.' + str(i) + '.' + str(j+1)
                self.net_hosts.append(self.addHost(hid, ip=hIP + '/24', defaultRoute=rIP))
                self.addLink(hid, self.swc[i])
                self.alias[hid] = [hIP]
                self.sroutes['r1'].append('ip route add ' + hIP + '/32 via ' + hIP + ' dev r1-eth' + str(i))
                self.sroutes[hid] = ['ip route add default via ' + rIP + ' dev ' + hid + '-eth0']

        # In Mininet you can't send simultaneously 2 commands to the same host. To circumvent this limitation
        # we create 3 hosts for each sensor, connected to the same switch: the active host looks for dead nodes,
        # The passive host looks for new nodes, the monitor host runs the topology inference algorithm
        if self.sensor1 == True:
            self.add_sensor(1)
        if self.sensor2 == True:
            self.add_sensor(2)

    def add_sensor(self,i):
        asid = 'has'+str(i)
        psid = 'hps' + str(i)
        msid = 'hms' + str(i)
        rIP = '192.168.' + str(i) + '.1'
        asIP = '192.168.' + str(i) + '.101' # Active sensor IP
        psIP = '192.168.' + str(i) + '.102' # Passive sensor IP
        msIP = '192.168.' + str(i) + '.103' # Monitor sensor IP (the one that runs iTop)
        self.active_sensors.append(self.addHost(asid, ip=asIP + '/24', defaultRoute=rIP))
        self.passive_sensors.append(self.addHost(psid, ip=psIP + '/24', defaultRoute=rIP))
        self.monitor_sensors.append(self.addHost(msid, ip=msIP + '/24', defaultRoute=rIP))
        self.addLink(asid, self.swc[i])
        self.addLink(psid, self.swc[i])
        self.addLink(msid, self.swc[i])
# The three IP address of the sensor are referred to the monitor sensor, because it is the only one that can actively ask
        self.alias[msid] = [asIP]
        self.alias[msid].append(psIP)
        self.alias[msid].append(msIP)
        self.sroutes['r1'].append('ip route add ' + msIP + '/32 via ' + msIP + ' dev r1-eth' + str(i))
        self.sroutes[asid] = ['ip route add default via ' + rIP + ' dev ' + asid + '-eth0']
        self.sroutes[psid] = ['ip route add default via ' + rIP + ' dev ' + psid + '-eth0']
        self.sroutes[msid] = ['ip route add default via ' + rIP + ' dev ' + msid + '-eth0']


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

class NetworkTopo4( Topo ):
    """
    This topology simulates a network with three routers.
    Two hosts belong to subnet 12.0.0.0/8, representing the internet.
    Two hosts belong to subnet 192.168.1.0/24, representing the DMZ.
    Two hosts belong to subnet 192.168.2.0/24, representing LAN 1.
    Two hosts belong to subnet 192.168.3.0/24, representing LAN 2.
    Communication possible among all subnets.
    """

    def __init__(self, *args, **params):
        '''
        :param sensor1: True if a sensor has to be placed in subnet 12.0.0.0/8
        :param sensor2: True if a sensor has to be placed in subnet 192.168.1.0/24
        :param sensor2: True if a sensor has to be placed in subnet 192.168.2.0/24
        :param sensor2: True if a sensor has to be placed in subnet 192.168.3.0/24
        '''
        self.sensor1 = False if (params['sensor1'] is None or params['sensor1'] is False) else True
        self.sensor2 = False if (params['sensor2'] is None or params['sensor2'] is False) else True
        self.sensor3 = False if (params['sensor3'] is None or params['sensor3'] is False) else True
        self.sensor4 = False if (params['sensor4'] is None or params['sensor4'] is False) else True
        self.swc = {} # Key: Number of switch, value: switch
        self.net_hosts = []
        self.active_sensors = []
        self.passive_sensors = []
        self.monitor_sensors = []
        self.interface_name = []
        self.alias = {} # Dictionary st: key = router/host name, value = list of IP addresses of the router/host
        self.sroutes = {} # Key: Router/Host/sensor id, value = list of static routes to be setup
        super(NetworkTopo4, self).__init__()

    def build( self, **_opts ):
        # Connect router r1 to Internet Hosts
        r1IP1 = '12.10.5.1'
        self.router1 = self.addNode( 'r1', cls=LinuxRouter, ip=r1IP1+'/8' )
        self.alias['r1'] = []
        self.alias['r1'].append(r1IP1)
        self.sroutes['r1'] = []
        self.swc[1] = self.addSwitch('s1')
        self.addLink(self.swc[1], self.router1, intfName2='r1-eth1', params2={'ip': r1IP1+'/8'})
        self.net_hosts.append(self.addHost('h1', ip='12.10.5.2/8', defaultRoute=r1IP1+'/8'))
        self.addLink('h1', self.swc[1])
        self.alias['h1'] = ['12.10.5.2']
        self.net_hosts.append(self.addHost('h2', ip='12.10.5.3/8', defaultRoute=r1IP1+'/8'))
        self.addLink('h2', self.swc[1])
        self.alias['h2'] = ['12.10.5.3']
        self.sroutes['r1'].append('ip route add 12.10.5.2/8 via 12.10.5.2 dev r1-eth1')
        self.sroutes['r1'].append('ip route add 12.10.5.3/8 via 12.10.5.3 dev r1-eth1')
        self.sroutes['h1'] = ['ip route add default via 12.10.5.1 dev h1-eth0']
        self.sroutes['h2'] = ['ip route add default via 12.10.5.1 dev h2-eth0']

        # Connect the DMZ
        r1IP2 = '192.168.4.1'
        r2IP1 = '192.168.4.2'
        r2IP2 = '192.168.1.1'
        # TODO l' indirizzo di default del router deve corrispondere sempre al' indirizzo della stessa classe degli host che gli sono attaccati (es: r2IP1 non funziona qui!)
        self.router2 = self.addNode('r2', cls=LinuxRouter, ip=r2IP1) #r2IP2
        self.alias['r2'] = []
        self.alias['r1'].append(r1IP2)
        self.alias['r2'].append(r2IP1)
        self.alias['r2'].append(r2IP2)
        self.sroutes['r2'] = []
        self.swc[5] = self.addSwitch('s5')
        self.addLink(self.swc[5], self.router2, intfName2='r2-eth1', params2={'ip': r2IP1+'/24'})
        self.addLink(self.swc[5], self.router1, intfName2='r1-eth2', params2={'ip': r1IP2+'/24'})
        self.swc[2] = self.addSwitch('s2')
        self.addLink(self.swc[2], self.router2, intfName2='r2-eth2',  params2={'ip': r2IP2+'/24'})
        self.net_hosts.append(self.addHost('h3', ip='192.168.1.2/24', defaultRoute=r2IP2+'/24'))
        self.addLink('h3', self.swc[2])
        self.alias['h3'] = ['192.168.1.2']
        self.net_hosts.append(self.addHost('h4', ip='192.168.1.3/24', defaultRoute=r2IP2+'/24'))
        self.addLink('h4', self.swc[2])
        self.alias['h4'] = ['192.168.1.3']
        self.sroutes['h3'] = ['ip route add default via 192.168.1.1 dev h3-eth0']
        self.sroutes['h4'] = ['ip route add default via 192.168.1.1 dev h4-eth0']
        self.sroutes['r1'].append('ip route add 192.168.1.0/24 via 192.168.4.2 dev r1-eth2')
        self.sroutes['r2'].append('ip route add 192.168.2.0/24 via 192.168.4.1 dev r2-eth1')
        self.sroutes['r2'].append('ip route add 192.168.3.0/24 via 192.168.4.1 dev r2-eth1')
        self.sroutes['r2'].append('ip route add 192.168.5.0/24 via 192.168.4.1 dev r2-eth1')
        self.sroutes['r2'].append('ip route add 12.0.0.0/8 via 192.168.4.1 dev r2-eth1')

        # Connect LAN 1 and LAN 2
        r1IP3 = '192.168.5.1'
        r3IP1 = '192.168.5.2'
        r3IP2 = '192.168.2.1'
        r3IP3 = '192.168.3.1'
        self.router3 = self.addNode('r3', cls=LinuxRouter, ip=r3IP1)
        self.alias['r3'] = []
        self.alias['r1'].append(r1IP3)
        self.alias['r3'].append(r3IP1)
        self.alias['r3'].append(r3IP2)
        self.alias['r3'].append(r3IP3)
        self.sroutes['r3'] = []
        self.swc[6] = self.addSwitch('s6')
        # Il primo collegamento switch-router DEVE usare l'indirizzo usato nella definizione del router
        self.addLink(self.swc[6], self.router3, intfName2='r3-eth1', params2={'ip': r3IP1+'/24'})
        self.addLink(self.swc[6], self.router1, intfName2='r1-eth3', params2={'ip': r1IP3+'/24'})
        self.swc[3] = self.addSwitch('s3')
        self.addLink(self.swc[3], self.router3, intfName2='r3-eth2', params2={'ip': r3IP2+'/24'})
        self.net_hosts.append(self.addHost('h5', ip='192.168.2.2/24', defaultRoute=r3IP2+'/24'))
        self.addLink('h5', self.swc[3])
        self.alias['h5'] = ['192.168.2.2']
        self.net_hosts.append(self.addHost('h6', ip='192.168.2.3/24', defaultRoute=r3IP2+'/24'))
        self.addLink('h6', self.swc[3])
        self.alias['h6'] = ['192.168.2.3']
        self.sroutes['h5'] = ['ip route add default via 192.168.2.1 dev h5-eth0']
        self.sroutes['h6'] = ['ip route add default via 192.168.2.1 dev h6-eth0']
        self.sroutes['r1'].append('ip route add 192.168.2.0/24 via 192.168.5.2 dev r1-eth3')
        self.sroutes['r1'].append('ip route add 192.168.3.0/24 via 192.168.5.2 dev r1-eth3')
        self.sroutes['r3'].append('ip route add 192.168.1.0/24 via 192.168.5.1 dev r3-eth1')
        self.sroutes['r3'].append('ip route add 192.168.4.0/24 via 192.168.5.1 dev r3-eth1')
        self.sroutes['r3'].append('ip route add 12.0.0.0/8 via 192.168.5.1 dev r3-eth1')
        self.sroutes['r3'].append('ip route add 12.10.5.2/8 via 192.168.5.1 dev r3-eth1')
        self.swc[4] = self.addSwitch('s4')
        self.addLink(self.swc[4], self.router3, intfName2='r3-eth3', params2={'ip': r3IP3+'/24'})
        self.net_hosts.append(self.addHost('h7', ip='192.168.3.2/24', defaultRoute=r3IP3+'/24'))
        self.addLink('h7', self.swc[4])
        self.alias['h7'] = ['192.168.3.2']
        self.net_hosts.append(self.addHost('h8', ip='192.168.3.3/24', defaultRoute=r3IP3+'/24'))
        self.addLink('h8', self.swc[4])
        self.alias['h8'] = ['192.168.3.3']
        self.sroutes['h7'] = ['ip route add default via 192.168.3.1 dev h7-eth0']
        self.sroutes['h8'] = ['ip route add default via 192.168.3.1 dev h8-eth0']
        if self.sensor1: self.add_sensor_Internet()
        if self.sensor2: self.add_sensor_LAN(1)
        if self.sensor3: self.add_sensor_LAN(2)
        if self.sensor4: self.add_sensor_LAN(3)

    def add_sensor_LAN(self, i):
        asid = 'has' + str(i)
        msid = 'hms' + str(i)
        rIP = '192.168.' + str(i) + '.1'
        asIP = '192.168.' + str(i) + '.101'  # Active sensor IP
        msIP = '192.168.' + str(i) + '.103'  # Monitor sensor IP (the one that runs iTop)
        self.active_sensors.append(self.addHost(asid, ip=asIP + '/24', defaultRoute=rIP))
        if i == 1:
            sensor=self.swc[2]
            intf = 's2-eth1'
        elif i == 2 :
            sensor=self.swc[3]
            intf = 's3-eth1'
        else:
            sensor=self.swc[4]
            intf = 's4-eth1'
        self.passive_sensors.append(sensor)
        self.interface_name.append(intf)
        self.monitor_sensors.append(self.addHost(msid, ip=msIP + '/24', defaultRoute=rIP))
        self.addLink(asid, self.swc[i + 1])
        self.addLink(msid, self.swc[i + 1])
        # The three IP address of the sensor are referred to the monitor sensor, because it is the only one that can actively ask
        self.alias[msid] = [asIP]
        self.alias[msid].append(msIP)
        if i == 1:
            self.sroutes['r2'].append('ip route add ' + msIP + '/32 via ' + msIP + ' dev r2-eth2')
        else:
            self.sroutes['r3'].append('ip route add ' + msIP + '/32 via ' + msIP + ' dev r3-eth' + str(i))
        self.sroutes[asid] = ['ip route add default via ' + rIP + ' dev ' + asid + '-eth0']
        self.sroutes[msid] = ['ip route add default via ' + rIP + ' dev ' + msid + '-eth0']


    def add_sensor_Internet(self):
        asid = 'hasI'
        msid = 'hmsI'
        rIP = '12.10.5.1'
        asIP = '12.10.5.101'  # Active sensor IP
        msIP = '12.10.5.103'  # Monitor sensor IP (the one that runs iTop)
        self.active_sensors.append(self.addHost(asid, ip=asIP + '/8', defaultRoute=rIP))
        self.passive_sensors.append(self.swc[1])
        self.interface_name.append('s1-eth1')
        self.monitor_sensors.append(self.addHost(msid, ip=msIP + '/8', defaultRoute=rIP))
        self.addLink(asid, self.swc[1])
        self.addLink(msid, self.swc[1])
        # The three IP address of the sensor are referred to the monitor sensor, because it is the only one that can actively ask
        self.alias[msid] = [asIP]
        self.alias[msid].append(msIP)
        self.sroutes['r1'].append('ip route add ' + msIP + '/32 via ' + msIP + ' dev r1-eth1')
        self.sroutes[asid] = ['ip route add default via ' + rIP + ' dev ' + asid + '-eth0']
        self.sroutes[msid] = ['ip route add default via ' + rIP + ' dev ' + msid + '-eth0']


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


class NetworkTopo5( Topo ):
    """
    This topology simulates a network with one router and two firewalls.
    Two hosts belong to subnet 12.0.0.0/8, representing the internet.
    Two hosts belong to subnet 192.168.1.0/24, representing the DMZ.
    Two hosts belong to subnet 192.168.2.0/24, representing LAN 1.
    Two hosts belong to subnet 192.168.3.0/24, representing LAN 2.
    Communication is only possible between Internet and DMZ and between LAN1 and LAN2.
    It os possible to put a sensor in each of the subnets.
    """

    def __init__(self, *args, **params):
        '''
        :param sensor1: True if a sensor has to be placed in subnet 12.0.0.0/8
        :param sensor2: True if a sensor has to be placed in subnet 192.168.1.0/24
        :param sensor2: True if a sensor has to be placed in subnet 192.168.2.0/24
        :param sensor2: True if a sensor has to be placed in subnet 192.168.3.0/24
        '''
        self.sensor1 = False if (params['sensor1'] is None or params['sensor1'] is False) else True
        self.sensor2 = False if (params['sensor2'] is None or params['sensor2'] is False) else True
        self.sensor3 = False if (params['sensor3'] is None or params['sensor3'] is False) else True
        self.sensor4 = False if (params['sensor4'] is None or params['sensor4'] is False) else True
        self.swc = {} # Key: Number of switch, value: switch
        self.net_hosts = []
        self.active_sensors = []
        self.passive_sensors = []
        self.monitor_sensors = []
        self.interface_name = []
        self.fw_rules = {} # Key:host name, value: list of rules to be applied
        self.alias = {} # Dictionary st: key = router/host name, value = list of IP addresses of the router/host
        self.sroutes = {} # Key: Router/Host/sensor id, value = list of static routes to be setup
        super(NetworkTopo5, self).__init__()

    def build( self, **_opts ):
        # Connect router r1 to Internet Hosts
        r1IP1 = '12.10.5.1'
        self.router1 = self.addNode( 'r1', cls=LinuxRouter, ip=r1IP1+'/8' )
        self.alias['r1'] = []
        self.alias['r1'].append(r1IP1)
        self.sroutes['r1'] = []
        self.swc[1] = self.addSwitch('s1')
        self.addLink(self.swc[1], self.router1, intfName2='r1-eth1', params2={'ip': r1IP1+'/8'})
        self.net_hosts.append(self.addHost('h1', ip='12.10.5.2/8', defaultRoute=r1IP1+'/8'))
        self.addLink('h1', self.swc[1])
        self.alias['h1'] = ['12.10.5.2']
        self.net_hosts.append(self.addHost('h2', ip='12.10.5.3/8', defaultRoute=r1IP1+'/8'))
        self.addLink('h2', self.swc[1])
        self.alias['h2'] = ['12.10.5.3']
        self.sroutes['r1'].append('ip route add 12.10.5.2/8 via 12.10.5.2 dev r1-eth1')
        self.sroutes['r1'].append('ip route add 12.10.5.3/8 via 12.10.5.3 dev r1-eth1')
        self.sroutes['h1'] = ['ip route add default via 12.10.5.1 dev h1-eth0']
        self.sroutes['h2'] = ['ip route add default via 12.10.5.1 dev h2-eth0']

        # Connect the DMZ
        r1IP2 = '192.168.4.1'
        r2IP1 = '192.168.4.2'
        r2IP2 = '192.168.1.1'
        # TODO l' indirizzo di default del router deve corrispondere sempre al' indirizzo della stessa classe degli host che gli sono attaccati (es: r2IP1 non funziona qui!)
        self.router2 = self.addNode('r2', cls=LinuxRouter, ip=r2IP1) #r2IP2
        self.alias['r2'] = []
        self.alias['r1'].append(r1IP2)
        self.alias['r2'].append(r2IP1)
        self.alias['r2'].append(r2IP2)
        self.sroutes['r2'] = []
        self.swc[5] = self.addSwitch('s5')
        self.addLink(self.swc[5], self.router2, intfName2='r2-eth1', params2={'ip': r2IP1+'/24'})
        self.addLink(self.swc[5], self.router1, intfName2='r1-eth2', params2={'ip': r1IP2+'/24'})
        self.swc[2] = self.addSwitch('s2')
        self.addLink(self.swc[2], self.router2, intfName2='r2-eth2',  params2={'ip': r2IP2+'/24'})
        self.net_hosts.append(self.addHost('h3', ip='192.168.1.2/24', defaultRoute=r2IP2+'/24'))
        self.addLink('h3', self.swc[2])
        self.alias['h3'] = ['192.168.1.2']
        self.net_hosts.append(self.addHost('h4', ip='192.168.1.3/24', defaultRoute=r2IP2+'/24'))
        self.addLink('h4', self.swc[2])
        self.alias['h4'] = ['192.168.1.3']
        self.sroutes['h3'] = ['ip route add default via 192.168.1.1 dev h3-eth0']
        self.sroutes['h4'] = ['ip route add default via 192.168.1.1 dev h4-eth0']
        self.sroutes['r1'].append('ip route add 192.168.1.0/24 via 192.168.4.2 dev r1-eth2')
        self.sroutes['r2'].append('ip route add 192.168.2.0/24 via 192.168.4.1 dev r2-eth1')
        self.sroutes['r2'].append('ip route add 192.168.3.0/24 via 192.168.4.1 dev r2-eth1')
        self.sroutes['r2'].append('ip route add 192.168.5.0/24 via 192.168.4.1 dev r2-eth1')
        self.sroutes['r2'].append('ip route add 12.0.0.0/8 via 192.168.4.1 dev r2-eth1')
        self.fw_rules['r1'] = ['iptables -P FORWARD DROP']
        self.fw_rules['r1'].append('iptables -A FORWARD -i r1-eth1 -s 12.0.0.0/8 -o r1-eth2 -d 192.168.1.0/24 -j ACCEPT')
        self.fw_rules['r1'].append('iptables -A FORWARD -i r1-eth2 -s 192.168.1.0/24 -o r1-eth1 -d 12.0.0.0/8 -j ACCEPT')

        # Connect LAN 1 and LAN 2
        r1IP3 = '192.168.5.1'
        r3IP1 = '192.168.5.2'
        r3IP2 = '192.168.2.1'
        r3IP3 = '192.168.3.1'
        self.router3 = self.addNode('r3', cls=LinuxRouter, ip=r3IP1)
        self.alias['r3'] = []
        self.alias['r1'].append(r1IP3)
        self.alias['r3'].append(r3IP1)
        self.alias['r3'].append(r3IP2)
        self.alias['r3'].append(r3IP3)
        self.sroutes['r3'] = []
        self.swc[6] = self.addSwitch('s6')
        # Il primo collegamento switch-router DEVE usare l'indirizzo usato nella definizione del router
        self.addLink(self.swc[6], self.router3, intfName2='r3-eth1', params2={'ip': r3IP1+'/24'})
        self.addLink(self.swc[6], self.router1, intfName2='r1-eth3', params2={'ip': r1IP3+'/24'})
        self.swc[3] = self.addSwitch('s3')
        self.addLink(self.swc[3], self.router3, intfName2='r3-eth2', params2={'ip': r3IP2+'/24'})
        self.net_hosts.append(self.addHost('h5', ip='192.168.2.2/24', defaultRoute=r3IP2+'/24'))
        self.addLink('h5', self.swc[3])
        self.alias['h5'] = ['192.168.2.2']
        self.net_hosts.append(self.addHost('h6', ip='192.168.2.3/24', defaultRoute=r3IP2+'/24'))
        self.addLink('h6', self.swc[3])
        self.alias['h6'] = ['192.168.2.3']
        self.sroutes['h5'] = ['ip route add default via 192.168.2.1 dev h5-eth0']
        self.sroutes['h6'] = ['ip route add default via 192.168.2.1 dev h6-eth0']
        self.sroutes['r1'].append('ip route add 192.168.2.0/24 via 192.168.5.2 dev r1-eth3')
        self.sroutes['r1'].append('ip route add 192.168.3.0/24 via 192.168.5.2 dev r1-eth3')
        self.sroutes['r3'].append('ip route add 192.168.1.0/24 via 192.168.5.1 dev r3-eth1')
        self.sroutes['r3'].append('ip route add 192.168.4.0/24 via 192.168.5.1 dev r3-eth1')
        self.sroutes['r3'].append('ip route add 12.0.0.0/8 via 192.168.5.1 dev r3-eth1')
        self.sroutes['r3'].append('ip route add 12.10.5.2/8 via 192.168.5.1 dev r3-eth1')
        self.swc[4] = self.addSwitch('s4')
        self.addLink(self.swc[4], self.router3, intfName2='r3-eth3', params2={'ip': r3IP3+'/24'})
        self.net_hosts.append(self.addHost('h7', ip='192.168.3.2/24', defaultRoute=r3IP3+'/24'))
        self.addLink('h7', self.swc[4])
        self.alias['h7'] = ['192.168.3.2']
        self.net_hosts.append(self.addHost('h8', ip='192.168.3.3/24', defaultRoute=r3IP3+'/24'))
        self.addLink('h8', self.swc[4])
        self.alias['h8'] = ['192.168.3.3']
        self.sroutes['h7'] = ['ip route add default via 192.168.3.1 dev h7-eth0']
        self.sroutes['h8'] = ['ip route add default via 192.168.3.1 dev h8-eth0']
        self.fw_rules['r3'] = ['iptables -P FORWARD DROP']
        self.fw_rules['r3'].append('iptables -A FORWARD -i r3-eth2 -s 192.168.2.0/24 -o r3-eth3 -d 192.168.3.0/24 -j ACCEPT')
        self.fw_rules['r3'].append('iptables -A FORWARD -i r3-eth3 -s 192.168.3.0/24 -o r3-eth2 -d 192.168.2.0/24 -j ACCEPT')
        if self.sensor1: self.add_sensor_Internet()
        if self.sensor2: self.add_sensor_LAN(1)
        if self.sensor3: self.add_sensor_LAN(2)
        if self.sensor4: self.add_sensor_LAN(3)

    def add_sensor_LAN(self, i):
        asid = 'has' + str(i)
        msid = 'hms' + str(i)
        rIP = '192.168.' + str(i) + '.1'
        asIP = '192.168.' + str(i) + '.101'  # Active sensor IP
        msIP = '192.168.' + str(i) + '.103'  # Monitor sensor IP (the one that runs iTop)
        self.active_sensors.append(self.addHost(asid, ip=asIP + '/24', defaultRoute=rIP))
        if i == 1:
            sensor=self.swc[2]
            intf = 's2-eth1'
        elif i == 2 :
            sensor=self.swc[3]
            intf = 's3-eth1'
        else:
            sensor=self.swc[4]
            intf = 's4-eth1'
        self.passive_sensors.append(sensor)
        self.interface_name.append(intf)
        self.monitor_sensors.append(self.addHost(msid, ip=msIP + '/24', defaultRoute=rIP))
        self.addLink(asid, self.swc[i + 1])
        self.addLink(msid, self.swc[i + 1])
        # The three IP address of the sensor are referred to the monitor sensor, because it is the only one that can actively ask
        self.alias[msid] = [asIP]
        self.alias[msid].append(msIP)
        if i == 1:
            self.sroutes['r2'].append('ip route add ' + msIP + '/32 via ' + msIP + ' dev r2-eth2')
        else:
            self.sroutes['r3'].append('ip route add ' + msIP + '/32 via ' + msIP + ' dev r3-eth' + str(i))
        self.sroutes[asid] = ['ip route add default via ' + rIP + ' dev ' + asid + '-eth0']
        self.sroutes[msid] = ['ip route add default via ' + rIP + ' dev ' + msid + '-eth0']


    def add_sensor_Internet(self):
        asid = 'hasI'
        msid = 'hmsI'
        rIP = '12.10.5.1'
        asIP = '12.10.5.101'  # Active sensor IP
        msIP = '12.10.5.103'  # Monitor sensor IP (the one that runs iTop)
        self.active_sensors.append(self.addHost(asid, ip=asIP + '/8', defaultRoute=rIP))
        self.passive_sensors.append(self.swc[1])
        self.interface_name.append('s1-eth1')
        self.monitor_sensors.append(self.addHost(msid, ip=msIP + '/8', defaultRoute=rIP))
        self.addLink(asid, self.swc[1])
        self.addLink(msid, self.swc[1])
        # The three IP address of the sensor are referred to the monitor sensor, because it is the only one that can actively ask
        self.alias[msid] = [asIP]
        self.alias[msid].append(msIP)
        self.sroutes['r1'].append('ip route add ' + msIP + '/32 via ' + msIP + ' dev r1-eth1')
        self.sroutes[asid] = ['ip route add default via ' + rIP + ' dev ' + asid + '-eth0']
        self.sroutes[msid] = ['ip route add default via ' + rIP + ' dev ' + msid + '-eth0']


    def add_static_routes(self, net):
        '''Add static routes to the router for subnets not directly visible'''
        for k in self.sroutes.keys():
            for r in self.sroutes[k]:
                net[k].cmd(r)


    def add_firewall_rules(self, net):
        '''Add firewall rules'''
        for k in self.fw_rules.keys():
            for r in self.fw_rules[k]:
                net[k].cmd(r)

    def create_alias_file(self):
        with open('alias', 'w') as f:
            for k in self.alias.keys():
                f.write(k + ' ')
                for ip in self.alias[k]:
                    f.write(ip + ' ')
                f.write('\n')


class NetworkTopo6( Topo ):
    """
    This topology simulates a network with one router.
    Three hosts belong to subnet 12.0.0.0/8, representing the internet.
    Three hosts belong to subnet 192.168.1.0/24, representing the DMZ.
    Three hosts belong to subnet 192.168.2.0/24, representing LAN.
    Communication possible among all subnets.
    """

    def __init__(self, *args, **params):
        '''
        :param sensor1: True if a sensor has to be placed in subnet 12.0.0.0/8
        :param sensor2: True if a sensor has to be placed in subnet 192.168.1.0/24
        :param sensor2: True if a sensor has to be placed in subnet 192.168.2.0/24
        '''
        self.sensor1 = False if (params['sensor1'] is None or params['sensor1'] is False) else True
        self.sensor2 = False if (params['sensor2'] is None or params['sensor2'] is False) else True
        self.sensor3 = False if (params['sensor3'] is None or params['sensor3'] is False) else True
        self.swc = {} # Key: Number of switch, value: switch
        self.net_hosts = []
        self.active_sensors = []
        self.passive_sensors = []
        self.monitor_sensors = []
        self.interface_name = []
        self.alias = {} # Dictionary st: key = router/host name, value = list of IP addresses of the router/host
        self.sroutes = {} # Key: Router/Host/sensor id, value = list of static routes to be setup
        super(NetworkTopo6, self).__init__()

    def build( self, **_opts ):
        # Connect router r1 to Internet Hosts
        r1IP1 = '12.10.5.1'
        self.router1 = self.addNode( 'r1', cls=LinuxRouter, ip=r1IP1+'/8' )
        self.alias['r1'] = []
        self.alias['r1'].append(r1IP1)
        self.sroutes['r1'] = []
        self.swc[1] = self.addSwitch('s1')
        self.addLink(self.swc[1], self.router1, intfName2='r1-eth1', params2={'ip': r1IP1+'/8'})
        self.net_hosts.append(self.addHost('h1', ip='12.10.5.2/8', defaultRoute=r1IP1+'/8'))
        self.addLink('h1', self.swc[1])
        self.alias['h1'] = ['12.10.5.2']
        self.net_hosts.append(self.addHost('h2', ip='12.10.5.3/8', defaultRoute=r1IP1+'/8'))
        self.addLink('h2', self.swc[1])
        self.alias['h2'] = ['12.10.5.3']
        self.net_hosts.append(self.addHost('h3', ip='12.10.5.4/8', defaultRoute=r1IP1+'/8'))
        self.addLink('h3', self.swc[1])
        self.alias['h3'] = ['12.10.5.4']
        #self.sroutes['r1'].append('ip route add 12.0.0.0/8 via 12.10.5.2 dev r1-eth1')
        #self.sroutes['r1'].append('ip route add 12.10.5.3/8 via 12.10.5.3 dev r1-eth1')
        #self.sroutes['r1'].append('ip route add 12.10.5.4/8 via 12.10.5.4 dev r1-eth1')
        self.sroutes['h1'] = ['ip route add default via 12.10.5.1 dev h1-eth0']
        self.sroutes['h2'] = ['ip route add default via 12.10.5.1 dev h2-eth0']
        self.sroutes['h3'] = ['ip route add default via 12.10.5.1 dev h3-eth0']

        # Connect the DMZ
        r1IP2 = '192.168.1.1'
        self.alias['r1'].append(r1IP2)
        self.swc[2] = self.addSwitch('s2')
        self.addLink(self.swc[2], self.router1, intfName2='r1-eth2', params2={'ip': r1IP2+'/24'})
        self.net_hosts.append(self.addHost('h5', ip='192.168.1.2/24', defaultRoute=r1IP2+'/24'))
        self.addLink('h5', self.swc[2])
        self.alias['h5'] = ['192.168.1.2']
        self.net_hosts.append(self.addHost('h4', ip='192.168.1.3/24', defaultRoute=r1IP2+'/24'))
        self.addLink('h4', self.swc[2])
        self.alias['h4'] = ['192.168.1.3']
        self.net_hosts.append(self.addHost('h6', ip='192.168.1.4/24', defaultRoute=r1IP2 + '/24'))
        self.addLink('h6', self.swc[2])
        self.alias['h6'] = ['192.168.1.4']
        self.sroutes['h4'] = ['ip route add default via 192.168.1.1 dev h4-eth0']
        self.sroutes['h5'] = ['ip route add default via 192.168.1.1 dev h5-eth0']
        self.sroutes['h6'] = ['ip route add default via 192.168.1.1 dev h6-eth0']
        #self.sroutes['r1'].append('ip route add 192.168.1.0/24 via 192.168.4.2 dev r1-eth2')

        # Connect LAN
        r1IP3 = '192.168.2.1'
        self.alias['r1'].append(r1IP3)
        self.swc[3] = self.addSwitch('s3')
        # Il primo collegamento switch-router DEVE usare l'indirizzo usato nella definizione del router)
        self.addLink(self.swc[3], self.router1, intfName2='r1-eth3', params2={'ip': r1IP3+'/24'})
        self.net_hosts.append(self.addHost('h9', ip='192.168.2.2/24', defaultRoute=r1IP3+'/24'))
        self.addLink('h9', self.swc[3])
        self.alias['h9'] = ['192.168.2.2']
        self.net_hosts.append(self.addHost('h7', ip='192.168.2.3/24', defaultRoute=r1IP3+'/24'))
        self.addLink('h7', self.swc[3])
        self.alias['h7'] = ['192.168.2.3']
        self.net_hosts.append(self.addHost('h8', ip='192.168.2.4/24', defaultRoute=r1IP3 + '/24'))
        self.addLink('h8', self.swc[3])
        self.alias['h8'] = ['192.168.2.4']
        self.sroutes['h8'] = ['ip route add default via 192.168.2.1 dev h8-eth0']
        self.sroutes['h7'] = ['ip route add default via 192.168.2.1 dev h7-eth0']
        self.sroutes['h9'] = ['ip route add default via 192.168.2.1 dev h9-eth0']
        if self.sensor1: self.add_sensor_Internet()
        if self.sensor2: self.add_sensor_LAN(1)
        if self.sensor3: self.add_sensor_LAN(2)

    def add_sensor_LAN(self, i):
        asid = 'has' + str(i)
        msid = 'hms' + str(i)
        rIP = '192.168.' + str(i) + '.1'
        asIP = '192.168.' + str(i) + '.101'  # Active sensor IP
        msIP = '192.168.' + str(i) + '.103'  # Monitor sensor IP (the one that runs iTop)
        self.active_sensors.append(self.addHost(asid, ip=asIP + '/24', defaultRoute=rIP))
        if i == 1:
            sensor=self.swc[2]
            intf = 's2-eth1'
        else:
            sensor = self.swc[3]
            intf = 's3-eth1'
        self.passive_sensors.append(sensor)
        self.interface_name.append(intf)
        self.monitor_sensors.append(self.addHost(msid, ip=msIP + '/24', defaultRoute=rIP))
        self.addLink(asid, self.swc[i + 1])
        self.addLink(msid, self.swc[i + 1])
        # The three IP address of the sensor are referred to the monitor sensor, because it is the only one that can actively ask
        self.alias[msid] = [asIP]
        self.alias[msid].append(msIP)
        #if i == 1:
        #    self.sroutes['r2'].append('ip route add ' + msIP + '/32 via ' + msIP + ' dev r2-eth2')
        #else:
        #    self.sroutes['r3'].append('ip route add ' + msIP + '/32 via ' + msIP + ' dev r3-eth' + str(i))
        self.sroutes[asid] = ['ip route add default via ' + rIP + ' dev ' + asid + '-eth0']
        self.sroutes[msid] = ['ip route add default via ' + rIP + ' dev ' + msid + '-eth0']


    def add_sensor_Internet(self):
        asid = 'hasI'
        msid = 'hmsI'
        rIP = '12.10.5.1'
        asIP = '12.10.5.101'  # Active sensor IP
        msIP = '12.10.5.103'  # Monitor sensor IP (the one that runs iTop)
        self.active_sensors.append(self.addHost(asid, ip=asIP + '/8', defaultRoute=rIP))
        self.passive_sensors.append(self.swc[1])
        self.interface_name.append('s1-eth1')
        self.monitor_sensors.append(self.addHost(msid, ip=msIP + '/8', defaultRoute=rIP))
        self.addLink(asid, self.swc[1])
        self.addLink(msid, self.swc[1])
        # The three IP address of the sensor are referred to the monitor sensor, because it is the only one that can actively ask
        self.alias[msid] = [asIP]
        self.alias[msid].append(msIP)
        self.sroutes['r1'].append('ip route add ' + msIP + '/32 via ' + msIP + ' dev r1-eth1')
        self.sroutes[asid] = ['ip route add default via ' + rIP + ' dev ' + asid + '-eth0']
        self.sroutes[msid] = ['ip route add default via ' + rIP + ' dev ' + msid + '-eth0']


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

class NetworkTopo7( Topo ):
    """
    This topology simulates a network with one firewall.
    Three hosts belong to subnet 12.0.0.0/8, representing the internet.
    Three hosts belong to subnet 192.168.1.0/24, representing the DMZ.
    Three hosts belong to subnet 192.168.2.0/24, representing LAN.
    Communication is possible only inside the LAN or between Internet and DMZ.
    """

    def __init__(self, *args, **params):
        '''
        :param sensor1: True if a sensor has to be placed in subnet 12.0.0.0/8
        :param sensor2: True if a sensor has to be placed in subnet 192.168.1.0/24
        :param sensor2: True if a sensor has to be placed in subnet 192.168.2.0/24
        '''
        self.sensor1 = False if (params['sensor1'] is None or params['sensor1'] is False) else True
        self.sensor2 = False if (params['sensor2'] is None or params['sensor2'] is False) else True
        self.sensor3 = False if (params['sensor3'] is None or params['sensor3'] is False) else True
        self.swc = {} # Key: Number of switch, value: switch
        self.net_hosts = []
        self.active_sensors = []
        self.passive_sensors = []
        self.monitor_sensors = []
        self.interface_name = []
        self.fw_rules = {}  # Key:host name, value: list of rules to be applied
        self.alias = {} # Dictionary st: key = router/host name, value = list of IP addresses of the router/host
        self.sroutes = {} # Key: Router/Host/sensor id, value = list of static routes to be setup
        super(NetworkTopo7, self).__init__()

    def build( self, **_opts ):
        # Connect router r1 to Internet Hosts
        r1IP1 = '12.10.5.1'
        self.router1 = self.addNode('r1', cls=LinuxRouter, ip=r1IP1+'/8' )
        self.alias['r1'] = []
        self.alias['r1'].append(r1IP1)
        self.sroutes['r1'] = []
        self.swc[1] = self.addSwitch('s1')
        self.addLink(self.swc[1], self.router1, intfName2='r1-eth1', params2={'ip': r1IP1+'/8'})
        self.net_hosts.append(self.addHost('h1', ip='12.10.5.2/8', defaultRoute=r1IP1+'/8'))
        self.addLink('h1', self.swc[1])
        self.alias['h1'] = ['12.10.5.2']
        self.net_hosts.append(self.addHost('h2', ip='12.10.5.3/8', defaultRoute=r1IP1+'/8'))
        self.addLink('h2', self.swc[1])
        self.alias['h2'] = ['12.10.5.3']
        self.net_hosts.append(self.addHost('h3', ip='12.10.5.4/8', defaultRoute=r1IP1+'/8'))
        self.addLink('h3', self.swc[1])
        self.alias['h3'] = ['12.10.5.4']
        #self.sroutes['r1'].append('ip route add 12.0.0.0/8 via 12.10.5.2 dev r1-eth1')
        #self.sroutes['r1'].append('ip route add 12.10.5.3/8 via 12.10.5.3 dev r1-eth1')
        #self.sroutes['r1'].append('ip route add 12.10.5.4/8 via 12.10.5.4 dev r1-eth1')
        self.sroutes['h1'] = ['ip route add default via 12.10.5.1 dev h1-eth0']
        self.sroutes['h2'] = ['ip route add default via 12.10.5.1 dev h2-eth0']
        self.sroutes['h3'] = ['ip route add default via 12.10.5.1 dev h3-eth0']

        # Connect the DMZ
        r1IP2 = '192.168.1.1'
        self.alias['r1'].append(r1IP2)
        self.swc[2] = self.addSwitch('s2')
        self.addLink(self.swc[2], self.router1, intfName2='r1-eth2', params2={'ip': r1IP2+'/24'})
        self.net_hosts.append(self.addHost('h5', ip='192.168.1.2/24', defaultRoute=r1IP2+'/24'))
        self.addLink('h5', self.swc[2])
        self.alias['h5'] = ['192.168.1.2']
        self.net_hosts.append(self.addHost('h4', ip='192.168.1.3/24', defaultRoute=r1IP2+'/24'))
        self.addLink('h4', self.swc[2])
        self.alias['h4'] = ['192.168.1.3']
        self.net_hosts.append(self.addHost('h6', ip='192.168.1.4/24', defaultRoute=r1IP2 + '/24'))
        self.addLink('h6', self.swc[2])
        self.alias['h6'] = ['192.168.1.4']
        self.sroutes['h4'] = ['ip route add default via 192.168.1.1 dev h4-eth0']
        self.sroutes['h5'] = ['ip route add default via 192.168.1.1 dev h5-eth0']
        self.sroutes['h6'] = ['ip route add default via 192.168.1.1 dev h6-eth0']
        #self.sroutes['r1'].append('ip route add 192.168.1.0/24 via 192.168.4.2 dev r1-eth2')

        # Connect LAN
        r1IP3 = '192.168.2.1'
        self.alias['r1'].append(r1IP3)
        self.swc[3] = self.addSwitch('s3')
        # Il primo collegamento switch-router DEVE usare l'indirizzo usato nella definizione del router)
        self.addLink(self.swc[3], self.router1, intfName2='r1-eth3', params2={'ip': r1IP3+'/24'})
        self.net_hosts.append(self.addHost('h9', ip='192.168.2.2/24', defaultRoute=r1IP3+'/24'))
        self.addLink('h9', self.swc[3])
        self.alias['h9'] = ['192.168.2.2']
        self.net_hosts.append(self.addHost('h7', ip='192.168.2.3/24', defaultRoute=r1IP3+'/24'))
        self.addLink('h7', self.swc[3])
        self.alias['h7'] = ['192.168.2.3']
        self.net_hosts.append(self.addHost('h8', ip='192.168.2.4/24', defaultRoute=r1IP3 + '/24'))
        self.addLink('h8', self.swc[3])
        self.alias['h8'] = ['192.168.2.4']
        self.sroutes['h8'] = ['ip route add default via 192.168.2.1 dev h8-eth0']
        self.sroutes['h7'] = ['ip route add default via 192.168.2.1 dev h7-eth0']
        self.sroutes['h9'] = ['ip route add default via 192.168.2.1 dev h9-eth0']

        self.fw_rules['r1'] = ['iptables -P FORWARD DROP']
        self.fw_rules['r1'].append('iptables -A FORWARD -i r1-eth1 -s 12.0.0.0/8 -o r1-eth2 -d 192.168.1.0/24 -j ACCEPT')
        self.fw_rules['r1'].append('iptables -A FORWARD -i r1-eth2 -s 192.168.1.0/24 -o r1-eth1 -d 12.0.0.0/8 -j ACCEPT')

        if self.sensor1: self.add_sensor_Internet()
        if self.sensor2: self.add_sensor_LAN(1)
        if self.sensor3: self.add_sensor_LAN(2)

    def add_sensor_LAN(self, i):
        asid = 'has' + str(i)
        msid = 'hms' + str(i)
        rIP = '192.168.' + str(i) + '.1'
        asIP = '192.168.' + str(i) + '.101'  # Active sensor IP
        msIP = '192.168.' + str(i) + '.103'  # Monitor sensor IP (the one that runs iTop)
        self.active_sensors.append(self.addHost(asid, ip=asIP + '/24', defaultRoute=rIP))
        if i == 1:
            sensor=self.swc[2]
            intf = 's2-eth1'
        else:
            sensor = self.swc[3]
            intf = 's3-eth1'
        self.passive_sensors.append(sensor)
        self.interface_name.append(intf)
        self.monitor_sensors.append(self.addHost(msid, ip=msIP + '/24', defaultRoute=rIP))
        self.addLink(asid, self.swc[i + 1])
        self.addLink(msid, self.swc[i + 1])
        # The three IP address of the sensor are referred to the monitor sensor, because it is the only one that can actively ask
        self.alias[msid] = [asIP]
        self.alias[msid].append(msIP)
        #if i == 1:
        #    self.sroutes['r2'].append('ip route add ' + msIP + '/32 via ' + msIP + ' dev r2-eth2')
        #else:
        #    self.sroutes['r3'].append('ip route add ' + msIP + '/32 via ' + msIP + ' dev r3-eth' + str(i))
        self.sroutes[asid] = ['ip route add default via ' + rIP + ' dev ' + asid + '-eth0']
        self.sroutes[msid] = ['ip route add default via ' + rIP + ' dev ' + msid + '-eth0']


    def add_sensor_Internet(self):
        asid = 'hasI'
        msid = 'hmsI'
        rIP = '12.10.5.1'
        asIP = '12.10.5.101'  # Active sensor IP
        msIP = '12.10.5.103'  # Monitor sensor IP (the one that runs iTop)
        self.active_sensors.append(self.addHost(asid, ip=asIP + '/8', defaultRoute=rIP))
        self.passive_sensors.append(self.swc[1])
        self.interface_name.append('s1-eth1')
        self.monitor_sensors.append(self.addHost(msid, ip=msIP + '/8', defaultRoute=rIP))
        self.addLink(asid, self.swc[1])
        self.addLink(msid, self.swc[1])
        # The three IP address of the sensor are referred to the monitor sensor, because it is the only one that can actively ask
        self.alias[msid] = [asIP]
        self.alias[msid].append(msIP)
        self.sroutes['r1'].append('ip route add ' + msIP + '/32 via ' + msIP + ' dev r1-eth1')
        self.sroutes[asid] = ['ip route add default via ' + rIP + ' dev ' + asid + '-eth0']
        self.sroutes[msid] = ['ip route add default via ' + rIP + ' dev ' + msid + '-eth0']


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
    def add_firewall_rules(self, net):
        '''Add firewall rules'''
        for k in self.fw_rules.keys():
            for r in self.fw_rules[k]:
                net[k].cmd(r)

class NetworkTopo8( Topo ):
    """
    This topology simulates a network with three routers.
    Two hosts belong to subnet 12.0.0.0/8, representing the internet.
    Two hosts belong to subnet 192.168.1.0/24, representing the DMZ.
    Two hosts belong to subnet 192.168.2.0/24, representing LAN 1.
    Two hosts belong to subnet 192.168.3.0/24, representing LAN 2.
    Router1, the one that connects the three subnets, is anonymous.
    """

    def __init__(self, *args, **params):
        '''
        :param sensor1: True if a sensor has to be placed in subnet 12.0.0.0/8
        :param sensor2: True if a sensor has to be placed in subnet 192.168.1.0/24
        :param sensor2: True if a sensor has to be placed in subnet 192.168.2.0/24
        :param sensor2: True if a sensor has to be placed in subnet 192.168.3.0/24
        '''
        self.sensor1 = False if (params['sensor1'] is None or params['sensor1'] is False) else True
        self.sensor2 = False if (params['sensor2'] is None or params['sensor2'] is False) else True
        self.sensor3 = False if (params['sensor3'] is None or params['sensor3'] is False) else True
        self.sensor4 = False if (params['sensor4'] is None or params['sensor4'] is False) else True
        self.swc = {} # Key: Number of switch, value: switch
        self.net_hosts = []
        self.active_sensors = []
        self.passive_sensors = []
        self.monitor_sensors = []
        self.interface_name = []
        self.alias = {} # Dictionary st: key = router/host name, value = list of IP addresses of the router/host
        self.sroutes = {} # Key: Router/Host/sensor id, value = list of static routes to be setup
        super(NetworkTopo8, self).__init__()

    def build( self, **_opts ):
        # Connect router r1 to Internet Hosts
        r1IP1 = '12.10.5.1'
        self.router1 = self.addNode( 'r1', cls=LinuxRouter, ip=r1IP1+'/8' )
        self.alias['r1'] = []
        self.alias['r1'].append(r1IP1)
        self.sroutes['r1'] = []
        self.swc[1] = self.addSwitch('s1')
        self.addLink(self.swc[1], self.router1, intfName2='r1-eth1', params2={'ip': r1IP1+'/8'})
        self.net_hosts.append(self.addHost('h1', ip='12.10.5.2/8', defaultRoute=r1IP1+'/8'))
        self.addLink('h1', self.swc[1])
        self.alias['h1'] = ['12.10.5.2']
        self.net_hosts.append(self.addHost('h2', ip='12.10.5.3/8', defaultRoute=r1IP1+'/8'))
        self.addLink('h2', self.swc[1])
        self.alias['h2'] = ['12.10.5.3']
        self.sroutes['r1'].append('ip route add 12.10.5.2/8 via 12.10.5.2 dev r1-eth1')
        self.sroutes['r1'].append('ip route add 12.10.5.3/8 via 12.10.5.3 dev r1-eth1')
        self.sroutes['h1'] = ['ip route add default via 12.10.5.1 dev h1-eth0']
        self.sroutes['h2'] = ['ip route add default via 12.10.5.1 dev h2-eth0']

        # Connect the DMZ
        r1IP2 = '192.168.4.1'
        r2IP1 = '192.168.4.2'
        r2IP2 = '192.168.1.1'
        # TODO l' indirizzo di default del router deve corrispondere sempre al' indirizzo della stessa classe degli host che gli sono attaccati (es: r2IP1 non funziona qui!)
        self.router2 = self.addNode('r2', cls=LinuxRouter, ip=r2IP1) #r2IP2
        self.alias['r2'] = []
        self.alias['r1'].append(r1IP2)
        self.alias['r2'].append(r2IP1)
        self.alias['r2'].append(r2IP2)
        self.sroutes['r2'] = []
        self.swc[5] = self.addSwitch('s5')
        self.addLink(self.swc[5], self.router2, intfName2='r2-eth1', params2={'ip': r2IP1+'/24'})
        self.addLink(self.swc[5], self.router1, intfName2='r1-eth2', params2={'ip': r1IP2+'/24'})
        self.swc[2] = self.addSwitch('s2')
        self.addLink(self.swc[2], self.router2, intfName2='r2-eth2',  params2={'ip': r2IP2+'/24'})
        self.net_hosts.append(self.addHost('h3', ip='192.168.1.2/24', defaultRoute=r2IP2+'/24'))
        self.addLink('h3', self.swc[2])
        self.alias['h3'] = ['192.168.1.2']
        self.net_hosts.append(self.addHost('h4', ip='192.168.1.3/24', defaultRoute=r2IP2+'/24'))
        self.addLink('h4', self.swc[2])
        self.alias['h4'] = ['192.168.1.3']
        self.sroutes['h3'] = ['ip route add default via 192.168.1.1 dev h3-eth0']
        self.sroutes['h4'] = ['ip route add default via 192.168.1.1 dev h4-eth0']
        self.sroutes['r1'].append('ip route add 192.168.1.0/24 via 192.168.4.2 dev r1-eth2')
        self.sroutes['r2'].append('ip route add 192.168.2.0/24 via 192.168.4.1 dev r2-eth1')
        self.sroutes['r2'].append('ip route add 192.168.3.0/24 via 192.168.4.1 dev r2-eth1')
        self.sroutes['r2'].append('ip route add 192.168.5.0/24 via 192.168.4.1 dev r2-eth1')
        self.sroutes['r2'].append('ip route add 12.0.0.0/8 via 192.168.4.1 dev r2-eth1')

        # Connect LAN 1 and LAN 2
        r1IP3 = '192.168.5.1'
        r3IP1 = '192.168.5.2'
        r3IP2 = '192.168.2.1'
        r3IP3 = '192.168.3.1'
        self.router3 = self.addNode('r3', cls=LinuxRouter, ip=r3IP1)
        self.alias['r3'] = []
        self.alias['r1'].append(r1IP3)
        self.alias['r3'].append(r3IP1)
        self.alias['r3'].append(r3IP2)
        self.alias['r3'].append(r3IP3)
        self.sroutes['r3'] = []
        self.swc[6] = self.addSwitch('s6')
        # Il primo collegamento switch-router DEVE usare l'indirizzo usato nella definizione del router
        self.addLink(self.swc[6], self.router3, intfName2='r3-eth1', params2={'ip': r3IP1+'/24'})
        self.addLink(self.swc[6], self.router1, intfName2='r1-eth3', params2={'ip': r1IP3+'/24'})
        self.swc[3] = self.addSwitch('s3')
        self.addLink(self.swc[3], self.router3, intfName2='r3-eth2', params2={'ip': r3IP2+'/24'})
        self.net_hosts.append(self.addHost('h5', ip='192.168.2.2/24', defaultRoute=r3IP2+'/24'))
        self.addLink('h5', self.swc[3])
        self.alias['h5'] = ['192.168.2.2']
        self.net_hosts.append(self.addHost('h6', ip='192.168.2.3/24', defaultRoute=r3IP2+'/24'))
        self.addLink('h6', self.swc[3])
        self.alias['h6'] = ['192.168.2.3']
        self.sroutes['h5'] = ['ip route add default via 192.168.2.1 dev h5-eth0']
        self.sroutes['h6'] = ['ip route add default via 192.168.2.1 dev h6-eth0']
        self.sroutes['r1'].append('ip route add 192.168.2.0/24 via 192.168.5.2 dev r1-eth3')
        self.sroutes['r1'].append('ip route add 192.168.3.0/24 via 192.168.5.2 dev r1-eth3')
        self.sroutes['r3'].append('ip route add 192.168.1.0/24 via 192.168.5.1 dev r3-eth1')
        self.sroutes['r3'].append('ip route add 192.168.4.0/24 via 192.168.5.1 dev r3-eth1')
        self.sroutes['r3'].append('ip route add 12.0.0.0/8 via 192.168.5.1 dev r3-eth1')
        self.sroutes['r3'].append('ip route add 12.10.5.2/8 via 192.168.5.1 dev r3-eth1')
        self.swc[4] = self.addSwitch('s4')
        self.addLink(self.swc[4], self.router3, intfName2='r3-eth3', params2={'ip': r3IP3+'/24'})
        self.net_hosts.append(self.addHost('h7', ip='192.168.3.2/24', defaultRoute=r3IP3+'/24'))
        self.addLink('h7', self.swc[4])
        self.alias['h7'] = ['192.168.3.2']
        self.net_hosts.append(self.addHost('h8', ip='192.168.3.3/24', defaultRoute=r3IP3+'/24'))
        self.addLink('h8', self.swc[4])
        self.alias['h8'] = ['192.168.3.3']
        self.sroutes['h7'] = ['ip route add default via 192.168.3.1 dev h7-eth0']
        self.sroutes['h8'] = ['ip route add default via 192.168.3.1 dev h8-eth0']
        if self.sensor1: self.add_sensor_Internet()
        if self.sensor2: self.add_sensor_LAN(1)
        if self.sensor3: self.add_sensor_LAN(2)
        if self.sensor4: self.add_sensor_LAN(3)

    def add_sensor_LAN(self, i):
        asid = 'has' + str(i)
        msid = 'hms' + str(i)
        rIP = '192.168.' + str(i) + '.1'
        asIP = '192.168.' + str(i) + '.101'  # Active sensor IP
        msIP = '192.168.' + str(i) + '.103'  # Monitor sensor IP (the one that runs iTop)
        self.active_sensors.append(self.addHost(asid, ip=asIP + '/24', defaultRoute=rIP))
        if i == 1:
            sensor=self.swc[2]
            intf = 's2-eth1'
        elif i == 2 :
            sensor=self.swc[3]
            intf = 's3-eth1'
        else:
            sensor=self.swc[4]
            intf = 's4-eth1'
        self.passive_sensors.append(sensor)
        self.interface_name.append(intf)
        self.monitor_sensors.append(self.addHost(msid, ip=msIP + '/24', defaultRoute=rIP))
        self.addLink(asid, self.swc[i + 1])
        self.addLink(msid, self.swc[i + 1])
        # The three IP address of the sensor are referred to the monitor sensor, because it is the only one that can actively ask
        self.alias[msid] = [asIP]
        self.alias[msid].append(msIP)
        if i == 1:
            self.sroutes['r2'].append('ip route add ' + msIP + '/32 via ' + msIP + ' dev r2-eth2')
        else:
            self.sroutes['r3'].append('ip route add ' + msIP + '/32 via ' + msIP + ' dev r3-eth' + str(i))
        self.sroutes[asid] = ['ip route add default via ' + rIP + ' dev ' + asid + '-eth0']
        self.sroutes[msid] = ['ip route add default via ' + rIP + ' dev ' + msid + '-eth0']


    def add_sensor_Internet(self):
        asid = 'hasI'
        msid = 'hmsI'
        rIP = '12.10.5.1'
        asIP = '12.10.5.101'  # Active sensor IP
        msIP = '12.10.5.103'  # Monitor sensor IP (the one that runs iTop)
        self.active_sensors.append(self.addHost(asid, ip=asIP + '/8', defaultRoute=rIP))
        self.passive_sensors.append(self.swc[1])
        self.interface_name.append('s1-eth1')
        self.monitor_sensors.append(self.addHost(msid, ip=msIP + '/8', defaultRoute=rIP))
        self.addLink(asid, self.swc[1])
        self.addLink(msid, self.swc[1])
        # The three IP address of the sensor are referred to the monitor sensor, because it is the only one that can actively ask
        self.alias[msid] = [asIP]
        self.alias[msid].append(msIP)
        self.sroutes['r1'].append('ip route add ' + msIP + '/32 via ' + msIP + ' dev r1-eth1')
        self.sroutes[asid] = ['ip route add default via ' + rIP + ' dev ' + asid + '-eth0']
        self.sroutes[msid] = ['ip route add default via ' + rIP + ' dev ' + msid + '-eth0']


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

    def add_firewall_rules(self, net):
        '''Add firewall rules to make router r1 anonymous'''
        net['r1'].cmd('iptables -P OUTPUT DROP')

class NetworkTopo9( Topo ):
    """
    This topology simulates a network with three routers.
    Two hosts belong to subnet 12.0.0.0/8, representing the internet.
    Two hosts belong to subnet 192.168.1.0/24, representing the DMZ.
    Two hosts belong to subnet 192.168.2.0/24, representing LAN 1.
    Two hosts belong to subnet 192.168.3.0/24, representing LAN 2.
    Router1, the one that connects the three subnets, is blocking.
    """

    def __init__(self, *args, **params):
        '''
        :param sensor1: True if a sensor has to be placed in subnet 12.0.0.0/8
        :param sensor2: True if a sensor has to be placed in subnet 192.168.1.0/24
        :param sensor2: True if a sensor has to be placed in subnet 192.168.2.0/24
        :param sensor2: True if a sensor has to be placed in subnet 192.168.3.0/24
        '''
        self.sensor1 = False if (params['sensor1'] is None or params['sensor1'] is False) else True
        self.sensor2 = False if (params['sensor2'] is None or params['sensor2'] is False) else True
        self.sensor3 = False if (params['sensor3'] is None or params['sensor3'] is False) else True
        self.sensor4 = False if (params['sensor4'] is None or params['sensor4'] is False) else True
        self.swc = {} # Key: Number of switch, value: switch
        self.net_hosts = []
        self.active_sensors = []
        self.passive_sensors = []
        self.monitor_sensors = []
        self.interface_name = []
        self.alias = {} # Dictionary st: key = router/host name, value = list of IP addresses of the router/host
        self.sroutes = {} # Key: Router/Host/sensor id, value = list of static routes to be setup
        super(NetworkTopo9, self).__init__()

    def build( self, **_opts ):
        # Connect router r1 to Internet Hosts
        r1IP1 = '12.10.5.1'
        self.router1 = self.addNode( 'r1', cls=LinuxRouter, ip=r1IP1+'/8' )
        self.alias['r1'] = []
        self.alias['r1'].append(r1IP1)
        self.sroutes['r1'] = []
        self.swc[1] = self.addSwitch('s1')
        self.addLink(self.swc[1], self.router1, intfName2='r1-eth1', params2={'ip': r1IP1+'/8'})
        self.net_hosts.append(self.addHost('h1', ip='12.10.5.2/8', defaultRoute=r1IP1+'/8'))
        self.addLink('h1', self.swc[1])
        self.alias['h1'] = ['12.10.5.2']
        self.net_hosts.append(self.addHost('h2', ip='12.10.5.3/8', defaultRoute=r1IP1+'/8'))
        self.addLink('h2', self.swc[1])
        self.alias['h2'] = ['12.10.5.3']
        self.sroutes['r1'].append('ip route add 12.10.5.2/8 via 12.10.5.2 dev r1-eth1')
        self.sroutes['r1'].append('ip route add 12.10.5.3/8 via 12.10.5.3 dev r1-eth1')
        self.sroutes['h1'] = ['ip route add default via 12.10.5.1 dev h1-eth0']
        self.sroutes['h2'] = ['ip route add default via 12.10.5.1 dev h2-eth0']

        # Connect the DMZ
        r1IP2 = '192.168.4.1'
        r2IP1 = '192.168.4.2'
        r2IP2 = '192.168.1.1'
        # TODO l' indirizzo di default del router deve corrispondere sempre al' indirizzo della stessa classe degli host che gli sono attaccati (es: r2IP1 non funziona qui!)
        self.router2 = self.addNode('r2', cls=LinuxRouter, ip=r2IP1) #r2IP2
        self.alias['r2'] = []
        self.alias['r1'].append(r1IP2)
        self.alias['r2'].append(r2IP1)
        self.alias['r2'].append(r2IP2)
        self.sroutes['r2'] = []
        self.swc[5] = self.addSwitch('s5')
        self.addLink(self.swc[5], self.router2, intfName2='r2-eth1', params2={'ip': r2IP1+'/24'})
        self.addLink(self.swc[5], self.router1, intfName2='r1-eth2', params2={'ip': r1IP2+'/24'})
        self.swc[2] = self.addSwitch('s2')
        self.addLink(self.swc[2], self.router2, intfName2='r2-eth2',  params2={'ip': r2IP2+'/24'})
        self.net_hosts.append(self.addHost('h3', ip='192.168.1.2/24', defaultRoute=r2IP2+'/24'))
        self.addLink('h3', self.swc[2])
        self.alias['h3'] = ['192.168.1.2']
        self.net_hosts.append(self.addHost('h4', ip='192.168.1.3/24', defaultRoute=r2IP2+'/24'))
        self.addLink('h4', self.swc[2])
        self.alias['h4'] = ['192.168.1.3']
        self.sroutes['h3'] = ['ip route add default via 192.168.1.1 dev h3-eth0']
        self.sroutes['h4'] = ['ip route add default via 192.168.1.1 dev h4-eth0']
        self.sroutes['r1'].append('ip route add 192.168.1.0/24 via 192.168.4.2 dev r1-eth2')
        self.sroutes['r2'].append('ip route add 192.168.2.0/24 via 192.168.4.1 dev r2-eth1')
        self.sroutes['r2'].append('ip route add 192.168.3.0/24 via 192.168.4.1 dev r2-eth1')
        self.sroutes['r2'].append('ip route add 192.168.5.0/24 via 192.168.4.1 dev r2-eth1')
        self.sroutes['r2'].append('ip route add 12.0.0.0/8 via 192.168.4.1 dev r2-eth1')

        # Connect LAN 1 and LAN 2
        r1IP3 = '192.168.5.1'
        r3IP1 = '192.168.5.2'
        r3IP2 = '192.168.2.1'
        r3IP3 = '192.168.3.1'
        self.router3 = self.addNode('r3', cls=LinuxRouter, ip=r3IP1)
        self.alias['r3'] = []
        self.alias['r1'].append(r1IP3)
        self.alias['r3'].append(r3IP1)
        self.alias['r3'].append(r3IP2)
        self.alias['r3'].append(r3IP3)
        self.sroutes['r3'] = []
        self.swc[6] = self.addSwitch('s6')
        # Il primo collegamento switch-router DEVE usare l'indirizzo usato nella definizione del router
        self.addLink(self.swc[6], self.router3, intfName2='r3-eth1', params2={'ip': r3IP1+'/24'})
        self.addLink(self.swc[6], self.router1, intfName2='r1-eth3', params2={'ip': r1IP3+'/24'})
        self.swc[3] = self.addSwitch('s3')
        self.addLink(self.swc[3], self.router3, intfName2='r3-eth2', params2={'ip': r3IP2+'/24'})
        self.net_hosts.append(self.addHost('h5', ip='192.168.2.2/24', defaultRoute=r3IP2+'/24'))
        self.addLink('h5', self.swc[3])
        self.alias['h5'] = ['192.168.2.2']
        self.net_hosts.append(self.addHost('h6', ip='192.168.2.3/24', defaultRoute=r3IP2+'/24'))
        self.addLink('h6', self.swc[3])
        self.alias['h6'] = ['192.168.2.3']
        self.sroutes['h5'] = ['ip route add default via 192.168.2.1 dev h5-eth0']
        self.sroutes['h6'] = ['ip route add default via 192.168.2.1 dev h6-eth0']
        self.sroutes['r1'].append('ip route add 192.168.2.0/24 via 192.168.5.2 dev r1-eth3')
        self.sroutes['r1'].append('ip route add 192.168.3.0/24 via 192.168.5.2 dev r1-eth3')
        self.sroutes['r3'].append('ip route add 192.168.1.0/24 via 192.168.5.1 dev r3-eth1')
        self.sroutes['r3'].append('ip route add 192.168.4.0/24 via 192.168.5.1 dev r3-eth1')
        self.sroutes['r3'].append('ip route add 12.0.0.0/8 via 192.168.5.1 dev r3-eth1')
        self.sroutes['r3'].append('ip route add 12.10.5.2/8 via 192.168.5.1 dev r3-eth1')
        self.swc[4] = self.addSwitch('s4')
        self.addLink(self.swc[4], self.router3, intfName2='r3-eth3', params2={'ip': r3IP3+'/24'})
        self.net_hosts.append(self.addHost('h7', ip='192.168.3.2/24', defaultRoute=r3IP3+'/24'))
        self.addLink('h7', self.swc[4])
        self.alias['h7'] = ['192.168.3.2']
        self.net_hosts.append(self.addHost('h8', ip='192.168.3.3/24', defaultRoute=r3IP3+'/24'))
        self.addLink('h8', self.swc[4])
        self.alias['h8'] = ['192.168.3.3']
        self.sroutes['h7'] = ['ip route add default via 192.168.3.1 dev h7-eth0']
        self.sroutes['h8'] = ['ip route add default via 192.168.3.1 dev h8-eth0']
        if self.sensor1: self.add_sensor_Internet()
        if self.sensor2: self.add_sensor_LAN(1)
        if self.sensor3: self.add_sensor_LAN(2)
        if self.sensor4: self.add_sensor_LAN(3)

    def add_sensor_LAN(self, i):
        asid = 'has' + str(i)
        msid = 'hms' + str(i)
        rIP = '192.168.' + str(i) + '.1'
        asIP = '192.168.' + str(i) + '.101'  # Active sensor IP
        msIP = '192.168.' + str(i) + '.103'  # Monitor sensor IP (the one that runs iTop)
        self.active_sensors.append(self.addHost(asid, ip=asIP + '/24', defaultRoute=rIP))
        if i == 1:
            sensor=self.swc[2]
            intf = 's2-eth1'
        elif i == 2 :
            sensor=self.swc[3]
            intf = 's3-eth1'
        else:
            sensor=self.swc[4]
            intf = 's4-eth1'
        self.passive_sensors.append(sensor)
        self.interface_name.append(intf)
        self.monitor_sensors.append(self.addHost(msid, ip=msIP + '/24', defaultRoute=rIP))
        self.addLink(asid, self.swc[i + 1])
        self.addLink(msid, self.swc[i + 1])
        # The three IP address of the sensor are referred to the monitor sensor, because it is the only one that can actively ask
        self.alias[msid] = [asIP]
        self.alias[msid].append(msIP)
        if i == 1:
            self.sroutes['r2'].append('ip route add ' + msIP + '/32 via ' + msIP + ' dev r2-eth2')
        else:
            self.sroutes['r3'].append('ip route add ' + msIP + '/32 via ' + msIP + ' dev r3-eth' + str(i))
        self.sroutes[asid] = ['ip route add default via ' + rIP + ' dev ' + asid + '-eth0']
        self.sroutes[msid] = ['ip route add default via ' + rIP + ' dev ' + msid + '-eth0']


    def add_sensor_Internet(self):
        asid = 'hasI'
        msid = 'hmsI'
        rIP = '12.10.5.1'
        asIP = '12.10.5.101'  # Active sensor IP
        msIP = '12.10.5.103'  # Monitor sensor IP (the one that runs iTop)
        self.active_sensors.append(self.addHost(asid, ip=asIP + '/8', defaultRoute=rIP))
        self.passive_sensors.append(self.swc[1])
        self.interface_name.append('s1-eth1')
        self.monitor_sensors.append(self.addHost(msid, ip=msIP + '/8', defaultRoute=rIP))
        self.addLink(asid, self.swc[1])
        self.addLink(msid, self.swc[1])
        # The three IP address of the sensor are referred to the monitor sensor, because it is the only one that can actively ask
        self.alias[msid] = [asIP]
        self.alias[msid].append(msIP)
        self.sroutes['r1'].append('ip route add ' + msIP + '/32 via ' + msIP + ' dev r1-eth1')
        self.sroutes[asid] = ['ip route add default via ' + rIP + ' dev ' + asid + '-eth0']
        self.sroutes[msid] = ['ip route add default via ' + rIP + ' dev ' + msid + '-eth0']


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

    def add_firewall_rules(self, net):
        '''Add firewall rules to make router r1 anonymous'''
        net['r1'].cmd('iptables -P FORWARD DROP')
        net['r1'].cmd('iptables -P INPUT DROP')
        net['r1'].cmd('iptables -P OUTPUT DROP')

class NetworkTopo11( Topo ):
    """
    This topology simulates a network with 4 routers/firewall and 4 subnets (plus an Internet Access).
    One host belongs to subnet 12.0.0.0/8, representing the internet.
    Seven hosts and a sensor belong to subnet 192.168.1.0/24, representing LAN1.
    Seven hosts and a sensor belong to subnet 192.168.2.0/24, representing LAN2.
    Seven hosts and a sensor belong to subnet 192.168.3.0/24, representing LAN3.
    Seven hosts and a sensor belong to subnet 192.168.4.0/24, representing LAN3.
    Router1(FW1) allows only the communication between h11 and h31;
    Router2(FW2) allows only the communication between h21 and h31;
    Router3(FW3) allows only the communication between h31 and h41;
    RouterI(FW4) allows the communication between any Internet host and any host in the DMZ.

    LAN1 - |FW1| - -  LAN2 - |FW3| - DMZ - |FW4| - INTERNET
                   /
    LAN3 - |FW2| /

    """

    def __init__(self, *args, **params):
        '''
        :param sensor1: True if a sensor has to be placed in subnet 12.0.0.0/8
        :param sensor2: True if a sensor has to be placed in subnet 192.168.1.0/24
        :param sensor2: True if a sensor has to be placed in subnet 192.168.2.0/24
        :param sensor2: True if a sensor has to be placed in subnet 192.168.3.0/24
        '''
        self.sensor1 = False if (params['sensor1'] is None or params['sensor1'] is False) else True
        self.sensor2 = False if (params['sensor2'] is None or params['sensor2'] is False) else True
        self.sensor3 = False if (params['sensor3'] is None or params['sensor3'] is False) else True
        self.sensor4 = False if (params['sensor4'] is None or params['sensor4'] is False) else True
        self.swc = {} # Key: Number of switch, value: switch
        self.net_hosts = []
        self.active_sensors = []
        self.passive_sensors = []
        self.monitor_sensors = []
        self.interface_name = []
        self.alias = {} # Dictionary st: key = router/host name, value = list of IP addresses of the router/host
        self.sroutes = {} # Key: Router/Host/sensor id, value = list of static routes to be setup
        super(NetworkTopo11, self).__init__()

    def build( self, **_opts ):
        # Connect router r4 to Internet Host hI
        r4IP1 = '12.10.5.1'
        self.router4 = self.addNode( 'r4', cls=LinuxRouter, ip=r4IP1+'/8' )
        self.alias['r4'] = []
        self.alias['r4'].append(r4IP1)
        self.sroutes['r4'] = []
        self.swc[5] = self.addSwitch('s5')
        self.addLink(self.swc[5], self.router4, intfName2='r4-eth1', params2={'ip': r4IP1+'/8'})
        self.net_hosts.append(self.addHost('hI', ip='12.10.5.2/8', defaultRoute=r4IP1+'/8'))
        self.addLink('hI', self.swc[5])
        self.alias['hI'] = ['12.10.5.2']
        self.sroutes['hI'] = ['ip route add 0.0.0.0/0 via ' + r4IP1 + ' dev hI-eth0']

        # Connect the DMZ
        r4IP2 = '192.168.4.1'
        r3IP1 = '192.168.4.2'
        self.router3 = self.addNode('r3', cls=LinuxRouter, ip=r3IP1)
        self.alias['r3'] = []
        self.alias['r3'].append(r3IP1)
        self.alias['r4'].append(r4IP2)
        self.sroutes['r3'] = []
        self.swc[4] = self.addSwitch('s4')
        self.addLink(self.swc[4], self.router3, intfName2='r3-eth1', params2={'ip': r3IP1+'/24'})
        self.addLink(self.swc[4], self.router4, intfName2='r4-eth2', params2={'ip': r4IP2+'/24'})
        self.add_hosts_DMZ(r4IP2)

        # Connect LAN2
        r3IP2 = '192.168.2.1'
        r1IP1 = '192.168.2.2'
        r2IP1 = '192.168.2.3'
        self.router2 = self.addNode('r2', cls=LinuxRouter, ip=r2IP1)
        self.router1 = self.addNode('r1', cls=LinuxRouter, ip=r1IP1)
        self.alias['r2'] = []
        self.alias['r1'] = []
        self.alias['r1'].append(r1IP1)
        self.alias['r2'].append(r2IP1)
        self.alias['r3'].append(r3IP2)
        self.swc[2] = self.addSwitch('s2')
        self.addLink(self.swc[2], self.router3, intfName2='r3-eth2',  params2={'ip': r3IP2+'/24'})
        self.addLink(self.swc[2], self.router2, intfName2='r2-eth1',  params2={'ip': r2IP1+'/24'})
        self.addLink(self.swc[2], self.router1, intfName2='r1-eth1',  params2={'ip': r3IP1+'/24'})
        self.add_hosts_LAN(2, r3IP2)

        # Connect LAN3
        r2IP2 = '192.168.3.1'
        self.alias['r2'].append(r2IP2)
        self.swc[3] = self.addSwitch('s3')
        self.addLink(self.swc[3], self.router2, intfName2='r2-eth2', params2={'ip': r2IP2 + '/24'})
        self.add_hosts_LAN(3, r2IP2)

        # Connect LAN1
        r1IP2 = '192.168.1.1'
        self.alias['r1'].append(r1IP2)
        self.swc[1] = self.addSwitch('s1')
        self.addLink(self.swc[1], self.router1, intfName2='r1-eth2', params2={'ip': r1IP2 + '/24'})
        self.add_hosts_LAN(1, r1IP2)

        # Adds routes to routers/firewalls for subnets not directly visible
        self.sroutes['r1'] = []
        self.sroutes['r2'] = []
        self.sroutes['r3'] = []
        self.sroutes['r4'] = []
        self.sroutes['r1'].append('ip route add 192.168.4.0/24 via 192.168.2.1 dev r1-eth1')
        self.sroutes['r1'].append('ip route add 192.168.3.0/24 via 192.168.2.3 dev r1-eth1')
        self.sroutes['r1'].append('ip route add 12.0.0.0/8 via 192.168.2.1 dev r1-eth1')
        self.sroutes['r2'].append('ip route add 192.168.4.0/24 via 192.168.2.1 dev r2-eth1')
        self.sroutes['r2'].append('ip route add 192.168.1.0/24 via 192.168.2.2 dev r2-eth1')
        self.sroutes['r2'].append('ip route add 12.0.0.0/8 via 192.168.2.1 dev r2-eth1')
        self.sroutes['r3'].append('ip route add 192.168.1.0/24 via 192.168.2.2 dev r3-eth2')
        self.sroutes['r3'].append('ip route add 192.168.3.0/24 via 192.168.2.3 dev r3-eth2')
        self.sroutes['r3'].append('ip route add 12.0.0.0/8 via 192.168.4.1 dev r3-eth1')
        self.sroutes['r4'].append('ip route add 192.168.1.0/24 via 192.168.4.2 dev r4-eth2')
        self.sroutes['r4'].append('ip route add 192.168.2.0/24 via 192.168.4.2 dev r4-eth2')
        self.sroutes['r4'].append('ip route add 192.168.3.0/24 via 192.168.4.2 dev r4-eth2')

        if self.sensor1:
            self.add_sensor_to_switch(1)
            self.interface_name.append('s1-eth1')
        if self.sensor2:
            self.add_sensor_to_switch(2)
            self.interface_name.append('s2-eth1')
        if self.sensor3:
            self.add_sensor_to_switch(3)
            self.interface_name.append('s3-eth1')
        if self.sensor4:
            self.add_sensor_to_switch(4)
            self.interface_name.append('s4-eth2')

    def add_hosts_DMZ(self, r4IP2):
        ''' Adds the hosts to the DMZ switch'''
        self.net_hosts.append(self.addHost('h41', ip='192.168.4.11/24', defaultRoute=r4IP2 + '/24'))
        self.addLink('h41', self.swc[4])
        self.alias['h41'] = ['192.168.4.11']
        self.sroutes['h41'] = ['ip route add 0.0.0.0/0 via ' + r4IP2 + ' dev h41-eth0']
        self.net_hosts.append(self.addHost('h42', ip='192.168.4.12/24', defaultRoute=r4IP2 + '/24'))
        self.addLink('h42', self.swc[4])
        self.alias['h42'] = ['192.168.4.12']
        self.sroutes['h42'] = ['ip route add 0.0.0.0/0 via ' + r4IP2 + ' dev h42-eth0']
        self.net_hosts.append(self.addHost('h43', ip='192.168.4.13/24', defaultRoute=r4IP2 + '/24'))
        self.addLink('h43', self.swc[4])
        self.alias['h43'] = ['192.168.4.13']
        self.sroutes['h43'] = ['ip route add 0.0.0.0/0 via ' + r4IP2 + ' dev h43-eth0']
        self.net_hosts.append(self.addHost('h44', ip='192.168.4.14/24', defaultRoute=r4IP2 + '/24'))
        self.addLink('h44', self.swc[4])
        self.alias['h44'] = ['192.168.4.14']
        self.sroutes['h44'] = ['ip route add 0.0.0.0/0 via ' + r4IP2 + ' dev h44-eth0']
        self.net_hosts.append(self.addHost('h45', ip='192.168.4.15/24', defaultRoute=r4IP2 + '/24'))
        self.addLink('h45', self.swc[4])
        self.alias['h45'] = ['192.168.4.15']
        self.sroutes['h45'] = ['ip route add 0.0.0.0/0 via ' + r4IP2 + ' dev h45-eth0']
        self.net_hosts.append(self.addHost('h46', ip='192.168.4.16/24', defaultRoute=r4IP2 + '/24'))
        self.addLink('h46', self.swc[4])
        self.alias['h46'] = ['192.168.4.16']
        self.sroutes['h46'] = ['ip route add 0.0.0.0/0 via ' + r4IP2 + ' dev h46-eth0']
        self.net_hosts.append(self.addHost('h47', ip='192.168.4.17/24', defaultRoute=r4IP2 + '/24'))
        self.addLink('h47', self.swc[4])
        self.alias['h47'] = ['192.168.4.17']
        self.sroutes['h47'] = ['ip route add 0.0.0.0/0 via ' + r4IP2 + ' dev h47-eth0']
        # TODO VA AGGIUNTA ROTTA DI DEFAULT AGLI HOST h21 ip route add 0.0.0.0/0 via 192.168.2.2 dev h21-eth0

    def add_hosts_LAN(self, i, rIP):
        '''
        Adds the hosts to the DMZ switch
        @param i: Number of LAN to which hosts are added
        @param rIP: IP of the hosts' default router
        '''
        h_ = 'h' + str(i) # Prefix of the host name
        ip_ = '192.168.' + str(i) # Prefix of the IP address
        self.net_hosts.append(self.addHost( h_+'1', ip=ip_+'.11/24', defaultRoute=rIP + '/24'))
        self.addLink(h_+'1', self.swc[i])
        self.alias[h_+'1'] = [ip_+'.11']
        self.sroutes[h_+'1'] = ['ip route add 0.0.0.0/0 via ' + rIP + ' dev ' + h_+'1-eth0']
        self.net_hosts.append(self.addHost( h_+'2', ip=ip_+'.12/24', defaultRoute=rIP + '/24'))
        self.addLink(h_+'2', self.swc[i])
        self.alias[h_+'2'] = [ip_+'.12']
        self.sroutes[h_ + '2'] = ['ip route add 0.0.0.0/0 via ' + rIP + ' dev ' + h_ + '2-eth0']
        self.net_hosts.append(self.addHost( h_+'3', ip=ip_+'.13/24', defaultRoute=rIP + '/24'))
        self.addLink(h_+'3', self.swc[i])
        self.alias[h_+'3'] = [ip_+'.13']
        self.sroutes[h_ + '3'] = ['ip route add 0.0.0.0/0 via ' + rIP + ' dev ' + h_ + '3-eth0']
        self.net_hosts.append(self.addHost(h_+'4', ip=ip_+'.14/24', defaultRoute=rIP + '/24'))
        self.addLink(h_+'4', self.swc[i])
        self.alias[h_+'4'] = [ip_+'.14']
        self.sroutes[h_ + '4'] = ['ip route add 0.0.0.0/0 via ' + rIP + ' dev ' + h_ + '4-eth0']
        self.net_hosts.append(self.addHost(h_+'5', ip=ip_+'.15/24', defaultRoute=rIP + '/24'))
        self.addLink(h_+'5', self.swc[i])
        self.alias[h_+'5'] = [ip_+'.15']
        self.sroutes[h_ + '5'] = ['ip route add 0.0.0.0/0 via ' + rIP + ' dev ' + h_ + '5-eth0']
        self.net_hosts.append(self.addHost(h_+'6', ip=ip_+'.16/24', defaultRoute=rIP + '/24'))
        self.addLink(h_+'6', self.swc[i])
        self.alias[h_+'6'] = [ip_+'.16']
        self.sroutes[h_ + '6'] = ['ip route add 0.0.0.0/0 via ' + rIP + ' dev ' + h_ + '6-eth0']
        self.net_hosts.append(self.addHost(h_+'7', ip=ip_+'.17/24', defaultRoute=rIP + '/24'))
        self.addLink(h_+'7', self.swc[i])
        self.alias[h_+'7'] = [ip_+'.17']
        self.sroutes[h_ + '7'] = ['ip route add 0.0.0.0/0 via ' + rIP + ' dev ' + h_ + '7-eth0']

    def add_sensor_to_switch(self, i):
        '''
        Adds the sensor to the proper switch.
        @param i: number of the switch the sensor is attached to
        '''
        asid = 'has' + str(i)
        msid = 'hms' + str(i)
        rIP = '192.168.' + str(i) + '.1'
        asIP = '192.168.' + str(i) + '.9'  # Active sensor IP
        msIP = '192.168.' + str(i) + '.10'  # Monitor sensor IP (the one that runs iTop)
        self.active_sensors.append(self.addHost(asid, ip=asIP + '/24', defaultRoute=rIP))
        self.passive_sensors.append(self.swc[i]) #TODO check
        self.monitor_sensors.append(self.addHost(msid, ip=msIP + '/24', defaultRoute=rIP))
        self.addLink(asid, self.swc[i])
        self.addLink(msid, self.swc[i])
        # The three IP address of the sensor are referred to the monitor sensor, because it is the only one that can actively ask
        self.alias[msid] = [asIP]
        self.alias[msid].append(msIP)
        self.sroutes[asid] = ['ip route add default via ' + rIP + ' dev ' + asid + '-eth0']
        self.sroutes[msid] = ['ip route add default via ' + rIP + ' dev ' + msid + '-eth0']


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

    def add_firewall_rules(self, net):
        '''Add firewall rules to make router r1 anonymous'''
        # TODO
        net['r1'].cmd('iptables -P FORWARD DROP')
        #net['r1'].cmd('iptables -P INPUT DROP')
        #net['r1'].cmd('iptables -P OUTPUT DROP')
        net['r1'].cmd('iptables -I FORWARD -s 192.168.1.11 -d 192.168.2.11 -j ACCEPT')
        net['r1'].cmd('iptables -I FORWARD -s 192.168.2.11 -d 192.168.1.11 -j ACCEPT')
        net['r2'].cmd('iptables -P FORWARD DROP')
        #net['r2'].cmd('iptables -P INPUT DROP')
        #net['r2'].cmd('iptables -P OUTPUT DROP')
        net['r2'].cmd('iptables -I FORWARD -s 192.168.3.11 -d 192.168.2.11 -j ACCEPT')
        net['r2'].cmd('iptables -I FORWARD -s 192.168.2.11 -d 192.168.3.11 -j ACCEPT')
        net['r3'].cmd('iptables -P FORWARD DROP')
        #net['r3'].cmd('iptables -P INPUT DROP')
        #net['r3'].cmd('iptables -P OUTPUT DROP')
        net['r3'].cmd('iptables -I FORWARD -s 192.168.2.11 -d 192.168.4.11 -j ACCEPT')
        net['r3'].cmd('iptables -I FORWARD -s 192.168.4.11 -d 192.168.2.11 -j ACCEPT')
        net['r3'].cmd('iptables -I FORWARD -s 192.168.2.0/24 -j ACCEPT')
        net['r4'].cmd('iptables -P FORWARD DROP')
        #net['r4'].cmd('iptables -P INPUT DROP')
        #net['r4'].cmd('iptables -P OUTPUT DROP')
        net['r4'].cmd('iptables -I FORWARD -s 0.0.0.0/0 -d 192.168.4.12 -j ACCEPT')
        net['r4'].cmd('iptables -I FORWARD -s 192.168.4.12 -j ACCEPT')
        net['r4'].cmd('iptables -I FORWARD -s 192.168.4.0/24 -j ACCEPT')