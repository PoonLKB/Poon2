import argparse
import os, sys
import platform
from eculib import *
from pylibftdi import FtdiError

def Main():
	parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument('--output', default=None, help="log output file")
	args = parser.parse_args()

	if args.output == None:
		args.output = sys.stdout
	else:
		args.output = open(args.output,"w")

	skip_header = False
	table = None
	start = None
	ecu = HondaECU(KlineAdapter(device_id=None))
	hl = 0
	while True:
		state = ecu.detect_ecu_state()
		if state == ECUSTATE.OK:
			if hl is 0:
				header = [
					"time","engine_speed",
					"tps_sensor_voltage","tps_sensor_scantool",
					"ect_sensor_voltage","ect_sensor_scantool",
					"iat_sensor_voltage","iat_sensor_scantool",
					"map_sensor_voltage","map_sensor_scantool",
					"battery_voltage","vehicle_speed",
					"injector_duration","ignition_advance"
				]
				u = ">H12BHB"
				h = header
				hl = len(h) - 1
				for t in [0x10,0x11,0x17]:
					info = ecu.send_command([0x72], [0x71, t])
					if info and len(info[2][2:]) > 0:
						table = t
						break
				if t == 0x11:
					u += "BH"
					h += ["iacv_pulse_count","iacv_command"]
					hl += 2
				elif t == 0x17:
					u += "BB"
				args.output.write("%s\n" % "\t".join(h))
				start = time.time()
			while True:
				info = ecu.send_command([0x72], [0x71, table])
				now = time.time() - start
				if info and len(info[2][2:]) > 0:
					data = list(struct.unpack(u, info[2][2:]))
					data[1] = data[1]/0xff*5.0
					data[2] = data[2]/1.6
					data[3] = data[3]/0xff*5.0
					data[4] = -40 + data[4]
					data[5] = data[5]/0xff*5.0
					data[6] = -40 + data[6]
					data[7] = data[7]/0xff*5.0
					data[11] = data[11]/10
					data[13] = data[13]/0xffff*265.5
					data[14] = -64 + data[14]/0xff*127.5
					if table == 0x11:
						data[16] = data[16]/0xffff*8.0
					args.output.write("%f\t%s\n" % (now,"\t".join(map(str,data[:9]+data[11:(hl+2)]))))
				else:
					break
		else:
			ecu.init()
			ecu.ping(mode=0xff)

if __name__ == '__main__':
	Main()
