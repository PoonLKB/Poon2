from __future__ import division, print_function
import struct
import time
import sys
import os
import argparse
from pydispatch import dispatcher

sys.path.insert(0, os.path.abspath('/mnt/data/workspace/eculib'))
from eculib import *

def format_read(location):
	tmp = struct.unpack(">4B",struct.pack(">I",location))
	return [tmp[1], tmp[3], tmp[2]]

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
db_grp = parser.add_argument_group('debugging options')
db_grp.add_argument('--debug', action='store_true', help="turn on debugging output")
args = parser.parse_args()

def ECUDebugHandler(msg):
    print(msg)
dispatcher.connect(ECUDebugHandler, signal="ecu.debug", sender=dispatcher.Any)

devices = [d for d in usb.core.find(find_all=True, idVendor=pyftdi.ftdi.Ftdi.FTDI_VENDOR)]

ecu = HondaECU(KlineAdapter(devices[0]))

while True:
	print(ecu.dev.kline())
