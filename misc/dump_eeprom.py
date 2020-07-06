import argparse
import os, sys
from pydispatch import dispatcher

sys.path.insert(0, os.path.abspath('/mnt/data/workspace/eculib'))
from eculib import *

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--offset', type=int, default=0, help="read start offset")
parser.add_argument('--bytes', type=int, default=512, help="number of bytes to read")
parser.add_argument('--output', type=str, default="eeprom.bin", help="file to save read bytes to")
db_grp = parser.add_argument_group('debugging options')
db_grp.add_argument('--debug', action='store_true', help="turn on debugging output")
args = parser.parse_args()

def ECUDebugHandler(msg):
    print(msg)

if args.debug:
    dispatcher.connect(ECUDebugHandler, signal="ecu.debug", sender=dispatcher.Any)

devices = [d for d in usb.core.find(find_all=True, idVendor=pyftdi.ftdi.Ftdi.FTDI_VENDOR)]

if len(devices) < 0:
    print("No devices")
    sys.exit(-1)

ecu = HondaECU(KlineAdapter(devices[0]))

if ecu.dev.kline():
	print("Turn off ECU")
	while ecu.dev.kline():
		time.sleep(.1)
if not ecu.dev.kline():
	print("Turn on ECU")
	while not ecu.dev.kline():
		time.sleep(.1)

ecu.init()
ecu.init()
ecu.ping()

ecu.send_command([0x27],[0xe0, 0x48, 0x65, 0x6c, 0x6c, 0x6f, 0x48, 0x6f])
ecu.send_command([0x27],[0xe0, 0x77, 0x41, 0x72, 0x65, 0x59, 0x6f, 0x75])

print("Saving eeprom")

offset = args.offset
nbytes = args.bytes / 2
with open(args.output,"wb") as eeprom:
	while offset < nbytes:
		status, data = ecu._read_eeprom_word(offset)
		if status:
			eeprom.write(bytearray(data))
			eeprom.flush()
			offset += 1
		else:
			break
