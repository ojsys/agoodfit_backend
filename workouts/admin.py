from django.contrib import admin
from .models import (
    Workout, WorkoutPhoto, WorkoutGoal, WorkoutStreak,
    PersonalRecord, WorkoutLike, WorkoutComment,
    LiveWorkoutSession, GPXRoute
)


@admin.register(Workout)
class WorkoutAdmin(admin.ModelAdmin):
    list_display = ['user', 'activity_type', 'start_time', 'duration_seconds', 'distance_km']
    list_filter = ['activity_type', 'source']
    date_hierarchy = 'start_time'


@admin.register(WorkoutPhoto)
class WorkoutPhotoAdmin(admin.ModelAdmin):
    list_display = ['user', 'caption', 'created_at']


@admin.register(WorkoutGoal)
class WorkoutGoalAdmin(admin.ModelAdmin):
    list_display = ['user', 'goal_type', 'target_value', 'current_value', 'is_completed']
    list_filter = ['goal_type', 'is_completed']


@admin.register(WorkoutStreak)
class WorkoutStreakAdmin(admin.ModelAdmin):
    list_display = ['user', 'current_streak', 'longest_streak', 'last_workout_date']


@admin.register(PersonalRecord)
class PersonalRecordAdmin(admin.ModelAdmin):
    list_display = ['user', 'record_type', 'value', 'unit', 'achieved_at']
    list_filter = ['record_type']


@admin.register(WorkoutLike)
class WorkoutLikeAdmin(admin.ModelAdmin):
    list_display = ['workout', 'user', 'created_at']


@admin.register(WorkoutComment)
class WorkoutCommentAdmin(admin.ModelAdmin):
    list_display = ['workout', 'user', 'text', 'created_at']


@admin.register(LiveWorkoutSession)
class LiveWorkoutSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'activity_type', 'status', 'started_at', 'current_distance_km']
    list_filter = ['activity_type', 'status']


@admin.register(GPXRoute)
class GPXRouteAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'activity_type', 'total_distance_km', 'times_used', 'is_public']
    list_filter = ['activity_type', 'is_public']
