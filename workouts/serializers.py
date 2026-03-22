from rest_framework import serializers
from .models import (
    Workout, WorkoutPhoto, WorkoutGoal, WorkoutStreak, PersonalRecord, 
    WorkoutLike, WorkoutComment, LiveWorkoutSession, GPXRoute
)


class WorkoutPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkoutPhoto
        fields = ['id', 'photo', 'caption', 'taken_at', 'location_lat', 'location_lng', 'created_at']


class WorkoutSerializer(serializers.ModelSerializer):
    photos = WorkoutPhotoSerializer(many=True, read_only=True)
    duration_formatted = serializers.ReadOnlyField()
    pace_per_km = serializers.ReadOnlyField()
    likes_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    is_liked_by_me = serializers.SerializerMethodField()
    
    class Meta:
        model = Workout
        fields = [
            'id', 'activity_type', 'title', 'description',
            'start_time', 'end_time', 'duration_seconds', 'duration_formatted',
            'distance_km', 'elevation_gain_m', 'elevation_loss_m',
            'calories_burned', 'avg_heart_rate', 'max_heart_rate',
            'avg_speed_kmh', 'max_speed_kmh', 'avg_cadence', 'max_cadence',
            'avg_power', 'max_power', 'source', 'external_id',
            'gps_data', 'photos', 'is_shared', 'shared_at',
            'duration_formatted', 'pace_per_km', 'likes_count',
            'comments_count', 'is_liked_by_me',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_likes_count(self, obj):
        return obj.likes.count()
    
    def get_comments_count(self, obj):
        return obj.comments.count()
    
    def get_is_liked_by_me(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False


class WorkoutCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workout
        fields = [
            'activity_type', 'title', 'description',
            'start_time', 'end_time', 'duration_seconds',
            'distance_km', 'elevation_gain_m', 'elevation_loss_m',
            'calories_burned', 'avg_heart_rate', 'max_heart_rate',
            'avg_speed_kmh', 'max_speed_kmh', 'avg_cadence', 'max_cadence',
            'avg_power', 'max_power', 'source', 'external_id',
            'gps_data', 'is_shared'
        ]


class WorkoutGoalSerializer(serializers.ModelSerializer):
    progress_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = WorkoutGoal
        fields = [
            'id', 'goal_type', 'target_value', 'current_value',
            'progress_percentage', 'start_date', 'end_date',
            'is_active', 'is_completed', 'completed_at',
            'created_at', 'updated_at'
        ]


class WorkoutGoalCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkoutGoal
        fields = ['goal_type', 'target_value', 'start_date', 'end_date']


class WorkoutStreakSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkoutStreak
        fields = ['id', 'current_streak', 'longest_streak', 'last_workout_date', 'updated_at']


class PersonalRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonalRecord
        fields = ['id', 'record_type', 'value', 'unit', 'achieved_at', 'created_at']


class WorkoutCommentSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    
    class Meta:
        model = WorkoutComment
        fields = ['id', 'user', 'text', 'created_at', 'updated_at']
    
    def get_user(self, obj):
        from users.serializers import PublicUserSerializer
        return PublicUserSerializer(obj.user).data


class WorkoutFeedSerializer(serializers.ModelSerializer):
    """Simplified workout serializer for feed"""
    user = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    is_liked_by_me = serializers.SerializerMethodField()
    
    class Meta:
        model = Workout
        fields = [
            'id', 'user', 'activity_type', 'title',
            'duration_seconds', 'distance_km', 'calories_burned',
            'photos', 'is_shared', 'shared_at',
            'likes_count', 'comments_count', 'is_liked_by_me',
            'created_at'
        ]
    
    def get_user(self, obj):
        from users.serializers import PublicUserSerializer
        return PublicUserSerializer(obj.user).data
    
    def get_likes_count(self, obj):
        return obj.likes.count()
    
    def get_comments_count(self, obj):
        return obj.comments.count()
    
    def get_is_liked_by_me(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False


class WorkoutStatsSerializer(serializers.Serializer):
    """Workout statistics summary"""
    total_workouts = serializers.IntegerField()
    total_distance_km = serializers.FloatField()
    total_duration_seconds = serializers.IntegerField()
    total_calories_burned = serializers.IntegerField()
    current_streak = serializers.IntegerField()
    longest_streak = serializers.IntegerField()
    this_week_workouts = serializers.IntegerField()
    this_month_workouts = serializers.IntegerField()


class LiveWorkoutSessionSerializer(serializers.ModelSerializer):
    elapsed_time_seconds = serializers.ReadOnlyField()
    average_speed_kmh = serializers.ReadOnlyField()
    pace_per_km = serializers.ReadOnlyField()
    
    class Meta:
        model = LiveWorkoutSession
        fields = [
            'id', 'activity_type', 'title', 'status',
            'started_at', 'paused_at', 'resumed_at', 'ended_at',
            'total_paused_seconds', 'current_distance_km',
            'current_duration_seconds', 'current_speed_kmh',
            'current_cadence', 'current_power', 'current_heart_rate',
            'current_altitude', 'current_lat', 'current_lng',
            'route_points', 'is_live_shared', 'final_workout',
            'elapsed_time_seconds', 'average_speed_kmh', 'pace_per_km'
        ]
        read_only_fields = ['id', 'started_at']


class GPXRouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = GPXRoute
        fields = [
            'id', 'name', 'description', 'route_points',
            'total_distance_km', 'total_elevation_gain_m',
            'activity_type', 'is_public', 'times_used', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'times_used']
