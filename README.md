# Dcard-Crawler-Analyzer
get Dcard & Meteor forum content and analyze ! <br>
And also provide a docker image version

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
* beautifulsoup4
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
cd app
python3 manage.py db init
python3 manage.py db migrate
python3 manage.py db upgrade
```

# Run
```bash=
cd app
python3 dcard.py  # for Dcard
python3 meteor.py   # for Meteor
```

# Docker image
You can also build crawler from dockerfile
```bash=
docker build . --tag uranusx86/forum_crawler --no-cache
docker run -dt --name forumcrawler -p 80:8000 uranusx86/forum_crawler
```
