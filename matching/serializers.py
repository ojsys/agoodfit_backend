from rest_framework import serializers
from .models import Match, Wave, UserDiscoverySettings, Swipe, MatchSuggestion


class MatchSerializer(serializers.ModelSerializer):
    other_user = serializers.SerializerMethodField()
    
    class Meta:
        model = Match
        fields = [
            'id', 'other_user', 'match_type', 'status',
            'compatibility_score', 'shared_interests',
            'icebreaker_sent', 'icebreaker_message',
            'created_at', 'matched_at'
        ]
    
    def get_other_user(self, obj):
        from users.serializers import PublicUserSerializer
        request = self.context.get('request')
        if request:
            if obj.user1 == request.user:
                return PublicUserSerializer(obj.user2).data
            return PublicUserSerializer(obj.user1).data
        return None


class MatchCreateSerializer(serializers.ModelSerializer):
    user2_id = serializers.UUIDField()
    
    class Meta:
        model = Match
        fields = ['user2_id', 'match_type', 'icebreaker_message']


class WaveSerializer(serializers.ModelSerializer):
    sender = serializers.SerializerMethodField()
    recipient = serializers.SerializerMethodField()
    
    class Meta:
        model = Wave
        fields = ['id', 'sender', 'recipient', 'status', 'message', 'created_at', 'responded_at']
    
    def get_sender(self, obj):
        from users.serializers import PublicUserSerializer
        return PublicUserSerializer(obj.sender).data
    
    def get_recipient(self, obj):
        from users.serializers import PublicUserSerializer
        return PublicUserSerializer(obj.recipient).data


class UserDiscoverySettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDiscoverySettings
        fields = [
            'id', 'discoverable', 'show_me_to', 'show_me',
            'min_age', 'max_age', 'max_distance_km',
            'looking_for_fitness_buddy', 'looking_for_romantic',
            'looking_for_community', 'preferred_activities',
            'min_experience_level', 'match_availability',
            'created_at', 'updated_at'
        ]


class SwipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Swipe
        fields = ['id', 'swiped', 'swipe_type', 'created_at']


class MatchSuggestionSerializer(serializers.ModelSerializer):
    suggested_user = serializers.SerializerMethodField()
    
    class Meta:
        model = MatchSuggestion
        fields = [
            'id', 'suggested_user', 'compatibility_score',
            'reason', 'reason_details', 'is_viewed',
            'created_at', 'expires_at'
        ]
    
    def get_suggested_user(self, obj):
        from users.serializers import PublicUserSerializer
        return PublicUserSerializer(obj.suggested_user).data


class DiscoveryProfileSerializer(serializers.Serializer):
    """Profile for discovery/matching"""
    id = serializers.UUIDField()
    username = serializers.CharField()
    bio = serializers.CharField()
    profile_photo = serializers.ImageField()
    hometown = serializers.CharField()
    interests = serializers.ListField()
    prompts = serializers.ListField()
    compatibility_score = serializers.FloatField()
    reason = serializers.CharField()
