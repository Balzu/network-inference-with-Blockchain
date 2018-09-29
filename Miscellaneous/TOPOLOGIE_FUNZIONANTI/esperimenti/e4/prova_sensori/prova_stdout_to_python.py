# coding=utf-8

import subprocess
import re


def clean_ip(raw_ip):
    bytes = raw_ip.split('.')
    return bytes[0] + '.' + bytes[1] + '.' + bytes[2] + '.' + bytes[3]

cmd = ['sudo', 'tcpdump', '-l', '-i', 'any']
p1 = subprocess.Popen(cmd, stdout=subprocess.PIPE)

for row in iter(p1.stdout.readline, b''):
    src_ip = row.split()[2]
    dst_ip = row.split()[4]
    s_match = re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", src_ip)
    d_match = re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", src_ip)
    if s_match:
        #TODO controlla se presente nel dizionario di IP address, altrimenti aggiungilo e fai partire iTop
        print clean_ip(src_ip)
    if d_match:
        #TODO controlla se presente nel dizionario di IP address, altrimenti aggiungilo e fai partire iTop
        print clean_ip(dst_ip)
