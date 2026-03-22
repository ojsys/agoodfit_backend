from django.db import models
from django.core.validators import MinValueValidator
import uuid


class Workout(models.Model):
    """User workout tracking model"""
    
    # Activity Types
    ACTIVITY_TYPES = [
        ('cycling', 'Cycling'),
        ('running', 'Running'),
        ('walking', 'Walking'),
        ('yoga', 'Yoga'),
        ('strength', 'Strength Training'),
        ('swimming', 'Swimming'),
        ('hiking', 'Hiking'),
        ('pilates', 'Pilates'),
        ('dance', 'Dance'),
        ('boxing', 'Boxing'),
        ('climbing', 'Climbing'),
        ('meditation', 'Meditation'),
        ('hiit', 'HIIT'),
        ('crossfit', 'CrossFit'),
        ('other', 'Other'),
    ]
    
    # Source
    SOURCE_CHOICES = [
        ('manual', 'Manual Entry'),
        ('live_tracking', 'Live Tracking'),
        ('strava', 'Strava'),
        ('apple_health', 'Apple Health'),
        ('google_fit', 'Google Fit'),
        ('fitbit', 'Fitbit'),
        ('garmin', 'Garmin'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='workouts')
    
    # Activity Details
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPES)
    title = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    
    # Time & Duration
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(default=0, help_text="Duration in seconds")
    
    # Distance (for applicable activities)
    distance_km = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0)])
    
    # Elevation
    elevation_gain_m = models.FloatField(null=True, blank=True)
    elevation_loss_m = models.FloatField(null=True, blank=True)
    
    # Performance Metrics
    calories_burned = models.PositiveIntegerField(null=True, blank=True)
    avg_heart_rate = models.PositiveIntegerField(null=True, blank=True)
    max_heart_rate = models.PositiveIntegerField(null=True, blank=True)
    avg_speed_kmh = models.FloatField(null=True, blank=True)
    max_speed_kmh = models.FloatField(null=True, blank=True)
    
    # Cycling/Running Specific
    avg_cadence = models.PositiveIntegerField(null=True, blank=True)
    max_cadence = models.PositiveIntegerField(null=True, blank=True)
    avg_power = models.PositiveIntegerField(null=True, blank=True)
    max_power = models.PositiveIntegerField(null=True, blank=True)
    
    # Source
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES, default='manual')
    external_id = models.CharField(max_length=255, blank=True, help_text="External platform workout ID")
    
    # GPS Route Data
    gps_data = models.JSONField(default=dict, blank=True, help_text="GPS coordinates and timestamps")
    
    # Photos
    photos = models.ManyToManyField('WorkoutPhoto', blank=True, related_name='workouts')
    
    # Sharing
    is_shared = models.BooleanField(default=False)
    shared_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'workouts'
        ordering = ['-start_time']
    
    def __str__(self):
        return f"{self.user.email} - {self.activity_type} - {self.start_time.date()}"
    
    @property
    def duration_formatted(self):
        """Return duration in HH:MM:SS format"""
        hours = self.duration_seconds // 3600
        minutes = (self.duration_seconds % 3600) // 60
        seconds = self.duration_seconds % 60
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"
    
    @property
    def pace_per_km(self):
        """Calculate pace per km for running/walking"""
        if self.distance_km and self.distance_km > 0 and self.duration_seconds:
            pace_seconds = self.duration_seconds / self.distance_km
            minutes = int(pace_seconds // 60)
            seconds = int(pace_seconds % 60)
            return f"{minutes}:{seconds:02d}"
        return None


class WorkoutPhoto(models.Model):
    """Workout photos"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='workout_photos')
    photo = models.ImageField(upload_to='workout_photos/')
    caption = models.CharField(max_length=200, blank=True)
    taken_at = models.DateTimeField(null=True, blank=True)
    location_lat = models.FloatField(null=True, blank=True)
    location_lng = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'workout_photos'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - Workout Photo"


class WorkoutGoal(models.Model):
    """User workout goals"""
    
    GOAL_TYPES = [
        ('weekly_workouts', 'Weekly Workouts'),
        ('weekly_distance', 'Weekly Distance (km)'),
        ('weekly_duration', 'Weekly Duration (minutes)'),
        ('monthly_workouts', 'Monthly Workouts'),
        ('monthly_distance', 'Monthly Distance (km)'),
        ('streak_days', 'Workout Streak (days)'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='workout_goals')
    goal_type = models.CharField(max_length=50, choices=GOAL_TYPES)
    target_value = models.FloatField(validators=[MinValueValidator(0)])
    current_value = models.FloatField(default=0, validators=[MinValueValidator(0)])
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'workout_goals'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.goal_type} - {self.target_value}"
    
    @property
    def progress_percentage(self):
        if self.target_value > 0:
            return min(100, (self.current_value / self.target_value) * 100)
        return 0


class WorkoutStreak(models.Model):
    """Track user workout streaks"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='workout_streaks')
    current_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)
    last_workout_date = models.DateField(null=True, blank=True)
    streak_started_at = models.DateField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'workout_streaks'
    
    def __str__(self):
        return f"{self.user.email} - Current: {self.current_streak}, Longest: {self.longest_streak}"


