from rest_framework import serializers
from .models import DeviceToken, PushNotificationLog, NotificationPreference


class DeviceTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceToken
        fields = ['id', 'token', 'platform', 'device_name', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class PushNotificationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = PushNotificationLog
        fields = ['id', 'title', 'body', 'data', 'notification_type', 'status', 'created_at']
        read_only_fields = ['id', 'created_at']


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = [
            'push_enabled', 'push_workout_reminders', 'push_event_reminders',
            'push_new_matches', 'push_new_messages', 'push_social_activity',
            'email_enabled', 'email_weekly_summary', 'email_event_updates',
            'email_promotions', 'quiet_hours_enabled', 'quiet_hours_start',
            'quiet_hours_end'
        ]
