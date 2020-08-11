# Grafana Smart Weather Dashboard

<div id="badges" align="center">

[![Grafana 7](https://img.shields.io/badge/Grafana-7-blue)](https://www.grafana.com)
[![RedisTimeSeries](https://img.shields.io/badge/RedisTimeSeries-inspired-yellowgreen)](https://oss.redislabs.com/redistimeseries/)
[![Grafana-Redis-Datasource](https://img.shields.io/badge/GrafanaRedisDatasource-integrated-yellow)](https://github.com/RedisTimeSeries/grafana-redis-datasource)

</div>


## Introduction

The purpose of this software is export current, hourly and daily weather forecast from https://openweathermap.org and display it on Grafana dashboards in the various numeric and graphs forms for a precise vision of the weather in the multiple locations, by multiple parameters, including temperature, wind speed, amount of precipitation, percent of cloudiness, a distance of visibility, etc.  There are a lot of interesting locations within a couple of hours drive from my house, and the weather can be very different from one to another. What I really want is a dashboard that shows the weather in a dozen locations on one screen, so I can compare conditions at a glance. Critically, I don’t just want to compare locations near each other.

![](docs/main_screen_shot.png)

The Docker container runs the following applications:

* openweather_redis_exporter.py - app to get weather metrics from https://openweathermap.org
* Redis database with RedisTimeSeries module - to store historical weather data and future forecasts
* Grafana with Redis Data Source - to display the weather data

The top section of the dashboard shows the current conditions for one location, which can be the primary or favorite or just selected from the list of available places (there is a Grafana template variable selection list in the top left corner of the dashboard). The bottom section shows weather conditions for a few different locations, so you can instantly compare the weather in various places.  
Grafana allows me to highlight low/high zones for temperature, dangerous zones for wind speed, display the degree of cloudiness, and mark periods of daytime and nighttime.


## Configuration


`openweather_redis_exporter.py` script comes together with the configuration file `openweather_redis_exporter.json`, which has a number of mandatory and optional parameters: 

```
{
	"units":"imperial"|"metric", #units format retrieving data from openweathermap.org. The default is "imperial", if you change it to "metric", you also need to update the units in Grafana dashboard
	"open_weather_api":"<api_key>", #provide your API key, which you will receive after the registration at openweathermap.org
	"redis_host":"host.docker.internal", #default Redis host
	"redis_port":6379, #default Redis port
	"pull_freq":1800, #default frequesncy of pulling data from openweathermap.org
	"places": #the list of locations to get the wether for
	[
        {
            "name":"Marlton", #Location name. Please note, current version doesn't support spaces in the names
            "lat":39.86, #lattitude
            "lon":-74.8, #longtitude
            "activity":[ "Bike" ] #reserved for future use
        },
		...
	]
}
```

There's nothing to configure in Redis.

Grafana comes with necessary default settings, including the Grafana Weather dashboard (you can modify this dashboard yourself later). The only thing you need to change in Grafana: Dashboard timezone setting should be `UTC`. This will ensure the data from locations in different time zone are displayed correctly: in a location local time. 

## Run using `docker-compose`

The project provides `docker-compose.yml` to start Redis with RedisTimeSeries module, Grafana 7.0 and OpenWeather data exporter.

```bash
docker-compose up
```

## What’s next

In the next version of my weather dashboard, I plan to display an activity type on the map according to the current conditions. The dashboard will show the places where the weather is suitable for specific activities like photography, skiing, hiking, climbing, drone flight, etc. Stay tuned! Or you can contribute to this project on GitHub. 

## Feedback

We love to hear from users, developers and the whole community interested by this plugin. These are various ways to get in touch with us:

- Ask a question, request a new feature and file a bug with GitHub issues.
- Star the repository to show your support.

## Contributing

- Fork the repository.
- Find an issue to work on and submit a pull request
- Could not find an issue? Look for documentation, bugs, typos, and missing features.

## Other interesting resources

- [RedisTimeSeries](https://oss.redislabs.com/redistimeseries/)
- [Grafana Redis Data Source](https://grafana.com/grafana/plugins/redis-datasource)

## License

- Apache License Version 2.0, see [LICENSE](LICENSE)