"""
Development settings — SQLite, debug toolbar, relaxed security.
"""

from .base import *

DEBUG = True

ALLOWED_HOSTS = ['*']

# SQLite — zero config for local development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Emails printed to console in dev
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# WebSockets — in-memory channel layer (no Redis needed locally)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    }
}

# Celery — uses Redis if available, otherwise tasks run eagerly (synchronously)
_redis_url = os.getenv('REDIS_URL', '')
if _redis_url:
    CELERY_BROKER_URL = _redis_url
    CELERY_RESULT_BACKEND = _redis_url
else:
    CELERY_TASK_ALWAYS_EAGER = True   # Run tasks inline, no broker needed

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}
