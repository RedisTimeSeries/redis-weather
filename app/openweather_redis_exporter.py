import urllib.request
import json
import redis 
import time
from datetime import datetime
from datetime import timezone
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

metrics=['sunrise','sunset','temp','feels_like','clouds','visibility','wind_deg','wind_gust','wind_speed','rain','snow']
units=conf['units']
if units == 'imperial':
    visibility_div=1609
else:   
    visibility_div=1000

r.delete("places")
r.delete('activities')

def ts_add_weather(ts,metric,location,mode,value):
    key_name='weather:' + location + ':' + mode + ':' + metric
    # if mode != 'current':
    #     r.execute_command('ts.add', key_name, ts, value)
    r.execute_command('ts.add', key_name, ts, value)

def ts_add_activity(ts,activity,location,value):
    key_name='activity:' + location + ':' + activity
    r.execute_command('ts.add', key_name, ts, value)

# def ts_add_activity_map(ts,activity,location,value):
#     key_name='activity:map:' + location + ':' + activity
#     r.execute_command('ts.add', key_name, ts, value)


def ts_init_location(location):
    r.sadd("places",location)
    for metric in metrics:
        if r.exists('weather:' + location + ':current:' + metric) == 0:
            r.execute_command('ts.create', 'weather:' + location + ':current:' + metric, 'labels', 'location', location, 'metric', metric, 'mode', 'current')
        r.delete('weather:' + location + ':hourly:' + metric)
        r.execute_command('ts.create', 'weather:' + location + ':hourly:' + metric, 'labels', 'location', location, 'metric', metric, 'mode', 'hourly')

def ts_init_activity():
    for place in conf['places']:
        r.delete(place['name'] + ':activities')
        for activity in place['activity']:
            r.delete('activity:' + place['name'] + ':' + activity)
            # r.delete('activity:map:' + place['name'] + ':' + activity)
            r.execute_command('ts.create', 'activity:' + place['name'] + ':' + activity, 'labels', 'location', place['name'], 'activity', activity, 'lat', place['lat'], 'lon', place['lon'], 'mode', 'activity_graph')
            r.sadd(place['name'] + ':activities', activity)
            r.sadd('activities', activity)
            r.sadd(activity + ':places', place['name'])
            # r.execute_command('ts.create', 'activity:map:' + place['name'] + ':' + activity, 'labels', 'location', place['name'], 'activity', activity, 'lat', place['lat'], 'lon', place['lon'], 'mode', 'activity_map')

def get_midnight(ts_current):
#    ts_current = datetime.utcfromtimestamp(float((dt['dt']+timezone_offset)))
    ts_midnight = datetime.combine(ts_current, datetime.min.time())
    ts_midnight = int(ts_midnight.replace(tzinfo=timezone.utc).timestamp())
    return (ts_midnight)

