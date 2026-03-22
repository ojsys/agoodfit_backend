from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet, UserInterestViewSet, UserIntentionViewSet,
    UserPhotoViewSet, UserPromptViewSet, FollowViewSet
)

router = DefaultRouter()
router.register(r'', UserViewSet, basename='user')
router.register(r'interests', UserInterestViewSet, basename='interest')
router.register(r'intentions', UserIntentionViewSet, basename='intention')
router.register(r'photos', UserPhotoViewSet, basename='photo')
router.register(r'prompts', UserPromptViewSet, basename='prompt')
router.register(r'follows', FollowViewSet, basename='follow')

urlpatterns = [
    path('', include(router.urls)),
]
