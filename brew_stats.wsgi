import sys
import os
import datetime
import pytz
import json
import re
import boto3
import csv
import getpass
import random
import string
from cgi import parse_qs, escape
from urllib import quote
import xmltodict
import json
import blue_lib
from http.cookies import SimpleCookie
import plotly
import plotly.offline as offline
import plotly.graph_objs as go

import datetime

s3_bucket = blue_lib.s3_config['bucket']
s3_path = blue_lib.s3_config['path']
s3_client = boto3.client('s3')

def get_random_string(length):
  letters = string.ascii_lowercase
  result_str = ''.join(random.choice(letters) for i in range(length))
  return result_str

def str_to_date(str):
  if len(str)>=14:
    dat=datetime.datetime.strptime(str[:14],"%Y%m%d%H%M%S").replace(tzinfo=pytz.timezone('US/Pacific'))
    return dat
  if len(str)>=12:
    dat=datetime.datetime.strptime(str[:12],"%Y%m%d%H%M").replace(tzinfo=pytz.timezone('US/Pacific'))
    return dat
  if len(str)>=10:
    dat=datetime.datetime.strptime(str[:10],"%Y%m%d%H").replace(tzinfo=pytz.timezone('US/Pacific'))
    return dat
  if len(str)>=8:
    dat=datetime.datetime.strptime(str[:8],"%Y%m%d").replace(tzinfo=pytz.timezone('US/Pacific'))
    return dat
  if len(str)>=6:
    dat=datetime.datetime.strptime(str[:6],"%Y%m").replace(tzinfo=pytz.timezone('US/Pacific'))
    return dat
  dat=datetime.datetime.strptime(str[:4],"%Y").replace(tzinfo=pytz.timezone('US/Pacific'))
  return dat





