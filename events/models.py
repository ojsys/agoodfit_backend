from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid


class Event(models.Model):
    """Wellness events model"""
    
    # Event Types
    EVENT_TYPE_CHOICES = [
        ('cycling', 'Cycling'),
        ('running', 'Running'),
        ('yoga', 'Yoga'),
        ('strength', 'Strength Training'),
        ('mindfulness', 'Mindfulness'),
        ('nutrition', 'Nutrition'),
        ('outdoors', 'Outdoors'),
        ('swimming', 'Swimming'),
        ('hiking', 'Hiking'),
        ('pilates', 'Pilates'),
        ('dance', 'Dance'),
        ('boxing', 'Boxing'),
        ('climbing', 'Climbing'),
        ('meditation', 'Meditation'),
        ('social', 'Social Gathering'),
        ('workshop', 'Workshop'),
    ]
    
    # Vibe Choices
    VIBE_CHOICES = [
        ('chill', 'Chill'),
        ('social', 'Social'),
        ('intense', 'Intense'),
        ('beginner_friendly', 'Beginner Friendly'),
        ('advanced', 'Advanced'),
    ]
    
    # Price Type
    PRICE_TYPE_CHOICES = [
        ('free', 'Free'),
        ('paid', 'Paid'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Host Information
    host = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='hosted_events')
    host_group = models.ForeignKey('dashboard.Club', on_delete=models.SET_NULL, null=True, blank=True, related_name='events')
    
    # Event Details
    title = models.CharField(max_length=200)
    description = models.TextField()
    event_type = models.CharField(max_length=50, choices=EVENT_TYPE_CHOICES)
    vibe = models.CharField(max_length=50, choices=VIBE_CHOICES, default='social')
    
    # Location
    location_name = models.CharField(max_length=200)
    address = models.TextField()
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    
    # Date & Time
    start_date = models.DateField()
    start_time = models.TimeField()
    end_date = models.DateField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    timezone = models.CharField(max_length=50, default='UTC')
    
    # Capacity & Pricing
    max_attendees = models.PositiveIntegerField(default=50)
    price_type = models.CharField(max_length=20, choices=PRICE_TYPE_CHOICES, default='free')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=3, default='USD')
    
    # Media
    cover_image = models.ImageField(upload_to='event_covers/', blank=True, null=True)
    
    # What to bring
    what_to_bring = models.JSONField(default=list, blank=True)
    
    # Status
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Visibility
    is_public = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'events'
        ordering = ['-start_date', '-start_time']
    
    def __str__(self):
        return self.title
    
    @property
    def attendee_count(self):
        return self.rsvps.filter(status='going').count()
    
    @property
    def spots_remaining(self):
        return self.max_attendees - self.attendee_count


class RSVP(models.Model):
    """Event RSVP model"""
    
    STATUS_CHOICES = [
        ('going', 'Going'),
        ('maybe', 'Maybe'),
        ('not_going', 'Not Going'),
        ('waitlist', 'Waitlist'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='rsvps')
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='rsvps')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='going')
    guests_count = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)
    checked_in = models.BooleanField(default=False)
    checked_in_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'rsvps'
        unique_together = ['event', 'user']
    
    def __str__(self):
        return f"{self.user.email} - {self.event.title} - {self.status}"


class EventReview(models.Model):
    """Post-event reviews"""
    
    VIBE_TAGS = [
        ('supportive', 'Supportive'),
        ('motivating', 'Motivating'),
        ('great_mix', 'Great Mix of People'),
        ('a_vibe', 'A Vibe'),
        ('felt_safe', 'I Felt Safe'),
        ('well_organized', 'Well Organized'),
        ('fun', 'Fun'),
        ('challenging', 'Challenging'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='event_reviews')
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    review_text = models.TextField(blank=True)
    vibe_tags = models.JSONField(default=list, blank=True)
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'event_reviews'
        unique_together = ['event', 'user']
    
    def __str__(self):
        return f"{self.user.email} - {self.event.title} - {self.rating} stars"


class EventInvitation(models.Model):
    """Event invitations sent to users"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='invitations')
    sender = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='sent_invitations')
    recipient = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='received_invitations')
    message = models.TextField(blank=True)
    accepted = models.BooleanField(null=True, blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'event_invitations'
        unique_together = ['event', 'sender', 'recipient']
    
    def __str__(self):
        return f"{self.sender.email} invited {self.recipient.email} to {self.event.title}"


class SavedEvent(models.Model):
    """User's saved events"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='saved_events')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='saved_by')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'saved_events'
        unique_together = ['user', 'event']
    
    def __str__(self):
        return f"{self.user.email} saved {self.event.title}"
