from django.db import models
import uuid


class Match(models.Model):
    """User matches model"""
    
    MATCH_TYPES = [
        ('fit_buddy', 'Fit Buddy'),
        ('vibe_check', 'Vibe Check'),
        ('community', 'Community Connector'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('blocked', 'Blocked'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Users involved in the match
    user1 = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='matches_as_user1')
    user2 = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='matches_as_user2')
    
    # Match Details
    match_type = models.CharField(max_length=50, choices=MATCH_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Who initiated the match
    initiated_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Match Score (algorithm-based compatibility)
    compatibility_score = models.FloatField(null=True, blank=True)
    
    # Shared interests that contributed to match
    shared_interests = models.JSONField(default=list, blank=True)
    
    # Mutual events (if matched through events)
    mutual_events = models.ManyToManyField('events.Event', blank=True)
    
    # Icebreaker sent
    icebreaker_sent = models.BooleanField(default=False)
    icebreaker_message = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    matched_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'matches'
        unique_together = ['user1', 'user2']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user1.email} <-> {self.user2.email} ({self.match_type})"
    
    @property
    def other_user(self, requesting_user):
        """Get the other user in the match"""
        if requesting_user == self.user1:
            return self.user2
        return self.user1


class Wave(models.Model):
    """Light touch connection (Wave) before matching"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sender = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='sent_waves')
    recipient = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='received_waves')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    message = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'waves'
        unique_together = ['sender', 'recipient']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.sender.email} waved at {self.recipient.email}"


class UserDiscoverySettings(models.Model):
    """User preferences for discovery/matching"""
    
    GENDER_PREFERENCES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('non_binary', 'Non-Binary'),
        ('all', 'All'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField('users.User', on_delete=models.CASCADE, related_name='discovery_settings')
    
    # Discovery Preferences
    discoverable = models.BooleanField(default=True)
    show_me_to = models.CharField(max_length=20, choices=GENDER_PREFERENCES, default='all')
    show_me = models.CharField(max_length=20, choices=GENDER_PREFERENCES, default='all')
    
    # Age Range
    min_age = models.PositiveIntegerField(default=18)
    max_age = models.PositiveIntegerField(default=65)
    
    # Distance (in km)
    max_distance_km = models.PositiveIntegerField(default=50)
    
    # Match Preferences
    looking_for_fitness_buddy = models.BooleanField(default=True)
    looking_for_romantic = models.BooleanField(default=True)
    looking_for_community = models.BooleanField(default=True)
    
    # Activity Preferences
    preferred_activities = models.JSONField(default=list, blank=True)
    
    # Experience Level
    min_experience_level = models.CharField(max_length=20, choices=[
        ('any', 'Any Level'),
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ], default='any')
    
    # Availability Filter
    match_availability = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_discovery_settings'
    
    def __str__(self):
        return f"{self.user.email} Discovery Settings"


class Swipe(models.Model):
    """Track user swipes for matching algorithm"""
    
    SWIPE_TYPES = [
        ('like', 'Like'),
        ('pass', 'Pass'),
        ('super_like', 'Super Like'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    swiper = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='swipes_made')
    swiped = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='swipes_received')
    swipe_type = models.CharField(max_length=20, choices=SWIPE_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'swipes'
        unique_together = ['swiper', 'swiped']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.swiper.email} {self.swipe_type}d {self.swiped.email}"


class MatchSuggestion(models.Model):
    """AI/Algorithm generated match suggestions"""
    
    REASON_CHOICES = [
        ('shared_interests', 'Shared Interests'),
        ('same_events', 'Attending Same Events'),
        ('location', 'Nearby Location'),
        ('activity_match', 'Activity Match'),
        ('goal_alignment', 'Goal Alignment'),
        ('mutual_friends', 'Mutual Connections'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='match_suggestions')
    suggested_user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='suggested_to')
    
    # Suggestion Details
    compatibility_score = models.FloatField()
    reason = models.CharField(max_length=50, choices=REASON_CHOICES)
    reason_details = models.TextField(blank=True)
    
    # Status
    is_viewed = models.BooleanField(default=False)
    is_acted_on = models.BooleanField(default=False)
    action_taken = models.CharField(max_length=20, blank=True)  # like, pass, etc.
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'match_suggestions'
        unique_together = ['user', 'suggested_user']
        ordering = ['-compatibility_score', '-created_at']
    
    def __str__(self):
        return f"Suggest {self.suggested_user.email} to {self.user.email}"
