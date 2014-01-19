# Measure temperatures on DS... devices via cobbler
# Continuously print them out on stderr.
import os
import glob
import time
import datetime


base_dir = '/sys/bus/w1/devices/'
logfile = '~/templog/%Y/%m'

def GetDevices():
  device_dir = glob.glob(base_dir + '28*')
  devs = []
  for d in device_dir:
    els = d.split('/')
    devs.append(els[-1].split('-')[1])
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
	
def init():
  # These need to be done as sudo anyway, but now
  # I put them in /etc/modules.
  os.system('modprobe w1-gpio')
  os.system('modprobe w1-therm')

def mymain():
  # init()
  devs = GetDevices()
  datetimenow = datetime.datetime.now()
  logdir = os.path.expanduser(datetimenow.strftime(logfile))
  if not os.path.exists(logdir):
    os.makedirs(logdir)
  filename = datetimenow.strftime('%s/%%d' % logdir)
  date = datetimenow.strftime('%Y-%m-%d %H:%M:%S')
  temps =[date]
  for onedev in devs:
    t = read_temp('%s/28-%s/w1_slave' % (base_dir, onedev))
    temps.append('%s:%.2f' % (onedev, t))
  print 'logdir', logdir, filename, date, len(temps)
  if len(temps) > 1:
    with open(filename, 'a') as myfile:
      myfile.write(' '.join(temps))
      myfile.write('\n')

mymain()