def wf(environ, start_response):
  start_response('200 OK', [('Content-Type', 'text/html')])

  qs=environ.get('QUERY_STRING', '')
  parameters = parse_qs(qs)
  if 'days' in parameters:
    days=int(parameters['days'][0])
  else:
    days=7
  if 'stime' in parameters:
    stime = str_to_date(parameters['stime'][0])
  else:
    stime = datetime.datetime.now(pytz.timezone('US/Pacific')) - datetime.timedelta(days=days)
  if 'etime' in parameters:
    etime = str_to_date(parameters['etime'][0])
  else:
    etime = datetime.datetime.now(pytz.timezone('US/Pacific'))
  if 'interval' in parameters:
    interval = int(parameters['interval'][0])
  else:
    interval = 5
    diff = int((etime - stime).total_seconds())
    if diff > 86400: #more than one day - 15 min intervals
      interval = 15
    if diff > 345600: #more than 4 days - 30 minutes
      interval = 30
    if diff > 604800: #more than 7 days - 60 minutes
      interval = 60
  if 'device' in parameters:
    device=parameters['device'][0]
  else:
    device=''

  html ='<html lang="en-US"><head>\n<title>Brewing Stats Page</title>\n'
  html+='<META HTTP-EQUIV="Pragma" CONTENT="no-cache">\n'
  html+='<META charset="UTF-8">\n'
  html+='<META http-equiv="refresh" content="'+str(interval*60)+'">\n'
  html+='<link rel="shortcut icon" type="image/png" href="beer_icon.png" />\n'
  html+='<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>\n'
  html+="<style>input[type='text'] { font-size: 16px; }</style>\n"
  html+="<style>input[type='number'] { font-size: 16px; }</style>\n"
  html+="<style>input[type='submit'] { font-size: 16px; }</style>\n"
  html+="<style>select { font-size: 16px; }</style>\n"
  html+="<style>textarea { font-size: 24px; }</style>\n"
  html+='</head>\n'
  html+='<body>'

  first_day = datetime.date(stime.year, stime.month, stime.day)
  last_day = datetime.date(etime.year, etime.month, etime.day)
  stime_str = stime.strftime("%Y%m%d%H%M%S")
  etime_str = etime.strftime("%Y%m%d%H%M%S")

  day = first_day
  temperature_trace = {}
  humidity_trace = {}
  battery_trace = {}
  time_trace = []
  great_hash = {}
  while True:
    s3_day_path = s3_path+"/"+day.strftime("%Y%m%d")+"_"+device
    remove_path = s3_path+"/"+day.strftime("%Y%m%d")+"_"
    result = s3_client.list_objects(Bucket=s3_bucket, Prefix=s3_day_path)
    if 'Contents' in result:
      for k in  result['Contents']:
        key = k['Key']
        device_name = key.replace(remove_path,'').replace('.csv','')
        if device_name not in temperature_trace:
          temperature_trace[device_name] = []
        if device_name not in humidity_trace:
          humidity_trace[device_name] = []
        if device_name not in battery_trace:
          battery_trace[device_name] = []
        temp_file_name = '/opt/wsgi_scripts/bin/buffer/'+get_random_string(15)+'.csv'
        s3_client.download_file(s3_bucket, key, temp_file_name)
        fh_r = open(temp_file_name, 'r')
        csv_reader = csv.reader(fh_r, delimiter=',', quotechar='"')
        for row in csv_reader:
          dt_str = row[0]
          temperature = row[1]
          humidity = row[2]
          battery = row[3]
          if dt_str>=stime_str and dt_str<=etime_str:
            dt = datetime.datetime.strptime(dt_str, "%Y%m%d%H%M%S")
            dt = dt.replace(microsecond=0, second=0, minute=(dt.minute//interval)*interval)
            dt_str = dt.strftime("%Y%m%d%H%M%S")
            if dt not in great_hash:
              great_hash[dt] = {}
            great_hash[dt][device_name] = [temperature, humidity, battery]
        fh_r.close()
        os.remove(temp_file_name)
    day += datetime.timedelta(days=1)
    if day > last_day:
      break

  #Rearrange the data
  for dt in sorted(great_hash):
    time_trace.append(dt)

    for device_name in temperature_trace:
      if device_name in great_hash[dt]:
        temperature_trace[device_name].append(great_hash[dt][device_name][0])
      else:
        temperature_trace[device_name].append(None)

    for device_name in humidity_trace:
      if device_name in great_hash[dt]:
        humidity_trace[device_name].append(great_hash[dt][device_name][1])
      else:
        humidity_trace[device_name].append(None)

    for device_name in battery_trace:
      if device_name in great_hash[dt]:
        battery_trace[device_name].append(great_hash[dt][device_name][2])
      else:
        battery_trace[device_name].append(None)

  html+='<h2>Brewing Experiment Statistics</h2>'

  html+='<h3>Temperature Graph</h3>'
  temp_scatter_set = []
  device_list = []
  for device_name in sorted(temperature_trace):
    device_list.append(device_name)
    scatter = go.Scatter(
      name=device_name,
      x=time_trace,
      y=temperature_trace[device_name],
      text='Temperature: '+device_name,
      mode = 'lines+markers'
    )
    temp_scatter_set.append(scatter)
  layout=go.Layout(
    showlegend=True,
    xaxis=dict(
      title='Time',
    ),
    yaxis=dict(
      title='Temperature(C)',
    ),
    height=500
  )
  html+='<div id="1" class="plotly-graph-div"></div>\n'
  html+='<script type="text/javascript">window.PLOTLYENV=window.PLOTLYENV || {};window.PLOTLYENV.BASE_URL="https://plot.ly";Plotly.newPlot("1", '+json.dumps(temp_scatter_set, cls=plotly.utils.PlotlyJSONEncoder)+', '+json.dumps(layout, cls=plotly.utils.PlotlyJSONEncoder)+', {"linkText": "Export to plot.ly", "showLink": false})</script>\n'

  html+='<h3>Humidity Graph</h3>'
  humid_scatter_set = []
  device_list = []
  for device_name in sorted(humidity_trace):
    device_list.append(device_name)
    scatter = go.Scatter(
      name=device_name,
      x=time_trace,
      y=humidity_trace[device_name],
      text='Humidity: '+device_name,
      mode = 'lines+markers'
    )
    humid_scatter_set.append(scatter)
  layout=go.Layout(
    showlegend=True,
    xaxis=dict(
      title='Time',
    ),
    yaxis=dict(
      title='Humidity(%)',
    ),
    height=500
  )
  html+='<div id="2" class="plotly-graph-div"></div>\n'
  html+='<script type="text/javascript">window.PLOTLYENV=window.PLOTLYENV || {};window.PLOTLYENV.BASE_URL="https://plot.ly";Plotly.newPlot("2", '+json.dumps(humid_scatter_set, cls=plotly.utils.PlotlyJSONEncoder)+', '+json.dumps(layout, cls=plotly.utils.PlotlyJSONEncoder)+', {"linkText": "Export to plot.ly", "showLink": false})</script>\n'

  html+='<h3>Battery Graph</h3>'
  battery_scatter_set = []
  device_list = []
  for device_name in sorted(battery_trace):
    device_list.append(device_name)
    scatter = go.Scatter(
      name=device_name,
      x=time_trace,
      y=battery_trace[device_name],
      text='Battery: '+device_name,
      mode = 'lines+markers'
    )
    battery_scatter_set.append(scatter)
  layout=go.Layout(
    showlegend=True,
    xaxis=dict(
      title='Time',
    ),
    yaxis=dict(
      title='Battery(%)',
    ),
    height=500
  )
  html+='<div id="3" class="plotly-graph-div"></div>\n'
  html+='<script type="text/javascript">window.PLOTLYENV=window.PLOTLYENV || {};window.PLOTLYENV.BASE_URL="https://plot.ly";Plotly.newPlot("3", '+json.dumps(battery_scatter_set, cls=plotly.utils.PlotlyJSONEncoder)+', '+json.dumps(layout, cls=plotly.utils.PlotlyJSONEncoder)+', {"linkText": "Export to plot.ly", "showLink": false})</script>\n'


  return [html]

application=wf
