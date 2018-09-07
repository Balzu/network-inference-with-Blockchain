# coding=utf-8

from create_merge_topo import *
import pdb
import time
from sensor import *

def stop_net(net):
    net.stop()    

def start_net():
    ''' Start Mininet Topology'''
    topo = NetworkTopo()
    net = Mininet( topo=topo )
    add_static_routes(net)
    net.start()
    s = sensor('h11', 5, net, 'file_config_prova/client1_config.json', max_fail=3,
               known_ips=['192.168.1.4', '192.168.12.2', '192.168.1.2'], simulation=True, readmit = False)
    s.start()
    time.sleep(10)
    h11 = net['h11']
    h21 = net['h21']
    h61 = net['h61']
    h71 = net['h71']
    net.pingAll()
    #net.interact()
    return net


if __name__ == '__main__':

    net = start_net()
    '''choice = raw_input("Type 'Y' to run sensors s1 (on router r1) "
                       "and s4 (on router r4).\nType 'Q' to quit the Mininet.\n")
    if choice == 'Y' or choice == 'y' or choice == 'Yes' or choice == 'YES':
        net['r1'].cmd('python start_sensor.py s1 5 file_config_prova/clientR1_config.json')
        net['r4'].cmd('python start_sensor.py s4 5 file_config_prova/clientR4_config.json')
    elif choice == 'Q' or choice == 'q':
        stop_net(net)
    choice = raw_input("Type 'Q' to quit the Mininet.\n")
    if choice == 'Q' or choice == 'q':
        stop_net(net)
    '''


   

