# coding=utf-8
import sys
from sensor import *


#TODO va fatta interfaccia a modo, con parsing argomenti linea di comando usando modulo argparse.
# In particolare, va data la possibilità di specificare argomenti opzionali
if __name__ == '__main__':
    if len(sys.argv) != 4:
        print 'Usage: python start_sensor.py <sensor_id> <num_hosts> <config_file>'
        sys.exit(1)
    sid = sys.argv[1]
    nh = sys.argv[2]
    config = sys.argv[3]
    s = sensor(sid, nh, config)
    s.start()
