#!/bin/bash
# Run this script on the server after uploading files

set -e

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Collecting static files..."
python manage.py collectstatic --no-input

echo "Running migrations..."
python manage.py migrate

echo "Done. Restart your Python app in cPanel."
