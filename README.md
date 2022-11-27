<h2>What is this thing?</h2>
This is my bluetooth sniffer.<br>
The file that matters is <b>blue_lib.py</b>; Also 2 scripts are provided, but they are merely examples, unless they do exactly what you want them to do<br>
<b>blue_explorer.py</b>: sniffs bluetooth packets for a minute, detects if any of them are from thermometers it is familiar with, and in the end prints the list of detected thermometers<br>
<b>blue_worker.py</b>: sniffs bluetooth packets for a minute, finds if any of them come from thermometers listed in ~/.blue/devices config file, afterwards writes the readings into a file in S3, and triggers alerts in PagerDuty in case temperature/humidity/battery charge are outside allowed ranges<br>

<b>What thermometers does it work with?</b><br>
At this moment, it works with 2 kinds of thermometers:
 - <a href="https://www.amazon.com/dp/B07Y36FWTT">Govee 5075</a> - a simple and reliable cheap thermometer<br>
 - <a href="https://www.amazon.com/dp/B07DQNFJVL">Inkbird IBS-TH1</a> - a slightly more expensive thermometer that has an external probe; handy when you brew beer or wine and need to measure liquid temperature inside the fermenter. Also must be handy if you have an aquarium.<br>
 <br>
 
 <b>What are the prerequisites?</b><br>
  - I made it for a raspberry pi device, but it will probably run on any linux device that has bluetooth. Running it on windows might require slight modifications<br>
  - Tested with Python 2.7 and 3.9
  - You must have <b>hcitool</b> and <b>hcidump</b> utilities installed on your device<br>
This is what you need to do in order to install the prerequisites on a fresh Raspberry PI device:<br>
<i>
<b>Python stuff</b><br>
sudo apt update && sudo apt upgrade -y<br>
sudo apt install python3-pip<br>
<br>
<b>These libraries are required for blue_worker.py, but if you aren't planning to run it, you don't have to install them</b><br>
pip install boto3<br>
pip install pdpyras<br>
<br>
<b>Check out the code</b><br>
sudo apt install git -y<br>
git clone https://github.com/SergeNov/BlueSniffer.git<br>
<br>
<b>Create config files</b><br>
cd BlueSniffer/<br>
mkdir ~/.blue<br>
cp config_sample/* ~/.blue/<br>
<br>
<b>Install bluetooth cli utility</b><br>
<b>(Unfortunately, there's no other way i could find for retrieving raw bluetooth packets at the moment i wrote this tool)</b><br>
sudo apt-get install bluez-hcidump<br>
<br>
<b>Make sure it works under non-root users</b><br>
sudo apt-get install libcap2-bin<br>
sudo setcap 'cap_net_raw,cap_net_admin+eip' \`which hcitool\`<br>
sudo setcap 'cap_net_raw,cap_net_admin+eip' \`which hcidump\`<br>
</i>

<h3>Functions that might be useful to you:</h3>
<i>
<b>blue_lib.open_sniffer()</b>: Start the HCI subprocesses that allow listening to Bluetooth<br>
<b>blue_lib.close_sniffer()</b>: Kill the HCI subprocesses<br>
<b>blue_lib.get_batch(seconds)</b>: Sniff packets for X seconds; returns an array of strings, each string a raw packet<br>
<b>blue_lib.parse_raw_message(data)</b>: Input is a raw packet in a string; returns a dictionary containing sender's mac address, and, if the packet has been recognized, thermometer model name, temperature, and other info extracted from the packet<br>
</i>
   <h3>Acknowledgements</h3>
 I relied heavily on code by user <b>Thrilleratplay</b> located here:<br>
 https://github.com/Home-Is-Where-You-Hang-Your-Hack/sensor.goveetemp_bt_hci<br>
 It helped me understand how to make a bluetooth sniffer and how to parse packets (which i had no previous experience with). I needed something completely different from a Home Assistant component, but i used bluetooth related code from that repository<br>
