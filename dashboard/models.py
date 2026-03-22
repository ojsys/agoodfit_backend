from django.db import models
import uuid


class Club(models.Model):
    """Fitness clubs/crews that can host events"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Club Details
    name = models.CharField(max_length=200)
    description = models.TextField()
    slug = models.SlugField(unique=True)
    
    # Media
    logo = models.ImageField(upload_to='club_logos/', blank=True, null=True)
    cover_image = models.ImageField(upload_to='club_covers/', blank=True, null=True)
    
    # Location
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='USA')
    
    # Club Type
    CLUB_TYPES = [
        ('cycling', 'Cycling Club'),
        ('running', 'Running Club'),
        ('yoga', 'Yoga Studio'),
        ('gym', 'Gym/Fitness Center'),
        ('outdoor', 'Outdoor Adventure'),
        ('wellness', 'Wellness Community'),
        ('social', 'Social Fitness'),
        ('other', 'Other'),
    ]
    club_type = models.CharField(max_length=50, choices=CLUB_TYPES, default='other')
    
    # Owner & Admins
    owner = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='owned_clubs')
    admins = models.ManyToManyField('users.User', blank=True, related_name='admin_clubs')
    
    # Members
    members = models.ManyToManyField('users.User', through='ClubMembership', related_name='clubs')
    
    # Settings
    is_public = models.BooleanField(default=True)
    requires_approval = models.BooleanField(default=False)
    
    # Stats
    member_count = models.PositiveIntegerField(default=0)
    event_count = models.PositiveIntegerField(default=0)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'clubs'
        ordering = ['-member_count', '-created_at']
    
    def __str__(self):
        return self.name
    
    def update_member_count(self):
        self.member_count = self.memberships.filter(status='active').count()
        self.save()


class ClubMembership(models.Model):
    """Club membership model"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('banned', 'Banned'),
    ]
    
    ROLE_CHOICES = [
        ('member', 'Member'),
        ('moderator', 'Moderator'),
        ('admin', 'Admin'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='club_memberships')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'club_memberships'
        unique_together = ['club', 'user']
    
    def __str__(self):
        return f"{self.user.email} - {self.club.name}"


class PlatformStats(models.Model):
    """Daily platform statistics for admin dashboard"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField(unique=True)
    
    # User Stats
    total_users = models.PositiveIntegerField(default=0)
    new_users = models.PositiveIntegerField(default=0)
    active_users_daily = models.PositiveIntegerField(default=0)
    active_users_weekly = models.PositiveIntegerField(default=0)
    active_users_monthly = models.PositiveIntegerField(default=0)
    
    # Engagement Stats
    total_workouts_logged = models.PositiveIntegerField(default=0)
    total_events_created = models.PositiveIntegerField(default=0)
    total_rsvps = models.PositiveIntegerField(default=0)
    total_matches = models.PositiveIntegerField(default=0)
    total_messages_sent = models.PositiveIntegerField(default=0)
    
    # Retention
    day_1_retention = models.FloatField(default=0)
    day_7_retention = models.FloatField(default=0)
    day_30_retention = models.FloatField(default=0)
    
    # Workout Stats
    total_distance_km = models.FloatField(default=0)
    total_duration_seconds = models.PositiveBigIntegerField(default=0)
    total_calories_burned = models.PositiveBigIntegerField(default=0)
    
    # Event Stats
    event_check_ins = models.PositiveIntegerField(default=0)
    average_event_rating = models.FloatField(default=0)
    
    # Match Stats
    new_matches = models.PositiveIntegerField(default=0)
    match_acceptance_rate = models.FloatField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'platform_stats'
        ordering = ['-date']
    
    def __str__(self):
        return f"Stats for {self.date}"


class EventStats(models.Model):
    """Statistics for individual events"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.OneToOneField('events.Event', on_delete=models.CASCADE, related_name='stats')
    
    # RSVP Stats
    total_rsvps = models.PositiveIntegerField(default=0)
    going_count = models.PositiveIntegerField(default=0)
    maybe_count = models.PositiveIntegerField(default=0)
    not_going_count = models.PositiveIntegerField(default=0)
    waitlist_count = models.PositiveIntegerField(default=0)
    
    # Check-in Stats
    check_ins = models.PositiveIntegerField(default=0)
    check_in_rate = models.FloatField(default=0)
    
    # Review Stats
    total_reviews = models.PositiveIntegerField(default=0)
    average_rating = models.FloatField(default=0)
    
    # Engagement
    invitations_sent = models.PositiveIntegerField(default=0)
    invitations_accepted = models.PositiveIntegerField(default=0)
    
    # Demographics
    attendee_age_avg = models.FloatField(null=True, blank=True)
    attendee_gender_breakdown = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'event_stats'
    
    def __str__(self):
        return f"Stats for {self.event.title}"


class UserActivityLog(models.Model):
    """Log user activities for analytics"""
    
    ACTIVITY_TYPES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('profile_view', 'Profile View'),
        ('workout_log', 'Workout Log'),
        ('event_view', 'Event View'),
        ('event_rsvp', 'Event RSVP'),
        ('event_checkin', 'Event Check-in'),
        ('match_view', 'Match View'),
        ('match_action', 'Match Action'),
        ('message_sent', 'Message Sent'),
        ('settings_change', 'Settings Change'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='activity_logs')
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPES)
    
    # Additional data
    metadata = models.JSONField(default=dict, blank=True)
    
    # Location (if available)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_activity_logs'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.activity_type} - {self.created_at}"


class ModerationAction(models.Model):
    """Track moderation actions by admins"""
    
    ACTION_TYPES = [
        ('warn', 'Warning'),
        ('mute', 'Mute'),
        ('ban', 'Ban'),
        ('content_remove', 'Content Removal'),
        ('account_suspend', 'Account Suspension'),
        ('account_delete', 'Account Deletion'),
        ('promote_super', 'Promote to Super User'),
        ('demote_super', 'Demote from Super User'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Who took action
    moderator = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='moderation_actions')
    
    # Who was affected
    target_user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='moderation_received')
    
    # Action Details
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)
    reason = models.TextField()
    duration_days = models.PositiveIntegerField(null=True, blank=True)
    
    # Related content (if applicable)
    related_message = models.ForeignKey('messaging.Message', on_delete=models.SET_NULL, null=True, blank=True)
    related_event = models.ForeignKey('events.Event', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'moderation_actions'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.moderator.email} {self.action_type} {self.target_user.email}"


class Notification(models.Model):
    """User notifications"""
    
    NOTIFICATION_TYPES = [
        ('match', 'New Match'),
        ('message', 'New Message'),
        ('event_reminder', 'Event Reminder'),
        ('event_invite', 'Event Invitation'),
        ('rsvp_confirmation', 'RSVP Confirmation'),
        ('workout_milestone', 'Workout Milestone'),
        ('follow', 'New Follower'),
        ('wave', 'New Wave'),
        ('system', 'System Notification'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='notifications')
    
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    body = models.TextField()
    
    # Deep link data
    data = models.JSONField(default=dict, blank=True)
    
    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.title}"
