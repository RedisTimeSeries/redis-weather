import urllib.request
import json
import redis 
import time
import sys
import os.path

if len(sys.argv) != 2:
    print("Usage: openweather_redis_exporter.py <config_file.json>")
    sys.exit()

if not os.path.isfile(sys.argv[1]):
    print("Config file " + sys.argv[1] + " not found!")
    sys.exit()

with open(sys.argv[1]) as f:
  conf = json.load(f)

r = redis.Redis(host=conf['redis_host'],port=conf['redis_port'])

r.delete("places")
units=conf['units']
if units == 'imperial':
    visibility_div=1609
else:   
    visibility_div=1000

def ts_add(ts,metric,location,mode,value):
    r.execute_command('ts.add weather:' + location + ':' + mode + ':' + metric +  ' ' + ts + ' ' + str(value) + ' LABELS location ' + location + ' metric ' + metric + ' mode ' + mode)    

def ts_del(location,mode):
    r.delete('weather:' + location + ':' + mode + ':sunrise')
    r.delete('weather:' + location + ':' + mode + ':sunset')
    r.delete('weather:' + location + ':' + mode + ':temp')
    r.delete('weather:' + location + ':' + mode + ':feels_like')
    r.delete('weather:' + location + ':' + mode + ':clouds')
    r.delete('weather:' + location + ':' + mode + ':visibility')
    r.delete('weather:' + location + ':' + mode + ':wind_deg')
    r.delete('weather:' + location + ':' + mode + ':wind_gust')
    r.delete('weather:' + location + ':' + mode + ':wind_speed')
    r.delete('weather:' + location + ':' + mode + ':rain')
    r.delete('weather:' + location + ':' + mode + ':snow')


while True:

    for place in conf['places']:
        location = place['name']
        url = "https://api.openweathermap.org/data/2.5/onecall?lat=" + str(place['lat']) + "&lon=" + str(place['lon']) + "&units=" + units + "&exclude=minutely&appid=" + conf['open_weather_api']
        print(place['name'], url)
        response = urllib.request.urlopen(url)
        data = json.loads(response.read())
        data['current']=[data['current']]
        timezone_offset = int(data['timezone_offset'])
        r.sadd("places",location)

        for mode in ['current','hourly']:
            if mode != 'current':
                ts_del(location,mode)
            for dt in data[mode]: 
                ts=str((dt['dt']+timezone_offset)*1000)

                if mode == 'current':
                    ts_add(ts,'dt',location,mode,ts)
                
                if 'sunrise' in dt:
                    ts_add(ts,'sunrise',location,mode,(dt['sunrise']+timezone_offset)*1000)
                if 'sunset' in dt:
                    ts_add(ts,'sunset',location,mode,(dt['sunset']+timezone_offset)*1000)
                if 'clouds' in dt:
                    ts_add(ts,'clouds',location,mode,dt['clouds'])
                if 'visibility' in dt:
                    ts_add(ts,'visibility',location,mode,dt['visibility']/visibility_div)
                if 'wind_speed' in dt:
                    ts_add(ts,'wind_speed',location,mode,dt['wind_speed'])
                if 'wind_deg' in dt:
                    ts_add(ts,'wind_deg',location,mode,dt['wind_deg'])
                if 'wind_gust' in dt:
                    ts_add(ts,'wind_gust',location,mode,dt['wind_gust'])
                if 'temp' in dt:
                    ts_add(ts,'temp',location,mode,dt['temp'])
                if 'feels_like' in dt:
                    ts_add(ts,'feels_like',location,mode,dt['feels_like'])
                if 'rain' in dt:
                    ts_add(ts,'rain',location,mode,dt['rain']['1h'])
                else:
                    ts_add(ts,'rain',location,mode,0)
                if 'snow' in dt:
                    ts_add(ts,'snow',location,mode,dt['snow']['1h'])
                else:
                    ts_add(ts,'snow',location,mode,0)
        
        for dt in data['daily']: 
            ts=str((dt['dt']+timezone_offset)*1000)

            if int(ts)-int(round(time.time() * 1000)) < 172800000:
                continue 

            if 'sunrise' in dt:
                ts_add(ts,'sunrise',location,'hourly',(dt['sunrise']+timezone_offset)*1000)
            if 'sunset' in dt:
                ts_add(ts,'sunset',location,'hourly',(dt['sunset']+timezone_offset)*1000)
            if 'clouds' in dt:
                ts_add(ts,'clouds',location,'hourly',dt['clouds'])
            if 'visibility' in dt:
                ts_add(ts,'visibility',location,'hourly',dt['visibility']/visibility_div)
            if 'wind_speed' in dt:
                ts_add(ts,'wind_speed',location,'hourly',dt['wind_speed'])
            if 'wind_deg' in dt:
                ts_add(ts,'wind_deg',location,'hourly',dt['wind_deg'])
            if 'wind_gust' in dt:
                ts_add(ts,'wind_gust',location,'hourly',dt['wind_gust'])
            if 'temp' in dt:
                ts_add(ts,'temp',location,'hourly',(dt['temp']['max']+dt['temp']['min'])/2)
            if 'feels_like' in dt:
                ts_add(ts,'feels_like',location,'hourly',(dt['feels_like']['morn']+dt['feels_like']['night']+dt['feels_like']['eve']+dt['feels_like']['day'])/4)
            if 'rain' in dt:
                ts_add(ts,'rain',location,'hourly',dt['rain'])
            else:
                ts_add(ts,'rain',location,'hourly',0)
            if 'snow' in dt:
                ts_add(ts,'snow',location,'hourly',dt['snow'])
            else:
                ts_add(ts,'snow',location,'hourly',0)

    t = time.localtime()
    print('Done at ' + time.strftime("%H:%M:%S", t) + ', now sleep for ' + str(conf['pull_freq']) + ' sec')
    time.sleep(conf['pull_freq'])