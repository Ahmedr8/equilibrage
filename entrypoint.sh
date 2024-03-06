#!/bin/bash

source /venv/bin/activate
# Apply Django migrations
python manage.py migrate

# Start Gunicorn server
python manage.py runserver 0.0.0.0:8000
