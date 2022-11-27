import blue_lib

config = blue_lib.devices

config_index = {}
stats = {}
names = {}

for item in config:
  if "mac" in config[item]:
    config_index[config[item]["mac"]] = item

detected = {}

print("Opening sniffer")
blue_lib.open_sniffer()

print("Collecting data..")

for i in range(10):
  packets = blue_lib.get_batch(6)

  recognized_packets = []
  for packet in packets:
    result = blue_lib.parse_raw_message(packet)
    if result is not None and "model" in result:
      recognized_packets.append(result)
      mac = result['mac']
      model = result['model']
      name = "Not found in config"
      if mac in config_index:
        name = config_index[mac]
      detected[mac] = {"model": model, "name": name}

  print(f"Scan {i}: captured {len(packets)} packets, recognized {len(recognized_packets)} packets")

print("Closing sniffer")
blue_lib.close_sniffer()

print("Devices detected:")
for mac in detected:
  detail = detected[mac]
  print(f"  {mac}: {detail['model']} / {detail['name']}")
