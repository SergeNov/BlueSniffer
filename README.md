<b>What is this thing?</b><br>
This is my bluetooth sniffer.<br>
It reads temperature, humidity, and battery charge from nearby bluetooth thermometers, stores results in CSV files in AWS S3, and triggers PagerDuty alerts if thresholds are set.<br>
<br>

<b>What thermometers does it work with?</b><br>
At this moment, it works with 2 kinds of thermometers:
 - <a href="https://www.amazon.com/dp/B07Y36FWTT">Govee 5075</a> - a simple and reliable cheap thermometer<br>
 - <a href="https://www.amazon.com/dp/B07DQNFJVL">Inkbird IBS-TH1</a> - a slightly more expensive thermometer that has an external probe; handy when you brew beer or wine and need to measure liquid temperature inside the fermenter. Also must be handy if you have an aquarium.<br>
 <br>
 
 <b>What are the prerequisites?</b><br>
  - I made it for a raspberry pi device, but it will probably run on any linux device that has bluetooth. Running it on windows might require slight modifications<br>
  - I am running this in Python 2.7 (i have my reasons), but it should work with Python 3
  - You must have <b>hcitool</b> and <b>hcidump</b> utilities installed on your device<br>
  - boto3 python library has to be installed. These scripts will be using your default credentials, so your environment must have your access/secret key in <i>~/.aws/</i> folder.<br>
  If you have never worked with AWS before, follow these instructions to install AWS command line interface:<br>
  https://docs.aws.amazon.com/cli/latest/userguide/install-cliv1.html
  it has a configuration feature that would create the right files for you (described here: https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html) <br>
  <br>
  
  <b>How do i use it?</b><br>
  First of all, you need to copy configuration files from <i>config_sample</i> directory into <i>~/.blue/</i><br>
  Edit the files:
   - <i>s3</i>: must contain s3 bucket name and path; default credentials in your environment must give you read/write access to that location<br>
   - <i>routing_key</i>: should contain a PagerDuty routing key; the key that is currently in the sample file is deprecated. If you do not want to use PagerDuty, leave this file empty<br>
   - <i>devices</i>: must contain a list of devices; each device you monitor must have at least a name and mac address, plus alert thresholds. <br>
   A script called <i>blue_explorer.py</i> will help you detect devices that are within range so you can easily populate the <i>devices</i> config file. When you run it, it it will monitor the surroundings for 20 seconds, and return the list of devices it detected:<br>
   <br>
   <i><p>
pi@raspberrypi:/opt/bluetooth_scan $ python blue_explorer.py<br>
Opening connections..<br>
Collecting data..<br>
&ensp;  Second: 0 -> 89<br>
&ensp;  Second: 1 -> 100<br>
...<br>
&ensp;  Second: 19 -> 92<br>
Closing connections..<br>
A4C138102487 (Unaccounted for):<br>
{<br>
&ensp;  "temperature": 23.4,<br>
&ensp;  "package": "043E2B0201000087241038C1A41F0D09475648353037355F32343837030388EC02010509FF88EC000394895800BF",<br>
&ensp;  "battery": 88.0,<br>
&ensp;  "packet": 234633,<br>
&ensp;  "humidity": 63.3,<br>
&ensp;  "mac": "A4C138102487",<br>
&ensp;  "rssi": -65<br>
}<br>
494206000490 (Irish_Primary_2020Aug21):<br>
{<br>
&ensp;  "battery": 100,<br>
&ensp;  "mac": "494206000490",<br>
&ensp;  "package": "043E1C020104009004000642491004097370730AFFAC08CA16010C096408C1",<br>
&ensp;  "temperature": 22.2,<br>
&ensp;  "humidity": 58.34<br>
}<br>
A4C138554580 (IPA_Bottled_2020Jul30):<br>
{<br>
&ensp;  "temperature": 23.2,<br>
&ensp;  "package": "043E2B0201000080455538C1A41F0D09475648353037355F34353830030388EC02010509FF88EC00038D1E5D00CA",<br>
&ensp;  "battery": 93.0,<br>
&ensp;  "packet": 232734,<br>
&ensp;  "humidity": 73.4,<br>
&ensp;  "mac": "A4C138554580",<br>
&ensp;  "rssi": -54<br>
}<br>
A4C138C5FD1E (Lions_Mane_Habitat_1):<br>
{<br>
&ensp;  "temperature": 21.8,<br>
&ensp;  "package": "043E2B020100001EFDC538C1A41F0D09475648353037355F46443145030388EC02010509FF88EC000356BF5700B5",<br>
&ensp;  "battery": 87.0,<br>
&ensp;  "packet": 218815,<br>
&ensp;  "humidity": 81.5,<br>
&ensp;  "mac": "A4C138C5FD1E",<br>
&ensp;  "rssi": -75<br>
}<br>
494206000666 (Wheat_Primary_2020Aug29):<br>
{<br>
&ensp;  "battery": 87,<br>
&ensp;  "mac": "494206000666",<br>
&ensp;  "package": "043E1C020104006606000642491004097370730AFFC30884140101095708C4",<br>
&ensp;  "temperature": 22.43,<br>
&ensp;  "humidity": 52.52<br>
}<br>
pi@raspberrypi:/opt/bluetooth_scan $<br>
</p></i>
<br>
 This device: <i>A4C138102487 (Unaccounted for):</i> is apparently not in the <i>devices</i> config file, but everything else is.<br>
 Have in mind that temperature values are in celsius.<br>
 <br>
 After you have finished the configuration, run <i>blue_worker.py</i> to make sure it is working; it should run for 20 seconds or less if it recieves data from all devices in your config file, prints the data, and stores the files in an S3 bucket.<br>
 Once you are sure it works, schedule it in cron to run as often as you want (i have it run every minute)<br>
 <i>* * * * * python /opt/bluetooth_scan/blue_worker.py >/dev/null 2>/dev/null</i><br>
 <br>
 <b>What do i do with data once it is in the bucket?</b><br>
 Pretty much anything; i have included a script called <i>brew_stats.wsgi</i> that builds diagrams based on recorded data. Feel free to use it, but it will require to set up apache with wsgi plugin.<br>
 Example of what the page looks like is here:<br>
 https://hydropony.net/brew_stats?days=3<br>
 https://hydropony.net/brew_stats?stime=20200807&stime=20200828&device=Mead_Primary_2020Aug07<br>
 <br>
   <b>Acknowledgements</b><br>
 I relied heavily on code by user <b>Thrilleratplay</b> located here:<br>
 https://github.com/Home-Is-Where-You-Hang-Your-Hack/sensor.goveetemp_bt_hci<br>
 It helped me understand how to make a bluetooth sniffer and how to parse packets (which i had no previous experience with). I needed something completely different from a Home Assistant component, but i used bluetooth related code from that repository<br>
 
