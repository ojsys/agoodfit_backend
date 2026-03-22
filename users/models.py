from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid


class User(AbstractUser):
    """Custom User Model for A Good Fit App"""
    
    # User Types
    USER_TYPE_CHOICES = [
        ('standard', 'Standard User'),
        ('super', 'Super User'),
        ('admin', 'Admin'),
    ]
    
    # Profile Goal Choices
    GOAL_CHOICES = [
        ('community', 'Find Community'),
        ('fitness', 'Fitness Buddy'),
        ('romantic', 'Romantic Spark'),
        ('events', 'Local Events'),
        ('all', 'All of the Above'),
    ]
    
    # Privacy Settings
    PRIVACY_CHOICES = [
        ('public', 'Public'),
        ('friends', 'Friends Only'),
        ('anonymous', 'Anonymous'),
    ]

    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('non_binary', 'Non-Binary'),
        ('other', 'Other'),
        ('prefer_not_to_say', 'Prefer Not to Say'),
    ]

    FITNESS_LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('athlete', 'Athlete'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='standard')
    
    # Profile Information
    middle_name = models.CharField(max_length=50, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True)
    pronouns = models.CharField(max_length=50, blank=True)
    fitness_level = models.CharField(max_length=20, choices=FITNESS_LEVEL_CHOICES, blank=True)
    occupation = models.CharField(max_length=100, blank=True)
    website = models.URLField(max_length=200, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    profile_photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)
    hometown = models.CharField(max_length=100, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    
    # Onboarding Information
    primary_goal = models.CharField(max_length=20, choices=GOAL_CHOICES, default='all')
    privacy_setting = models.CharField(max_length=20, choices=PRIVACY_CHOICES, default='public')
    
    # Availability
    WEEKDAY = 'weekday'
    WEEKEND = 'weekend'
    BOTH = 'both'
    AVAILABILITY_CHOICES = [
        (WEEKDAY, 'Weekdays'),
        (WEEKEND, 'Weekends'),
        (BOTH, 'Both'),
    ]
    availability = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default=BOTH)
    
    # Motivation & Prompts
    motivation = models.TextField(max_length=200, blank=True, help_text="What motivates you to move?")
    wellness_looks_like = models.TextField(max_length=200, blank=True, help_text="Wellness looks like ___ to me")
    
    # Stats
    login_streak = models.PositiveIntegerField(default=0)
    workout_streak = models.PositiveIntegerField(default=0)
    last_login_date = models.DateField(null=True, blank=True)
    last_workout_date = models.DateField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Settings
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        db_table = 'users'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.email


class UserInterest(models.Model):
    """User's wellness interests"""
    
    INTEREST_CHOICES = [
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
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='interests')
    interest = models.CharField(max_length=50, choices=INTEREST_CHOICES)
    level = models.CharField(max_length=20, choices=[
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ], default='beginner')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_interests'
        unique_together = ['user', 'interest']
    
    def __str__(self):
        return f"{self.user.email} - {self.interest}"


class UserIntention(models.Model):
    """User's intentions on the platform"""
    
    INTENTION_CHOICES = [
        ('meet_people', 'Meet New People'),
        ('stay_fit', 'Stay Consistent with Workouts'),
        ('find_events', 'Find Wellness Events'),
        ('explore_dating', 'Explore Dating Intentionally'),
        ('try_new', 'Try New Things'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='intentions')
    intention = models.CharField(max_length=50, choices=INTENTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_intentions'
        unique_together = ['user', 'intention']
    
    def __str__(self):
        return f"{self.user.email} - {self.intention}"


class UserPhoto(models.Model):
    """Additional user photos"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='photos')
    photo = models.ImageField(upload_to='user_photos/')
    caption = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_photos'
        ordering = ['order', '-created_at']
    
    def __str__(self):
        return f"{self.user.email} - Photo {self.order}"


class UserPrompt(models.Model):
    """User profile prompts/answers"""
    
    PROMPT_CHOICES = [
        ('post_ride_snack', 'What\'s your go-to post-ride snack?'),
        ('workout_music', 'What\'s on your workout playlist?'),
        ('favorite_trail', 'Favorite local trail or route?'),
        ('wellness_routine', 'Describe your morning wellness routine'),
        ('fitness_goal', 'What\'s your current fitness goal?'),
        ('weekend_activity', 'Ideal weekend wellness activity?'),
        ('motivation', 'What keeps you motivated?'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prompts')
    prompt = models.CharField(max_length=100, choices=PROMPT_CHOICES)
    answer = models.TextField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_prompts'
    
    def __str__(self):
        return f"{self.user.email} - {self.prompt}"


class Follow(models.Model):
    """User following relationships"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'follows'
        unique_together = ['follower', 'following']
    
    def __str__(self):
        return f"{self.follower.email} follows {self.following.email}"


class Block(models.Model):
    """User blocking relationships"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    blocker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocked_users')
    blocked = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocked_by')
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'blocks'
        unique_together = ['blocker', 'blocked']
    
    def __str__(self):
        return f"{self.blocker.email} blocked {self.blocked.email}"
