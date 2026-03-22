"""
ASGI config for agoodfit_backend project.
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agoodfit_backend.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    # WebSocket configuration will be added here
    # "websocket": AuthMiddlewareStack(
    #     URLRouter(
    #         messaging.routing.websocket_urlpatterns
    #     )
    # ),
})
