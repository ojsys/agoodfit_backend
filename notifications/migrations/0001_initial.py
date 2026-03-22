from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DeviceToken',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('token', models.TextField()),
                ('platform', models.CharField(choices=[('ios', 'iOS'), ('android', 'Android'), ('web', 'Web')], max_length=20)),
                ('device_name', models.CharField(blank=True, max_length=200)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='device_tokens', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'device_tokens',
                'unique_together': {('user', 'token')},
            },
        ),
        migrations.CreateModel(
            name='PushNotificationLog',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=200)),
                ('body', models.TextField()),
                ('data', models.JSONField(blank=True, default=dict)),
                ('notification_type', models.CharField(max_length=50)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('sent', 'Sent'), ('delivered', 'Delivered'), ('failed', 'Failed')], default='pending', max_length=20)),
                ('error_message', models.TextField(blank=True)),
                ('sent_at', models.DateTimeField(blank=True, null=True)),
                ('delivered_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='push_notifications', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'push_notification_logs',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='NotificationPreference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('push_enabled', models.BooleanField(default=True)),
                ('push_workout_reminders', models.BooleanField(default=True)),
                ('push_event_reminders', models.BooleanField(default=True)),
                ('push_new_matches', models.BooleanField(default=True)),
                ('push_new_messages', models.BooleanField(default=True)),
                ('push_social_activity', models.BooleanField(default=True)),
                ('email_enabled', models.BooleanField(default=True)),
                ('email_weekly_summary', models.BooleanField(default=True)),
                ('email_event_updates', models.BooleanField(default=True)),
                ('email_promotions', models.BooleanField(default=False)),
                ('quiet_hours_enabled', models.BooleanField(default=False)),
                ('quiet_hours_start', models.TimeField(blank=True, null=True)),
                ('quiet_hours_end', models.TimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='notification_preferences', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'notification_preferences',
            },
        ),
    ]
