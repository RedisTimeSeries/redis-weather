FROM python:3.8
ADD . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["python", "-u", "openweather_redis_exporter.py",  "openweather_redis_exporter.json"]