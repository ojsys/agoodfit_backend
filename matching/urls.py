from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MatchViewSet, WaveViewSet, UserDiscoverySettingsViewSet,
    DiscoveryViewSet, MatchSuggestionViewSet
)

router = DefaultRouter()
router.register(r'matches', MatchViewSet, basename='match')
router.register(r'waves', WaveViewSet, basename='wave')
router.register(r'settings', UserDiscoverySettingsViewSet, basename='discovery-settings')
router.register(r'suggestions', MatchSuggestionViewSet, basename='suggestion')

urlpatterns = [
    path('', include(router.urls)),
    path('discover/', DiscoveryViewSet.as_view({'get': 'discover'}), name='discover'),
    path('swipe/', DiscoveryViewSet.as_view({'post': 'swipe'}), name='swipe'),
]
