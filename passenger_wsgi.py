"""
cPanel Passenger entry point.
cPanel's Python App feature uses Passenger, which looks for this file.
"""
import os
import sys

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agoodfit_backend.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
