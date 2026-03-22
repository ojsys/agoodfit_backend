from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DeviceTokenViewSet, PushNotificationLogViewSet, NotificationPreferenceViewSet

router = DefaultRouter()
router.register(r'device-tokens', DeviceTokenViewSet, basename='device-token')
router.register(r'history', PushNotificationLogViewSet, basename='notification-history')
router.register(r'preferences', NotificationPreferenceViewSet, basename='notification-preference')

urlpatterns = [
    path('', include(router.urls)),
]
