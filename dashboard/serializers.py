from rest_framework import serializers
from .models import Club, ClubMembership, PlatformStats, EventStats, UserActivityLog, ModerationAction, Notification


class ClubMembershipSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    
    class Meta:
        model = ClubMembership
        fields = ['id', 'user', 'status', 'role', 'joined_at']
    
    def get_user(self, obj):
        from users.serializers import PublicUserSerializer
        return PublicUserSerializer(obj.user).data


class ClubSerializer(serializers.ModelSerializer):
    owner = serializers.SerializerMethodField()
    member_count = serializers.ReadOnlyField()
    is_member = serializers.SerializerMethodField()
    
    class Meta:
        model = Club
        fields = [
            'id', 'name', 'description', 'slug', 'logo', 'cover_image',
            'city', 'state', 'country', 'club_type', 'owner',
            'member_count', 'is_public', 'requires_approval',
            'is_member', 'created_at'
        ]
    
    def get_owner(self, obj):
        from users.serializers import PublicUserSerializer
        return PublicUserSerializer(obj.owner).data
    
    def get_is_member(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.members.filter(id=request.user.id).exists()
        return False


class ClubDetailSerializer(serializers.ModelSerializer):
    owner = serializers.SerializerMethodField()
    admins = serializers.SerializerMethodField()
    members = serializers.SerializerMethodField()
    member_count = serializers.ReadOnlyField()
    is_member = serializers.SerializerMethodField()
    is_admin = serializers.SerializerMethodField()
    
    class Meta:
        model = Club
        fields = [
            'id', 'name', 'description', 'slug', 'logo', 'cover_image',
            'city', 'state', 'country', 'club_type', 'owner', 'admins',
            'members', 'member_count', 'is_public', 'requires_approval',
            'is_member', 'is_admin', 'created_at'
        ]
    
    def get_owner(self, obj):
        from users.serializers import PublicUserSerializer
        return PublicUserSerializer(obj.owner).data
    
    def get_admins(self, obj):
        from users.serializers import PublicUserSerializer
        return PublicUserSerializer(obj.admins.all()[:10], many=True).data
    
    def get_members(self, obj):
        from users.serializers import PublicUserSerializer
        memberships = obj.memberships.filter(status='active')[:20]
        users = [m.user for m in memberships]
        return PublicUserSerializer(users, many=True).data
    
    def get_is_member(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.members.filter(id=request.user.id).exists()
        return False
    
    def get_is_admin(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.admins.filter(id=request.user.id).exists() or obj.owner == request.user
        return False


class ClubCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Club
        fields = [
            'name', 'description', 'city', 'state', 'country',
            'club_type', 'logo', 'cover_image', 'is_public', 'requires_approval'
        ]


class PlatformStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlatformStats
        fields = [
            'date', 'total_users', 'new_users', 'active_users_daily',
            'active_users_weekly', 'active_users_monthly',
            'total_workouts_logged', 'total_events_created', 'total_rsvps',
            'total_matches', 'total_messages_sent',
            'day_1_retention', 'day_7_retention', 'day_30_retention',
            'total_distance_km', 'total_duration_seconds', 'total_calories_burned',
            'event_check_ins', 'average_event_rating',
            'new_matches', 'match_acceptance_rate'
        ]


class EventStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventStats
        fields = [
            'total_rsvps', 'going_count', 'maybe_count', 'not_going_count',
            'waitlist_count', 'check_ins', 'check_in_rate',
            'total_reviews', 'average_rating',
            'invitations_sent', 'invitations_accepted'
        ]


class UserActivityLogSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    
    class Meta:
        model = UserActivityLog
        fields = ['id', 'user', 'activity_type', 'metadata', 'created_at']
    
    def get_user(self, obj):
        from users.serializers import PublicUserSerializer
        return PublicUserSerializer(obj.user).data


class ModerationActionSerializer(serializers.ModelSerializer):
    moderator = serializers.SerializerMethodField()
    target_user = serializers.SerializerMethodField()
    
    class Meta:
        model = ModerationAction
        fields = [
            'id', 'moderator', 'target_user', 'action_type',
            'reason', 'duration_days', 'is_active', 'expires_at', 'created_at'
        ]
    
    def get_moderator(self, obj):
        from users.serializers import PublicUserSerializer
        return PublicUserSerializer(obj.moderator).data
    
    def get_target_user(self, obj):
        from users.serializers import PublicUserSerializer
        return PublicUserSerializer(obj.target_user).data


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type', 'title', 'body',
            'data', 'is_read', 'read_at', 'created_at'
        ]


class AdminDashboardSerializer(serializers.Serializer):
    """Admin dashboard summary"""
    total_users = serializers.IntegerField()
    active_users_today = serializers.IntegerField()
    new_users_today = serializers.IntegerField()
    total_events = serializers.IntegerField()
    events_today = serializers.IntegerField()
    total_workouts = serializers.IntegerField()
    workouts_today = serializers.IntegerField()
    total_matches = serializers.IntegerField()
    matches_today = serializers.IntegerField()
    pending_reports = serializers.IntegerField()
    recent_activity = UserActivityLogSerializer(many=True)


class SuperUserDashboardSerializer(serializers.Serializer):
    """Super user dashboard summary"""
    hosted_events_count = serializers.IntegerField()
    total_rsvps = serializers.IntegerField()
    average_event_rating = serializers.FloatField()
    upcoming_events = serializers.IntegerField()
    past_events = serializers.IntegerField()
    recent_events = serializers.ListField()
