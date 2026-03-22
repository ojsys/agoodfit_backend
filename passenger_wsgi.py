"""
cPanel Passenger entry point — always uses production settings.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

os.environ['DJANGO_SETTINGS_MODULE'] = 'agoodfit_backend.settings.production'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
