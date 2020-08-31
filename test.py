from time import sleep
from bluepy import btle

mac = "49:42:06:00:06:66"
read_interval = 30

sleep(read_interval)
dev = btle.Peripheral(mac, addrType=btle.ADDR_TYPE_PUBLIC)
readings = dev.readCharacteristic(0x28)
print readings
