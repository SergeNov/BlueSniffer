import os
import time
import datetime
import subprocess
import tempfile
import json
import boto3
import blue_lib

home_dir = os.path.dirname(os.path.realpath(__file__))
buffer_dir = home_dir+'/buffer'
s3_bucket = blue_lib.s3_config['bucket']
s3_path = blue_lib.s3_config['path']

from pdpyras import EventsAPISession

config = blue_lib.devices

routing_key = blue_lib.routing_key
pd_session = EventsAPISession(routing_key)

config_index = {}
stats = {}
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
      if result != None and "mac" in result and result["mac"] in config_index and "temperature" in result:
        result["data"] = data
        device_name = config_index[result["mac"]]
        for k, v in config[device_name].items():
          result[k] = v 
        stats[device_name] = result
    except:
      pass
  if len(stats) == len(config_index):
    break
  print("  Second: " + str(i) + " -> " + str(c))
  tempf.truncate(0)


print("Closing connections..")
hcidump.kill()
hcidump.communicate()
hcitool.kill()
hcitool.communicate()
s3 = boto3.resource('s3')
s3_client = boto3.client('s3')

#populate statistics
now = datetime.datetime.now()
current_ts = now.strftime("%Y%m%d%H%M%S")
current_d = now.strftime("%Y%m%d")
for device, facts in stats.items():
  file_name = current_d+'_'+device+'.csv'
  #check if the file exists in buffer
  if not os.path.exists(buffer_dir+'/'+file_name):
    #file does not exist locally;
    #this could be a new day/device, in which case it is ok
    #file could have disappeared from local folder for some reason;
    #check if it exists in s3; if it does, download it into buffer
    response = s3_client.list_objects(
      Bucket=s3_bucket,
      Prefix=s3_path+'/'+file_name
    )
    if 'Contents' in response:
      #File exists in s3, but not in local buffer; download
      s3.meta.client.download_file(s3_bucket ,s3_path+'/'+file_name, buffer_dir+'/'+file_name)
  fh = open(buffer_dir+'/'+file_name, 'a')
  fh.write(current_ts+','+str(facts['temperature'])+','+str(facts['humidity'])+','+str(facts['battery'])+','+str(facts['data'])+"\n")
  fh.close()

#loop through files in the buffer
onlyfiles = [f for f in os.listdir(buffer_dir) if os.path.isfile(os.path.join(buffer_dir, f))]
for file in onlyfiles:
  file_arr = file.split('_')
  file_d = file_arr[0]
  s3.meta.client.upload_file(buffer_dir+'/'+file, s3_bucket, s3_path+'/'+file)
  if file_d < current_d:
    os.remove(buffer_dir+'/'+file)

tempf.close()
print("Done!")
print json.dumps(stats, indent = 2)
for device, facts in stats.items():
   for key, value in facts.items():
     if '_threshold_' in key:
       key_arr = key.split('_')
       key_metric = key_arr[0]
       key_nature = key_arr[2]
       if key_metric in facts:
         metric = facts[key_metric]
         if key_nature == 'min' and metric < value:
           message = "ALERT!!! " + device + " " +key_metric + " = " + str(metric) + " (MIN allowed value: " + str(value) + ")"
           service = "Home Beer Brewing Operation"
           dedup_key = device + "." + key
           pd_session.trigger(message, service, dedup_key=dedup_key)
           print(message)
         if key_nature == 'max' and metric > value:
           message = "ALERT!!! " + device + " " +key_metric + " = " + str(metric) + " (MAX allowed value: " + str(value) + ")"
           service = "Home Beer Brewing Operation"
           dedup_key = device + "." + key
           pd_session.trigger(message, service, dedup_key=dedup_key)
           print(message)