while True:
    ts_init_activity()
    for place in conf['places']:
        location = place['name']
        url = "https://api.openweathermap.org/data/2.5/onecall?lat=" + str(place['lat']) + "&lon=" + str(place['lon']) + "&units=" + units + "&exclude=minutely&appid=" + conf['open_weather_api']
        print(place['name'], url)
        response = urllib.request.urlopen(url)
        data = json.loads(response.read())
        data['current']=[data['current']]
        timezone_offset = int(data['timezone_offset'])
        ts_init_location(location)
        for mode in ['current','hourly']:
            for dt in data[mode]: 
                ts=(dt['dt']+timezone_offset)*1000
                ts_midnight=get_midnight(datetime.utcfromtimestamp(float((dt['dt']+timezone_offset))))    

                if mode == 'current':
                    ts_add_weather(ts,'dt',location,mode,ts)
                if 'sunrise' in dt:
                    ts_add_weather(ts,'sunrise',location,mode,(dt['sunrise']+timezone_offset)*1000)
                    sunrise_offset=dt['sunrise']+timezone_offset-ts_midnight
                if 'sunset' in dt:
                    ts_add_weather(ts,'sunset',location,mode,(dt['sunset']+timezone_offset)*1000)
                    sunset_offset=dt['sunset']+timezone_offset-ts_midnight
                if 'clouds' in dt:
                    ts_add_weather(ts,'clouds',location,mode,dt['clouds'])
                if 'visibility' in dt:
                    ts_add_weather(ts,'visibility',location,mode,dt['visibility']/visibility_div)
                if 'wind_speed' in dt:
                    ts_add_weather(ts,'wind_speed',location,mode,dt['wind_speed'])
                if 'wind_deg' in dt:
                    ts_add_weather(ts,'wind_deg',location,mode,dt['wind_deg'])
                if 'wind_gust' in dt:
                    ts_add_weather(ts,'wind_gust',location,mode,dt['wind_gust'])
                if 'temp' in dt:
                    ts_add_weather(ts,'temp',location,mode,dt['temp'])
                if 'feels_like' in dt:
                    ts_add_weather(ts,'feels_like',location,mode,dt['feels_like'])
                if 'rain' in dt:
                    ts_add_weather(ts,'rain',location,mode,dt['rain']['1h'])
                else:
                    ts_add_weather(ts,'rain',location,mode,0)
                if 'snow' in dt:
                    ts_add_weather(ts,'snow',location,mode,dt['snow']['1h'])
                else:
                    ts_add_weather(ts,'snow',location,mode,0)

                if mode == 'hourly':
                    # match_total = 0
                    for activity in place['activity']:
                        ts_midnight=get_midnight(datetime.utcfromtimestamp(float(ts/1000)))
                        if ts > (ts_midnight+sunrise_offset-3600)*1000 and ts < (ts_midnight+sunset_offset+3600)*1000:
                            match=1
                            for parameters in conf['activity:'+activity]:
                                metric = parameters['name']
                                metric_max = parameters['max']
                                metric_min = parameters['min']
                                if metric in dt:
                                    if metric in ['rain','snow']:
                                        if dt[metric]['1h'] < metric_min or dt[metric]['1h'] > metric_max:
                                            match=0
                                            break
                                    else:
                                        if dt[metric] < metric_min or dt[metric] > metric_max:
                                            match=0
                                            break
                        else:
                            match=0
                        ts_add_activity(ts,activity,location,match)
                        # match_total = match_total + match
                        # if match == 0:
                        #     ts_add_activity_map(ts,activity,location,0)
                        # else:
                        #     ts_add_activity_map(ts,activity,location,match_total)
        
        for dt in data['daily']: 
            ts=(dt['dt']+timezone_offset)*1000

            if ts-int(round(time.time() * 1000)) < 172800000:
                continue 

            ts_midnight=get_midnight(datetime.utcfromtimestamp(float((dt['dt']+timezone_offset))))    
            ts_night = (ts_midnight + 3*3600)*1000
            ts_morn = (ts_midnight + 9*3600)*1000
            ts_day = (ts_midnight + 15*3600)*1000
            ts_eve = (ts_midnight + 21*3600)*1000
                
            if 'sunrise' in dt:
                ts_add_weather(ts,'sunrise',location,'hourly',(dt['sunrise']+timezone_offset)*1000)
            if 'sunset' in dt:
                ts_add_weather(ts,'sunset',location,'hourly',(dt['sunset']+timezone_offset)*1000)
            if 'clouds' in dt:
                ts_add_weather(ts,'clouds',location,'hourly',dt['clouds'])
            if 'visibility' in dt:
                ts_add_weather(ts,'visibility',location,'hourly',dt['visibility']/visibility_div)
            if 'wind_speed' in dt:
                ts_add_weather(ts,'wind_speed',location,'hourly',dt['wind_speed'])
            if 'wind_deg' in dt:
                ts_add_weather(ts,'wind_deg',location,'hourly',dt['wind_deg'])
            if 'wind_gust' in dt:
                ts_add_weather(ts,'wind_gust',location,'hourly',dt['wind_gust'])
            if 'temp' in dt:
                ts_add_weather(ts_night,'temp',location,'hourly',dt['temp']['night'])
                ts_add_weather(ts_morn,'temp',location,'hourly',dt['temp']['morn'])
                ts_add_weather(ts_day,'temp',location,'hourly',dt['temp']['day'])
                ts_add_weather(ts_eve,'temp',location,'hourly',dt['temp']['eve'])
            if 'feels_like' in dt:
                ts_add_weather(ts_night,'feels_like',location,'hourly',dt['feels_like']['night'])
                ts_add_weather(ts_morn,'feels_like',location,'hourly',dt['feels_like']['morn'])
                ts_add_weather(ts_day,'feels_like',location,'hourly',dt['feels_like']['day'])
                ts_add_weather(ts_eve,'feels_like',location,'hourly',dt['feels_like']['eve'])
            if 'rain' in dt:
                ts_add_weather(ts,'rain',location,'hourly',dt['rain'])
            else:
                ts_add_weather(ts,'rain',location,'hourly',0)
            if 'snow' in dt:
                ts_add_weather(ts,'snow',location,'hourly',dt['snow'])
            else:
                ts_add_weather(ts,'snow',location,'hourly',0)

    t = time.localtime()
    print('Done at ' + time.strftime("%H:%M:%S", t) + ', now sleep for ' + str(conf['pull_freq']) + ' sec')
    time.sleep(conf['pull_freq'])