import os
import time
import datetime
import json
import blue_lib

blue_packet_bad = '043E1C020104006606000642491004097370730AFFCD0CD628251002B457B1'
blue_packet_good = '043E1C020104006606000642491004097370730AFFCD09931101A9096408BB'

print "Good packet:"+blue_packet_good+" ("+str(len(blue_packet_good))+" characters)"
result_good = blue_lib.parse_raw_message(blue_packet_good)
print json.dumps(result_good, indent = 2)
print

print "Bad packet:"+blue_packet_bad+" ("+str(len(blue_packet_bad))+" characters)"
result_bad = blue_lib.parse_raw_message(blue_packet_bad)
print json.dumps(result_bad, indent = 2)
