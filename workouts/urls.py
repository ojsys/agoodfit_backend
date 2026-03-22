from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    WorkoutViewSet, WorkoutGoalViewSet, WorkoutStreakViewSet,
    PersonalRecordViewSet, WorkoutCommentViewSet,
    LiveWorkoutSessionViewSet, GPXRouteViewSet
)

router = DefaultRouter()
router.register(r'', WorkoutViewSet, basename='workout')
router.register(r'goals', WorkoutGoalViewSet, basename='goal')
router.register(r'streaks', WorkoutStreakViewSet, basename='streak')
router.register(r'personal-records', PersonalRecordViewSet, basename='personal-record')
router.register(r'comments', WorkoutCommentViewSet, basename='comment')
router.register(r'live', LiveWorkoutSessionViewSet, basename='live-session')
router.register(r'routes', GPXRouteViewSet, basename='gpx-route')

urlpatterns = [
    path('', include(router.urls)),
]
