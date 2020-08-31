import os
import time
import datetime
import subprocess
import tempfile
import json
import boto3
import blue_lib

home_dir = '/opt/bluetooth_scan'
buffer_dir = home_dir+'/buffer'
s3_bucket = 'sergebucket'
s3_path = 'brewing'

from pdpyras import EventsAPISession

f_c = open(home_dir+"/config", "r")
config_json = f_c.read()
config = json.loads(config_json)
f_c.close()

f_rk = open(home_dir+"/routing_key", "r")
routing_key = f_rk.read().strip()
pd_session = EventsAPISession(routing_key)
f_rk.close()

config_index = {}
stats = {}
names = {}
for item in config:
  if "mac" in config[item]:
    config_index[config[item]["mac"]] = item

hcitool_cmd = ["hcitool", "-i", "hci_device", "lescan", "--duplicates"]
hcidump_cmd = ["hcidump", "-i", "hci_device", "--raw", "hci"]

tempf = tempfile.TemporaryFile(mode="w+b")
devnull = open(os.devnull, "wb")

print("Opening connections..")

hcitool = subprocess.Popen(
            hcitool_cmd, stdout=devnull, stderr=devnull
        )
hcidump = subprocess.Popen(
            hcidump_cmd,
            stdout=tempf,
            stderr=devnull
        )

print("Collecting data..")

for i in range(20):
  c = 0
  time.sleep(1)
  tempf.flush()
  tempf.seek(0)

  data = ""
  for line in tempf:
    try:
      sline = line.decode()
      c += 1
      if sline.startswith(">"):
        data = sline.replace(">", "").replace(" ", "").strip()
      elif sline.startswith("< "):
        data = ""
      else:
        data += sline.replace(" ", "").strip()
      result = blue_lib.parse_raw_message(data)
      if result != None and "mac" in result:
        if result["mac"] in config_index:
          device_name = config_index[result["mac"]]
        else:
          device_name = "Unaccounted for"
        result["package"] = data
        stats[result["mac"]] = result
        names[result["mac"]] = device_name
    except:
      pass
  print "  Second: " + str(i) + " -> " + str(c)
  tempf.truncate(0)


print("Closing connections..")
hcidump.kill()
hcidump.communicate()
hcitool.kill()
hcitool.communicate()
tempf.close()


#populate statistics
now = datetime.datetime.now()
current_ts = now.strftime("%Y%m%d%H%M%S")
current_d = now.strftime("%Y%m%d")
for mac, name in names.items():
  print mac+" ("+name+"):"
  print json.dumps(stats[mac], indent=2)
