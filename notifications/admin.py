from django.contrib import admin
from .models import DeviceToken, PushNotificationLog, NotificationPreference


@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'platform', 'device_name', 'is_active', 'created_at']
    list_filter = ['platform', 'is_active']
    search_fields = ['user__email', 'device_name']


@admin.register(PushNotificationLog)
class PushNotificationLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'notification_type', 'status', 'created_at']
    list_filter = ['notification_type', 'status']
    search_fields = ['user__email', 'title', 'body']


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'push_enabled', 'email_enabled', 'updated_at']
    list_filter = ['push_enabled', 'email_enabled']
