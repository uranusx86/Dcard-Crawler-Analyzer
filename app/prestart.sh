#! /usr/bin/env bash

echo "Running inside /app/prestart.sh, you could add migrations to this file, e.g.:"

echo "
#! /usr/bin/env bash

# Let the DB start
sleep 10;
# Run migrations
alembic upgrade head
"

source /app/.env
python3 /app/manage.py db init   # for no "migrations" folder
#python3 /app/manage.py db stamp head    # for already exist "migrations" folder
python3 /app/manage.py db migrate
python3 /app/manage.py db upgrade