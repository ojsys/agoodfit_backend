from django.contrib import admin
from .models import (
    Club, ClubMembership, PlatformStats, EventStats,
    UserActivityLog, ModerationAction, Notification
)


@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'club_type', 'city', 'member_count', 'is_active']
    list_filter = ['club_type', 'is_active', 'is_public']
    search_fields = ['name', 'description', 'city']


@admin.register(ClubMembership)
class ClubMembershipAdmin(admin.ModelAdmin):
    list_display = ['club', 'user', 'status', 'role', 'joined_at']
    list_filter = ['status', 'role']


@admin.register(PlatformStats)
class PlatformStatsAdmin(admin.ModelAdmin):
    list_display = ['date', 'total_users', 'active_users_daily', 'new_users', 'total_workouts_logged']
    date_hierarchy = 'date'


@admin.register(EventStats)
class EventStatsAdmin(admin.ModelAdmin):
    list_display = ['event', 'total_rsvps', 'check_ins', 'average_rating']


@admin.register(UserActivityLog)
class UserActivityLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'activity_type', 'created_at']
    list_filter = ['activity_type']
    date_hierarchy = 'created_at'


@admin.register(ModerationAction)
class ModerationActionAdmin(admin.ModelAdmin):
    list_display = ['moderator', 'target_user', 'action_type', 'is_active', 'created_at']
    list_filter = ['action_type', 'is_active']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'title', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read']
