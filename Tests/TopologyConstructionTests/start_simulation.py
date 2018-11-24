# coding=utf-8

import os, sys, pdb, time
from threading import Thread, Lock, Condition
topo_path = os.path.abspath(os.path.join('..', '..',  'Topology'))
sen_path = os.path.abspath(os.path.join('..', '..',  'Sensor'))
blk_path = os.path.abspath(os.path.join('..', '..',  'Blockchain'))
sys.path.insert(0, topo_path)
sys.path.insert(0, sen_path)
sys.path.insert(0, blk_path)
from create_merge_topo import *
from sensor import *
from client import *
from run import *
from argparse import ArgumentParser


def parse_cmd_args():
    parser = ArgumentParser(description = "Runs a simulation on a given Mininet topology")
    parser.add_argument("-n", "--number",  dest="num", required=True, type = int,
                        help="Specify the network simulation to be run")
    parser.add_argument("-e", "--experiments",
                        dest="experiments", type=int,
                        help="Specify the number of times that the simulation must be carried out")
    return parser.parse_args()

def simulation_one(num):
    '''
    Runs the simulation number one. Experiment one is run 'num' times. Network topology 1 is used
    '''
    os.system('rm -rf topo_exp1')
    os.system('mkdir topo_exp1')
    for i in range(num):
        os.system('sudo mn -c')
        experiment_one(i)
        time.sleep(20) # Time to close sockets..

def simulation_two(num):
    '''
    Runs the simulation number two. Experiment two is run 'num' times. Network topology 2 is used
    '''
    os.system('rm -rf topo_exp2')
    os.system('mkdir topo_exp2')
    os.system('sudo mn -c')
    for i in range(num):
        os.system('sudo python run.py -n 2 -id ' + str(i))
        time.sleep(30)

def simulation_three(num):
    '''
    Runs the simulation number three. Experiment three is run 'num' times. Network topology 3 is used
    '''
    os.system('rm -rf topo_exp3')
    os.system('mkdir topo_exp3')
    os.system('sudo mn -c')
    for i in range(num):
        os.system('sudo python run.py -n 3 -id ' + str(i))
        time.sleep(30)

def simulation_four():
    '''
    Runs the simulation number four. Experiment four is run 'num' times with various combinations of sensors (1,2,3 or 4).
    Network topology 4 is used.
    '''
    os.system('rm -rf topo_exp4')
    os.system('mkdir topo_exp4')
    os.system('mkdir topo_exp4/one_sensor')
    os.system('mkdir topo_exp4/two_sensors')
    os.system('mkdir topo_exp4/three_sensors')
    os.system('mkdir topo_exp4/four_sensors')
    os.system('sudo mn -c')
    # First element of the pair: command. Second element: number of times the cmd has to be executed
    cmd1s = [   ('sudo python run.py -n 4 -s1 -sub one_sensor -id ', 5),
                ('sudo python run.py -n 4 -s2 -sub one_sensor -id ', 5),
                ('sudo python run.py -n 4 -s3 -sub one_sensor -id ', 5),
                ('sudo python run.py -n 4 -s4 -sub one_sensor -id ', 5)
            ]
    cmd2s = [   ('sudo python run.py -n 4 -s1 -s2 -sub two_sensors -id ', 3),
                ('sudo python run.py -n 4 -s1 -s3 -sub two_sensors -id ', 3),
                ('sudo python run.py -n 4 -s1 -s4 -sub two_sensors -id ', 3),
                ('sudo python run.py -n 4 -s2 -s3 -sub two_sensors -id ', 3),
                ('sudo python run.py -n 4 -s2 -s4 -sub two_sensors -id ', 4),
                ('sudo python run.py -n 4 -s3 -s4 -sub two_sensors -id ', 4)
            ]
    cmd3s = [   ('sudo python run.py -n 4 -s1 -s2 -s3 -sub three_sensors -id ', 5),
                ('sudo python run.py -n 4 -s1 -s2 -s4 -sub three_sensors -id ', 5),
                ('sudo python run.py -n 4 -s1 -s3 -s4 -sub three_sensors -id ', 5),
                ('sudo python run.py -n 4 -s2 -s3 -s4 -sub three_sensors -id ', 5)
            ]
    cmd4s = [   ('sudo python run.py -n 4 -s1 -s2 -s3 -s4 -sub four_sensors -id ', 20)
            ]
    commands = [cmd1s, cmd2s, cmd3s, cmd4s]
    for cmdlist in commands:
        id = 0
        for pair in cmdlist:
            for i in range(pair[1]):
                try:
                    os.system(pair[0] + str(id))
                    id += 1
                    time.sleep(25)
                except Exception as e:
                    with open("error", "w") as file:
                        file.write(str(e))

