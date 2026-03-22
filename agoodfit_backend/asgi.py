import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agoodfit_backend.settings.production')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    # WebSocket routes can be added here when needed
})
