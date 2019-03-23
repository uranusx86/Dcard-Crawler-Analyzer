# Dcard-Crawler-Analyzer
get content and analyze ! <br>
And provide a docker image version

# Dependency
python3

## pypi package
* flask
* flask_script
* flask_migrate
* Flask-SQLAlchemy
* gunicorn
* requests
* cfscrape
* jieba

## apt package
* nodejs 8+

# Install
```bash=
# install dependency
apt-get install nodejs
pip install requirements.txt   # it highly recommend install packages in the virual env

# environment variable
export APP_SETTINGS="config.DevelopmentConfig"
export DATABASE_URL="sqlite:///WHERE_YOU_WANT_PUT_DB"

# database migration
python3 app/manage.py db init
python3 app/manage.py db migrate
python3 app/manage.py db upgrade
```

# Run
```bash=
python3 app/crawler.py
```

# Docker image
You can also build crawler from dockerfile
```bash=
docker build uranusx86/DcardCrawler
docker run -dt --name dcard_crawler -p 8080:80 uranusx86/DcardCrawler
```