def simulation_five():
    '''
    Runs the simulation number five. Experiment five is run 'num' times with various combinations of sensors (1,2,3 or 4).
    Network topology 5 is used.
    '''
    os.system('rm -rf topo_exp5')
    os.system('mkdir topo_exp5')
    os.system('mkdir topo_exp5/one_sensor')
    os.system('mkdir topo_exp5/two_sensors')
    os.system('mkdir topo_exp5/three_sensors')
    os.system('mkdir topo_exp5/four_sensors')
    os.system('sudo mn -c')
    # First element of the pair: command. Second element: number of times the cmd has to be executed
    cmd1s = [   ('sudo python run.py -n 5 -s1 -sub one_sensor -id ', 5),
                ('sudo python run.py -n 5 -s2 -sub one_sensor -id ', 5),
                ('sudo python run.py -n 5 -s3 -sub one_sensor -id ', 5),
                ('sudo python run.py -n 5 -s4 -sub one_sensor -id ', 5)
            ]
    cmd2s = [   ('sudo python run.py -n 5 -s1 -s2 -sub two_sensors -id ', 3),
                ('sudo python run.py -n 5 -s1 -s3 -sub two_sensors -id ', 3),
                ('sudo python run.py -n 5 -s1 -s4 -sub two_sensors -id ', 3),
                ('sudo python run.py -n 5 -s2 -s3 -sub two_sensors -id ', 3),
                ('sudo python run.py -n 5 -s2 -s4 -sub two_sensors -id ', 4),
                ('sudo python run.py -n 5 -s3 -s4 -sub two_sensors -id ', 4)
            ]
    cmd3s = [   ('sudo python run.py -n 5 -s1 -s2 -s3 -sub three_sensors -id ', 5),
                ('sudo python run.py -n 5 -s1 -s2 -s4 -sub three_sensors -id ', 5),
                ('sudo python run.py -n 5 -s1 -s3 -s4 -sub three_sensors -id ', 5),
                ('sudo python run.py -n 5 -s2 -s3 -s4 -sub three_sensors -id ', 5)
            ]
    cmd4s = [   ('sudo python run.py -n 5 -s1 -s2 -s3 -s4 -sub four_sensors -id ', 20)
            ]
    commands = [cmd1s, cmd2s, cmd3s, cmd4s]
    for cmdlist in commands:
        id = 0
        for pair in cmdlist:
            for i in range(pair[1]):
                try:
                    os.system(pair[0] + str(id))
                    id += 1
                    time.sleep(25)
                except Exception as e:
                    with open("error", "w") as file:
                        file.write(str(e))

def simulation_six():
    '''
    Runs the simulation number six. Experiment six is run with various combinations of sensors (1,2,3 or 4).
    Network topology 6 is used.
    '''
    os.system('rm -rf topo_exp6')
    os.system('mkdir topo_exp6')
    os.system('mkdir topo_exp6/one_sensor')
    os.system('mkdir topo_exp6/two_sensors')
    os.system('mkdir topo_exp6/three_sensors')
    os.system('sudo mn -c')
    # First element of the pair: command. Second element: number of times the cmd has to be executed
    cmd1s = [   ('sudo python run.py -n 6 -s1 -sub one_sensor -id ', 7),
                ('sudo python run.py -n 6 -s2 -sub one_sensor -id ', 7),
                ('sudo python run.py -n 6 -s3 -sub one_sensor -id ', 6)
            ]
    cmd2s = [   ('sudo python run.py -n 6 -s1 -s2 -sub two_sensors -id ', 7),
                ('sudo python run.py -n 6 -s1 -s3 -sub two_sensors -id ', 7),
                ('sudo python run.py -n 6 -s2 -s3 -sub two_sensors -id ', 6)
            ]
    cmd3s = [   ('sudo python run.py -n 6 -s1 -s2 -s3 -sub three_sensors -id ', 20)
            ]
    commands = [cmd1s, cmd2s, cmd3s]
    for cmdlist in commands:
        id = 0
        for pair in cmdlist:
            for i in range(pair[1]):
                try:
                    os.system(pair[0] + str(id))
                    id += 1
                    time.sleep(25)
                except Exception as e:
                    with open("error", "w") as file:
                        file.write(str(e))

