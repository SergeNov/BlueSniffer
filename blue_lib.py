import os
import json
import struct
import tempfile
import time
import subprocess

home = os.path.expanduser("~")

fh_r = open(home + "/.blue/devices", "r")
devices = json.loads(fh_r.read())
fh_r.close()

fh_r = open(home + "/.blue/s3", "r")
s3_config = json.loads(fh_r.read())
fh_r.close()

fh_r = open(home + "/.blue/routing_key", "r")
routing_key = fh_r.read().strip()
fh_r.close()

hcitool_cmd = ["hcitool", "-i", "hci_device", "lescan", "--duplicates"]
hcidump_cmd = ["hcidump", "-i", "hci_device", "--raw", "hci"]

tempf = None
devnull = None
hcitool = None
hcidump = None


# This function opens the HCI subprocesses, making it possible to
# intercept Bluetooth packets
def open_sniffer():
  global tempf
  global devnull
  global hcitool
  global hcidump

  tempf = tempfile.TemporaryFile(mode="w+b")
  devnull = open(os.devnull, "wb")
  hcitool = subprocess.Popen(
            hcitool_cmd, stdout=devnull, stderr=devnull
        )
  hcidump = subprocess.Popen(
            hcidump_cmd,
            stdout=tempf,
            stderr=devnull
        )


# This function kills HCI processes once they are no longer required
def close_sniffer():
  global hcidump
  global hcitool
  global tempf

  hcidump.kill()
  hcidump.communicate()
  hcitool.kill()
  hcitool.communicate()
  tempf.close()

# This function sniffs the packets for an interval of time, and returns captured
# packets as an array of strings
# Input parameters:
#  seconds - how many seconds to listen for packets
def get_batch(seconds):
  result = []

  time.sleep(seconds)
  tempf.flush()
  tempf.seek(0)

  for line in tempf:
    data = feed_line(line)
    if data is not None:
      result.append(data)

  tempf.truncate(0)
  return result


current_line = ""


def feed_line(line):
  global current_line
  sline = line.decode().replace(" ", "").replace(chr(0), "").strip()
  if sline.startswith(">") or sline.startswith("<"):
    old_line = current_line
    current_line = sline.replace(">", "").replace("<", "").strip()
    return old_line
  current_line += sline.replace(" ", "")
  return None


def reverse_mac(rmac):
  """Change LE order to BE."""
  if len(rmac) != 12:
      return None

  reversed_mac = rmac[10:12]
  reversed_mac += rmac[8:10]
  reversed_mac += rmac[6:8]
  reversed_mac += rmac[4:6]
  reversed_mac += rmac[2:4]
  reversed_mac += rmac[0:2]
  return reversed_mac


# This function tries to determine if the packet comes from one of the
# know thermometers, and parses it
# Input parameter:
#  data - raw packet as a string
# Output dictionary has the following keys:
#  mac - mac address of the device
#  data - raw packet from the input
# If the device has been recognized, should have at least these keys:
#  model - model of the thermometer
#  temperature - temperature in Celcius
# Might have other parameters if the thermometer broadcasts them, such as
# humidity or battery charge
def parse_raw_message(data):
  result = {}
  if len(data) < 26:
    return result
  mac = reverse_mac(data[14:26])
  if "475648353037355F" in data or "47564835303732" in data:
    result = parse_raw_message_gvh5075(data)
  if "1004097370730AFF" in data:
    result = parse_raw_message_inkIBSTH1(data)
  result['mac'] = mac
  result['data'] = data
  return result


def parse_raw_message_inkIBSTH1(data):
  if len(data) != 62 or data[58:60] != '08':
    return {}
  temp = float(int(data[44:46]+data[42:44], 16))/100
  humid = float(int(data[48:50]+data[46:48], 16))/100
  battery = int(data[56:58], 16)
  result = {
      "temperature": temp,
      "humidity": humid,
      "battery": battery,
      "model": "Inkbird IBS-TH1"
  }
  return result


def parse_raw_message_gvh5075(data):
  # this function has been borrowed from here:
  # https://github.com/Home-Is-Where-You-Hang-Your-Hack/sensor.goveetemp_bt_hci
  """Parse the raw data."""
  if data is None:
      return None

  # check for Govee H5075 name prefix "GVH5075_"
  GVH5075_index = data.find("475648353037355F", 32)
  # check for Govee H5072 name prefix "GVH5072"
  GVH5072_index = data.find("47564835303732", 32)
  if GVH5072_index == -1 and GVH5075_index == -1:
    return None
  if GVH5075_index > 0 and len(data) != 92:
    return None
  # check LE General Discoverable Mode and BR/EDR Not Supported
  adv_index = data.find("020105", 64, 71)
  if adv_index == -1:
    return None
  # check if RSSI is valid
  (rssi,) = struct.unpack("<b", bytearray.fromhex(data[-2:]))
  if not 0 >= rssi >= -127:
    return None

  # parse Govee Encoded data
  if len(data[80:86]) != 6:
    return None

  govee_encoded_data = int(data[80:86], 16)

  # parse battery percentage
  if len(data[86:88]) != 2:
    return None

  battery = int(data[86:88], 16)

  model = ""
  if GVH5072_index > 0:
    model = "Govee H5072"
  elif GVH5075_index > 0:
    model = "Govee H5075"

  result = {
    "rssi": int(rssi),
    "temperature": float(govee_encoded_data / 1000) / 10,
    "humidity": float(govee_encoded_data % 1000) / 10,
    "battery": float(battery),
    "model": model
  }

  return result
