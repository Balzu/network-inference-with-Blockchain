# -*- coding: utf-8 -*-

from __future__ import division
import random, os, pdb, glob, time, subprocess
from run import *

def retrieve_times():
    '''
    Parses all the blockchain server nodes log files and returns a tuple containing the dictionaries of open,
    establish and accept phase completion times.
    :return: Tuple of three dictionaries
    '''
    logs = glob.glob('*.log')
    logs.sort() # Let's put log files in order. The first 6 comprise the first group
    # Dictionaries to hold simulation times. Key=node_log; value=list of execution times
    open_times = {}
    est_times = {}
    acc_times = {}
    for i in range(0,len(logs)):
        open_times[logs[i]] = []
        est_times[logs[i]] = []
        acc_times[logs[i]] = []
        with open(logs[i], 'r') as logfile:
            open_tmp = 0
            est_tmp = 0
            acc_tmp = 0
            for l in logfile:
                if l.startswith('Open'):
                    open_tmp += float(l.split()[3])
                elif l.startswith('Establish'):
                    est_tmp += float(l.split()[3])
                elif l.startswith('Accept'):
                    acc_tmp += float(l.split()[3])
                elif l.startswith('Consensus'):
                    if l.split()[2] == 'True':
                        open_times[logs[i]].append(open_tmp)
                        est_times[logs[i]].append(est_tmp)
                        acc_times[logs[i]].append(acc_tmp)
                        open_tmp = 0
                        est_tmp = 0
                        acc_tmp = 0
    return (open_times, est_times, acc_times)


def plot_avg_group_times(open, establish, accepted, part, limit, filename):
    '''
    Plots the histogram of the completion times of the various phases plus the total completion time.
    It is assumed that the nodes belonging to the first group are in the first part of the list (that's why we sort),
    while the second group is in the second part. The second group also contains one random node from the first group.
    :param open: Dictionary of open phase completion times
    :param establish: Dictionary of establish phase completion times
    :param accepted: Dictionary of accepted phase completion times
    :param part: Specifies whether the first or the second part of the dictionaries has to be considered. Must be
                either 'first' or 'second'
    :param limit: Upper limit if first part; Lower limit if second part. In ay case, it designs the border item.
    :param filename: Name of the plotted graph on disk
    '''
    def compute_average(dict):
        sum = 0
        num = 0
        for i in range(lower, upper):
            for t in dict[keys[i]]:
                sum += t
                num += 1
        if part == 'second': #In the second group insert one random node of the first group to always have an intersection
            for t in dict[keys[random.randint(lower, upper-1)]]:
                sum += t
                num += 1
            #sum += dict[keys[random.randint(lower, upper-1)]]
            #num += 1
        return sum / num

    keys = open.keys() # keys are the same for all the dictionaries
    keys.sort()
    assert part == 'first' or part == 'second'
    if part == 'first':
        lower = 0
        upper = limit
    else:
        lower = limit
        upper = len(keys)
    open_avg = compute_average(open)
    est_avg = compute_average(establish)
    acc_avg = compute_average(accepted)
    total_avg = open_avg + est_avg + acc_avg
    times = [open_avg, est_avg, acc_avg, total_avg]
    plot_histogram(times, filename)


def simulation_one(num_exp, num_htx=0):
    '''
    Runs a simulation for the first case.
    :param num_exp: Number of experiments that comprise the simulation.
    :param num_htx: Number of honest transactions sent to the blockchain nodes. If 0, use default transactions (104)
    '''
    servers = configure_client('configuration/client_config.json').validators
    for sip in servers:
        os.system("ssh mininet@" + sip.split(':')[
            0] + " 'cd network-inference-with-BlockchainNEW/Tests/MaliciousNodesDistributedLAN/;"
                 " rm *.log > /dev/null &'")
    for i in range(0, num_exp):
        print '\n Number of experiment: ' + str(i)
        # Run one experiment of the simulation
        #os.system("python run.py --type 1 --honest_transactions " + str(num_htx)) + " &"
        subprocess.Popen(["python", "run.py", "--type", "1", "--honest_transactions", str(num_htx)])
        print '\n Going to sleep..\n'
        time.sleep(250)
        print '\n Going to kill stale processes..\n'
        # Kill the processes that still use the sockets (if any). Returns usage message if nothing to kill
        for sip in servers:
            os.system("ssh mininet@" + sip.split(':')[
                0] + " 'kill $(sudo netstat -pltn | grep 10000 | awk '{print $7}' | awk -F'/' '{print $1}') >test.txt &'")
    print '\nEXPERIMENT ENDED. COPY THE FILES FROM SERVERS TO CLIENT (this machine) AND THEN COMPUTE TIMES AND DRAW GRAPH..\n'
    #open, est, acc = retrieve_times()
    #plot_avg_group_times(open, est, acc, 'first', 6, 'c1_g1.png')
    #plot_avg_group_times(open, est, acc, 'second', 6, 'c1_g2.png')