def simulation_seven():
    '''
    Runs the simulation number seven. Experiment seven is run with various combinations of sensors (1,2,3 or 4).
    Network topology 7 is used.
    '''
    os.system('rm -rf topo_exp7')
    os.system('mkdir topo_exp7')
    os.system('mkdir topo_exp7/one_sensor')
    os.system('mkdir topo_exp7/two_sensors')
    os.system('mkdir topo_exp7/three_sensors')
    os.system('sudo mn -c')
    # First element of the pair: command. Second element: number of times the cmd has to be executed
    cmd1s = [   ('sudo python run.py -n 7 -s1 -sub one_sensor -id ', 7),
                ('sudo python run.py -n 7 -s2 -sub one_sensor -id ', 7),
                ('sudo python run.py -n 7 -s3 -sub one_sensor -id ', 6)
            ]
    cmd2s = [   ('sudo python run.py -n 7 -s1 -s2 -sub two_sensors -id ', 7),
                ('sudo python run.py -n 7 -s1 -s3 -sub two_sensors -id ', 7),
                ('sudo python run.py -n 7 -s2 -s3 -sub two_sensors -id ', 6)
            ]
    cmd3s = [   ('sudo python run.py -n 7 -s1 -s2 -s3 -sub three_sensors -id ', 20)
            ]
    commands = [cmd1s, cmd2s, cmd3s]
    for cmdlist in commands:
        id = 0
        for pair in cmdlist:
            for i in range(pair[1]):
                try:
                    os.system(pair[0] + str(id))
                    id += 1
                    time.sleep(25)
                except Exception as e:
                    with open("error", "w") as file:
                        file.write(str(e))

def simulation_eight():
    '''
    Runs the simulation number eight. Experiment eight is run with various combinations of sensors (1,2,3 or 4).
    Network topology 8 is used.
    '''
    os.system('rm -rf topo_exp8')
    os.system('mkdir topo_exp8')
    os.system('mkdir topo_exp8/one_sensor')
    os.system('mkdir topo_exp8/two_sensors')
    os.system('mkdir topo_exp8/three_sensors')
    os.system('mkdir topo_exp8/four_sensors')
    os.system('sudo mn -c')
    # First element of the pair: command. Second element: number of times the cmd has to be executed
    cmd1s = [   ('sudo python run.py -n 8 -s1 -sub one_sensor -id ', 5),
                ('sudo python run.py -n 8 -s2 -sub one_sensor -id ', 5),
                ('sudo python run.py -n 8 -s3 -sub one_sensor -id ', 5),
                ('sudo python run.py -n 8 -s4 -sub one_sensor -id ', 5)
            ]
    cmd2s = [   ('sudo python run.py -n 8 -s1 -s2 -sub two_sensors -id ', 3),
                ('sudo python run.py -n 8 -s1 -s3 -sub two_sensors -id ', 3),
                ('sudo python run.py -n 8 -s1 -s4 -sub two_sensors -id ', 3),
                ('sudo python run.py -n 8 -s2 -s3 -sub two_sensors -id ', 3),
                ('sudo python run.py -n 8 -s2 -s4 -sub two_sensors -id ', 4),
                ('sudo python run.py -n 8 -s3 -s4 -sub two_sensors -id ', 4)
            ]
    cmd3s = [   ('sudo python run.py -n 8 -s1 -s2 -s3 -sub three_sensors -id ', 5),
                ('sudo python run.py -n 8 -s1 -s2 -s4 -sub three_sensors -id ', 5),
                ('sudo python run.py -n 8 -s1 -s3 -s4 -sub three_sensors -id ', 5),
                ('sudo python run.py -n 8 -s2 -s3 -s4 -sub three_sensors -id ', 5)
            ]
    cmd4s = [   ('sudo python run.py -n 8 -s1 -s2 -s3 -s4 -sub four_sensors -id ', 20)
            ]
    commands = [cmd1s, cmd2s, cmd3s, cmd4s]
    for cmdlist in commands:
        id = 0
        for pair in cmdlist:
            for i in range(pair[1]):
                try:
                    os.system(pair[0] + str(id))
                    id += 1
                    time.sleep(25)
                except Exception as e:
                    with open("error", "w") as file:
                        file.write(str(e))

