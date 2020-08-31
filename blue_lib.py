import json
import struct

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

def parse_raw_message(data):
    result = {}
    if data is None:
      return result
    if "475648353037355F" in data or "47564835303732" in data:
      result = parse_raw_message_gvh5075(data)
    if "1004097370730AFF" in data:
      result = parse_raw_message_inkIBSTH1(data)
    return result

def parse_raw_message_inkIBSTH1(data):
    if len(data)!=62:
      return {}
    mac = reverse_mac(data[14:26])
    temp = float(int(data[44:46]+data[42:44], 16))/100
    humid = float(int(data[48:50]+data[46:48], 16))/100
    battery = int(data[56:58], 16)
    result = {
        "mac": mac,
        "temperature": temp,
        "humidity": humid,
        "battery": battery
    }
    return result

def parse_raw_message_gvh5075(data):
    """Parse the raw data."""
    if data is None:
        return None

    # check for Govee H5075 name prefix "GVH5075_"
    GVH5075_index = data.find("475648353037355F", 32)
    # check for Govee H5072 name prefix "GVH5072"
    GVH5072_index = data.find("47564835303732", 32)
    if GVH5072_index == -1 and GVH5075_index == -1:
        return None
    if GVH5075_index>0 and len(data)!=92:
        return None
    # check LE General Discoverable Mode and BR/EDR Not Supported
    adv_index = data.find("020105", 64, 71)
    if adv_index == -1:
        return None
    # check if RSSI is valid
    (rssi,) = struct.unpack("<b", bytearray.fromhex(data[-2:]))
    if not 0 >= rssi >= -127:
        return None
    # check for MAC presence in message and in service data
    device_mac_reversed = data[14:26]

    # parse Govee Encoded data
    if len(data[80:86]) != 6:
        return None

    govee_encoded_data = int(data[80:86], 16)

    # parse battery percentage
    if len(data[86:88]) != 2:
        return None

    battery = int(data[86:88], 16)

    result = {
        "rssi": int(rssi),
        "mac": reverse_mac(device_mac_reversed),
        "temperature": float(govee_encoded_data / 1000) / 10,
        "humidity": float(govee_encoded_data % 1000) / 10,
        "battery": float(battery),
        "packet": govee_encoded_data,
    }

    return result
