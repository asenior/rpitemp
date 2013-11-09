# Measure temperatures on DS... devices via cobbler
# Continuously print them out on stderr.
import os
import glob
import time

os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

base_dir = '/sys/bus/w1/devices/'


def GetDevices():
  device_dir = glob.glob(base_dir + '28*')
  devs = []
  for d in device_dir:
    els = d.split('/')
    devs.append(els[-1])
  return devs  

def read_temp_raw(device_file):
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines

def read_temp(device_file):
    lines = read_temp_raw(device_file)
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.1)
        lines = read_temp_raw(device_file)
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        temp_f = temp_c * 9.0 / 5.0 + 32.0
        return temp_c
	
def mymain():
  devs = GetDevices()
  while True:
    for onedev in devs:
      t = read_temp('%s/%s/w1_slave' % (base_dir, onedev))
      print onedev, t
  time.sleep(1)

mymain()

