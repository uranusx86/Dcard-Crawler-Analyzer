FROM python:3.6

LABEL maintainer="craweler"

RUN apt-get update
RUN apt-get install -y nano cron tzdata nodejs nodejs-legacy

# set timezone
RUN ln -fs /usr/share/zoneinfo/Asia/Taipei /etc/localtime && dpkg-reconfigure -f noninteractive tzdata

# Install app dependencies
COPY ./requirements.txt /requirements.txt
RUN pip3 install --upgrade pip
RUN pip install meinheld
RUN pip3 install -r /requirements.txt

COPY ./entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY ./start.sh /start.sh
RUN chmod +x /start.sh

# server config
COPY ./gunicorn_conf.py /gunicorn_conf.py

# app
COPY ./app /app/
WORKDIR /app/

# define environment variable
ENV PYTHONPATH=/app

EXPOSE 80

ENTRYPOINT ["/entrypoint.sh"]

# Run the start script, it will check for an /app/prestart.sh script (e.g. for migrations)
# And then will start Gunicorn with Meinheld
CMD ["/start.sh"]