def simulation_two(num_exp, num_mal, num_htx=0):
    '''
    Runs a simulation for the second case.
    :param num_exp: Number of experiments that comprise the simulation
    :param num_mal: Number of malicious nodes
    :param num_htx: Number of honest transactions sent to the blockchain nodes. If 0, use default transactions (104)
    '''
    os.system("rm *.log")
    for i in range(0, num_exp):
        # Run one experiment of the simulation
        os.system("python run.py --type 2 --number " + str(num_mal) + " --honest_transactions " + str(num_htx))
        # Kill the processes that still use the sockets (if any). Returns usage message if nothing to kill
        os.system("kill $(sudo netstat -pltn | grep 10000 | awk '{print $7}' | awk -F'/' '{print $1}')")
    open, est, acc = retrieve_times()
    plot_avg_group_times(open, est, acc, 'first', 6, 'c2_g1_n' + str(num_mal) + '.png')
    plot_avg_group_times(open, est, acc, 'second', 6, 'c2_g2_n' + str(num_mal) + '.png')

def simulation_three(num_exp, num_mal, num_tx, num_htx=0):
    '''
    Runs a simulation for the third case.
    :param num_exp: Number of experiments that comprise the simulation
    :param num_mal: Number of malicious nodes
    :param num_tx: Number of fraudolent transactions inserted by malicious nodes
    :param num_htx: Number of honest transactions sent to the blockchain nodes. If 0, use default transactions (104)
    '''
    os.system("rm *.log")
    for i in range(0, num_exp):
        # Run one experiment of the simulation
        os.system("python run.py --type 3 --number " + str(num_mal) + ' --fraudolent_transactions ' + str(num_tx)
                  + " --honest_transactions " + str(num_htx))
        # Kill the processes that still use the sockets (if any). Returns usage message if nothing to kill
        os.system("kill $(sudo netstat -pltn | grep 10000 | awk '{print $7}' | awk -F'/' '{print $1}')")
        # time.sleep(5)
    open, est, acc = retrieve_times()
    plot_avg_group_times(open, est, acc, 'first', 6, 'c3_g1_n' + str(num_mal) + '_tx' + str(num_tx) + '.png')
    plot_avg_group_times(open, est, acc, 'second', 6, 'c3_g2_n' + str(num_mal) + '_tx' + str(num_tx)  + '.png')

def simulation_four(num_exp, num_mal, num_tx, num_htx=0):
    '''
    Runs a simulation for the third case.
    :param num_exp: Number of experiments that comprise the simulation
    :param num_mal: Number of malicious nodes
    :param num_tx: Number of honest transactions dropped by malicious nodes
    :param num_htx: Number of honest transactions sent to the blockchain nodes. If 0, use default transactions (104)
    '''
    os.system("rm *.log")
    for i in range(0, num_exp):
        # Run one experiment of the simulation
        os.system("python run.py --type 4 --number " + str(num_mal) + ' --fraudolent_transactions ' + str(num_tx)
                  + " --honest_transactions " + str(num_htx))
        # Kill the processes that still use the sockets (if any). Returns usage message if nothing to kill
        os.system("kill $(sudo netstat -pltn | grep 10000 | awk '{print $7}' | awk -F'/' '{print $1}')")
        # time.sleep(5)
    open, est, acc = retrieve_times()
    plot_avg_group_times(open, est, acc, 'first', 6, 'c4_g1_n' + str(num_mal) + '_tx' + str(num_tx) + '.png')
    plot_avg_group_times(open, est, acc, 'second', 6, 'c4_g2_n' + str(num_mal) + '_tx' + str(num_tx)  + '.png')


simulation_one(20, num_htx=500)
#simulation_two(20,1, num_htx=500)
#simulation_three(20, 1, 1000, num_htx=500)
#simulation_four(20, 1, 900, num_htx=500)

