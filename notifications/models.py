from django.db import models
import uuid


class DeviceToken(models.Model):
    """Store FCM device tokens for push notifications"""
    
    PLATFORM_CHOICES = [
        ('ios', 'iOS'),
        ('android', 'Android'),
        ('web', 'Web'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='device_tokens')
    token = models.TextField()
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    device_name = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'device_tokens'
        unique_together = ['user', 'token']
    
    def __str__(self):
        return f"{self.user.email} - {self.platform}"


class PushNotificationLog(models.Model):
    """Log of sent push notifications"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='push_notifications')
    
    # Notification content
    title = models.CharField(max_length=200)
    body = models.TextField()
    data = models.JSONField(default=dict, blank=True)
    
    # Notification type
    notification_type = models.CharField(max_length=50)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    
    # Timestamps
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'push_notification_logs'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.title} - {self.status}"


class NotificationPreference(models.Model):
    """User notification preferences"""
    
    user = models.OneToOneField('users.User', on_delete=models.CASCADE, related_name='notification_preferences')
    
    # Push notification settings
    push_enabled = models.BooleanField(default=True)
    push_workout_reminders = models.BooleanField(default=True)
    push_event_reminders = models.BooleanField(default=True)
    push_new_matches = models.BooleanField(default=True)
    push_new_messages = models.BooleanField(default=True)
    push_social_activity = models.BooleanField(default=True)
    
    # Email notification settings
    email_enabled = models.BooleanField(default=True)
    email_weekly_summary = models.BooleanField(default=True)
    email_event_updates = models.BooleanField(default=True)
    email_promotions = models.BooleanField(default=False)
    
    # Quiet hours
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notification_preferences'
    
    def __str__(self):
        return f"{self.user.email} - Preferences"
