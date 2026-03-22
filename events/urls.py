from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EventViewSet, RSVPViewSet, EventInvitationViewSet

router = DefaultRouter()
router.register(r'', EventViewSet, basename='event')
router.register(r'rsvps', RSVPViewSet, basename='rsvp')
router.register(r'invitations', EventInvitationViewSet, basename='invitation')

urlpatterns = [
    path('', include(router.urls)),
]
