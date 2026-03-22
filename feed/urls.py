from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PostViewSet, PostCommentViewSet

router = DefaultRouter()
router.register(r'posts', PostViewSet, basename='post')
router.register(r'comments', PostCommentViewSet, basename='comment')

urlpatterns = [
    path('', include(router.urls)),
]