class PersonalRecord(models.Model):
    """User personal records"""
    
    RECORD_TYPES = [
        ('fastest_5k', 'Fastest 5K'),
        ('fastest_10k', 'Fastest 10K'),
        ('half_marathon', 'Half Marathon'),
        ('marathon', 'Marathon'),
        ('longest_ride', 'Longest Ride'),
        ('max_power', 'Max Power'),
        ('max_speed', 'Max Speed'),
        ('longest_workout', 'Longest Workout'),
        ('most_calories', 'Most Calories Burned'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='personal_records')
    record_type = models.CharField(max_length=50, choices=RECORD_TYPES)
    value = models.FloatField()
    unit = models.CharField(max_length=50)
    workout = models.ForeignKey(Workout, on_delete=models.SET_NULL, null=True, blank=True)
    achieved_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'personal_records'
        ordering = ['-achieved_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.record_type} - {self.value} {self.unit}"


class WorkoutLike(models.Model):
    """Likes on shared workouts"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workout = models.ForeignKey(Workout, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='workout_likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'workout_likes'
        unique_together = ['workout', 'user']
    
    def __str__(self):
        return f"{self.user.email} liked {self.workout.id}"


class WorkoutComment(models.Model):
    """Comments on shared workouts"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workout = models.ForeignKey(Workout, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='workout_comments')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'workout_comments'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} commented on {self.workout.id}"


class LiveWorkoutSession(models.Model):
    """Active live workout tracking sessions"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='live_sessions')
    
    # Session details
    activity_type = models.CharField(max_length=50, choices=Workout.ACTIVITY_TYPES)
    title = models.CharField(max_length=200, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Timing
    started_at = models.DateTimeField(auto_now_add=True)
    paused_at = models.DateTimeField(null=True, blank=True)
    resumed_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    total_paused_seconds = models.PositiveIntegerField(default=0)
    
    # Current metrics (updated in real-time)
    current_distance_km = models.FloatField(default=0)
    current_duration_seconds = models.PositiveIntegerField(default=0)
    current_speed_kmh = models.FloatField(null=True, blank=True)
    current_cadence = models.PositiveIntegerField(null=True, blank=True)
    current_power = models.PositiveIntegerField(null=True, blank=True)
    current_heart_rate = models.PositiveIntegerField(null=True, blank=True)
    current_altitude = models.FloatField(null=True, blank=True)
    
    # Location
    current_lat = models.FloatField(null=True, blank=True)
    current_lng = models.FloatField(null=True, blank=True)
    
    # GPS route points (stored as JSON array)
    route_points = models.JSONField(default=list, help_text="Array of {lat, lng, timestamp, altitude, speed} objects")
    
    # Final workout reference
    final_workout = models.ForeignKey(Workout, on_delete=models.SET_NULL, null=True, blank=True, related_name='live_session')
    
    # Sharing
    is_live_shared = models.BooleanField(default=False, help_text="Share live location with friends")
    
    class Meta:
        db_table = 'live_workout_sessions'
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.user.email} - Live {self.activity_type} - {self.status}"
    
    @property
    def elapsed_time_seconds(self):
        """Calculate actual elapsed time accounting for pauses"""
        from django.utils import timezone
        import datetime
        
        if self.status == 'completed' or self.status == 'cancelled':
            if self.ended_at and self.started_at:
                return int((self.ended_at - self.started_at).total_seconds()) - self.total_paused_seconds
            return self.current_duration_seconds
        
        elapsed = (timezone.now() - self.started_at).total_seconds() - self.total_paused_seconds
        return int(elapsed)
    
    @property
    def average_speed_kmh(self):
        """Calculate average speed"""
        if self.current_distance_km > 0 and self.elapsed_time_seconds > 0:
            hours = self.elapsed_time_seconds / 3600
            return round(self.current_distance_km / hours, 2)
        return 0
    
    @property
    def pace_per_km(self):
        """Calculate current pace per km"""
        if self.current_distance_km > 0 and self.elapsed_time_seconds > 0:
            pace_seconds = self.elapsed_time_seconds / self.current_distance_km
            minutes = int(pace_seconds // 60)
            seconds = int(pace_seconds % 60)
            return f"{minutes}:{seconds:02d}"
        return "--:--"


class GPXRoute(models.Model):
    """Stored GPX routes for users to follow"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='gpx_routes')
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Route data
    route_points = models.JSONField(help_text="Array of {lat, lng, elevation} points")
    total_distance_km = models.FloatField()
    total_elevation_gain_m = models.FloatField(default=0)
    
    # Route type
    activity_type = models.CharField(max_length=50, choices=Workout.ACTIVITY_TYPES, default='cycling')
    
    # Visibility
    is_public = models.BooleanField(default=True)
    
    # Usage stats
    times_used = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'gpx_routes'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.total_distance_km}km"