def simulation_nine():
    '''
    Runs the simulation number nine. Experiment nine is run with various combinations of sensors (1,2,3 or 4).
    Network topology 9 is used.
    '''
    os.system('rm -rf topo_exp9')
    os.system('mkdir topo_exp9')
    os.system('mkdir topo_exp9/one_sensor')
    os.system('mkdir topo_exp9/two_sensors')
    os.system('mkdir topo_exp9/three_sensors')
    os.system('mkdir topo_exp9/four_sensors')
    os.system('sudo mn -c')
    # First element of the pair: command. Second element: number of times the cmd has to be executed
    cmd1s = [   ('sudo python run.py -n 9 -s1 -sub one_sensor -id ', 5),
                ('sudo python run.py -n 9 -s2 -sub one_sensor -id ', 5),
                ('sudo python run.py -n 9 -s3 -sub one_sensor -id ', 5),
                ('sudo python run.py -n 9 -s4 -sub one_sensor -id ', 5)
            ]
    cmd2s = [   ('sudo python run.py -n 9 -s1 -s2 -sub two_sensors -id ', 3),
                ('sudo python run.py -n 9 -s1 -s3 -sub two_sensors -id ', 3),
                ('sudo python run.py -n 9 -s1 -s4 -sub two_sensors -id ', 3),
                ('sudo python run.py -n 9 -s2 -s3 -sub two_sensors -id ', 3),
                ('sudo python run.py -n 9 -s2 -s4 -sub two_sensors -id ', 4),
                ('sudo python run.py -n 9 -s3 -s4 -sub two_sensors -id ', 4)
            ]
    cmd3s = [   ('sudo python run.py -n 9 -s1 -s2 -s3 -sub three_sensors -id ', 5),
                ('sudo python run.py -n 9 -s1 -s2 -s4 -sub three_sensors -id ', 5),
                ('sudo python run.py -n 9 -s1 -s3 -s4 -sub three_sensors -id ', 5),
                ('sudo python run.py -n 9 -s2 -s3 -s4 -sub three_sensors -id ', 5)
            ]
    cmd4s = [   ('sudo python run.py -n 9 -s1 -s2 -s3 -s4 -sub four_sensors -id ', 20)
            ]
    commands = [cmd1s, cmd2s, cmd3s, cmd4s]
    for cmdlist in commands:
        id = 0
        for pair in cmdlist:
            for i in range(pair[1]):
                try:
                    os.system(pair[0] + str(id))
                    id += 1
                    time.sleep(25)
                except Exception as e:
                    with open("error", "w") as file:
                        file.write(str(e))

if __name__ == '__main__':
    args = parse_cmd_args()
    snum = args.num
    exp = args.experiments
    if snum == 1:
        simulation_one(exp)
    elif snum == 2:
        simulation_two(exp)
    elif snum == 3:
        simulation_three(exp)
    elif snum == 4:
        simulation_four()
    elif snum == 5:
        simulation_five()
    elif snum == 6:
        simulation_six()
    elif snum == 7:
        simulation_seven()
    elif snum == 8:
        simulation_eight()
    elif snum == 9:
        simulation_nine()



