from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ClubViewSet, PlatformStatsViewSet, EventStatsViewSet,
    UserActivityLogViewSet, ModerationActionViewSet,
    NotificationViewSet, DashboardViewSet
)

router = DefaultRouter()
router.register(r'clubs', ClubViewSet, basename='club')
router.register(r'stats', PlatformStatsViewSet, basename='platform-stats')
router.register(r'event-stats', EventStatsViewSet, basename='event-stats')
router.register(r'activity-logs', UserActivityLogViewSet, basename='activity-log')
router.register(r'moderation', ModerationActionViewSet, basename='moderation')
router.register(r'notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/admin/', DashboardViewSet.as_view({'get': 'admin'}), name='admin-dashboard'),
    path('dashboard/super/', DashboardViewSet.as_view({'get': 'super_user'}), name='super-dashboard'),
    path('dashboard/user/', DashboardViewSet.as_view({'get': 'user'}), name='user-dashboard'),
]
