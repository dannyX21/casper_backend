#!/bin/bash
set -e

cd /casper

python manage.py makemigrations

python manage.py migrate

exec "$@"