"""
Production settings — MySQL via PyMySQL, strict security, WhiteNoise static files.
"""

import pymysql
pymysql.install_as_MySQLdb()   # Makes Django's MySQL backend use PyMySQL

from .base import *

DEBUG = False

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

# ─── Database (MySQL via PyMySQL) ─────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# ─── HTTPS & Cookie Security ──────────────────────────────────────────────────
# Set SECURE_SSL_REDIRECT=False if your cPanel/proxy handles HTTPS termination
SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'False') == 'True'
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# ─── CSRF ─────────────────────────────────────────────────────────────────────
_csrf = os.getenv('CSRF_TRUSTED_ORIGINS', '')
if _csrf:
    CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf.split(',') if o.strip()]

# ─── Email ────────────────────────────────────────────────────────────────────
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# ─── WebSockets / Channels ────────────────────────────────────────────────────
_redis_url = os.getenv('REDIS_URL', '')
if _redis_url:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {'hosts': [_redis_url]},
        }
    }
else:
    # Fallback — works for single-process deployments (no WebSocket fan-out)
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        }
    }

# ─── Celery ───────────────────────────────────────────────────────────────────
_redis_url = os.getenv('REDIS_URL', '')
if _redis_url:
    CELERY_BROKER_URL = _redis_url
    CELERY_RESULT_BACKEND = _redis_url
else:
    CELERY_TASK_ALWAYS_EAGER = True

CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

# ─── Logging ──────────────────────────────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}
