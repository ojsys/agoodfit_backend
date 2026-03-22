from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserInterest, UserIntention, UserPhoto, UserPrompt, Follow

User = get_user_model()


class UserInterestSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserInterest
        fields = ['id', 'interest', 'level', 'created_at']


class UserIntentionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserIntention
        fields = ['id', 'intention', 'created_at']


class UserPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPhoto
        fields = ['id', 'photo', 'caption', 'is_primary', 'order', 'created_at']


class UserPromptSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPrompt
        fields = ['id', 'prompt', 'answer', 'created_at']


class UserSerializer(serializers.ModelSerializer):
    interests = UserInterestSerializer(many=True, read_only=True)
    intentions = UserIntentionSerializer(many=True, read_only=True)
    photos = UserPhotoSerializer(many=True, read_only=True)
    prompts = UserPromptSerializer(many=True, read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'user_type', 'bio', 'profile_photo',
            'hometown', 'latitude', 'longitude', 'primary_goal', 'privacy_setting',
            'availability', 'motivation', 'wellness_looks_like', 'login_streak',
            'workout_streak', 'interests', 'intentions', 'photos', 'prompts',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserProfileSerializer(serializers.ModelSerializer):
    interests = UserInterestSerializer(many=True, read_only=True)
    intentions = UserIntentionSerializer(many=True, read_only=True)
    photos = UserPhotoSerializer(many=True, read_only=True)
    prompts = UserPromptSerializer(many=True, read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'bio', 'profile_photo',
            'hometown', 'latitude', 'longitude', 'primary_goal',
            'availability', 'motivation', 'wellness_looks_like',
            'login_streak', 'workout_streak',
            'interests', 'intentions', 'photos', 'prompts',
            'created_at'
        ]
        read_only_fields = ['id', 'email', 'created_at']


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'primary_goal']
    
    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
            primary_goal=validated_data.get('primary_goal', 'all')
        )
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'username', 'bio', 'hometown', 'latitude', 'longitude',
            'primary_goal', 'privacy_setting', 'availability',
            'motivation', 'wellness_looks_like'
        ]


class PublicUserSerializer(serializers.ModelSerializer):
    """Limited user info for public viewing"""
    interests = UserInterestSerializer(many=True, read_only=True)
    photos = UserPhotoSerializer(many=True, read_only=True)
    prompts = UserPromptSerializer(many=True, read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'bio', 'profile_photo',
            'hometown', 'interests', 'photos', 'prompts'
        ]


class FollowSerializer(serializers.ModelSerializer):
    follower = PublicUserSerializer(read_only=True)
    following = PublicUserSerializer(read_only=True)
    
    class Meta:
        model = Follow
        fields = ['id', 'follower', 'following', 'created_at']


class OnboardingSerializer(serializers.Serializer):
    """Serializer for onboarding flow"""
    primary_goal = serializers.ChoiceField(choices=User.GOAL_CHOICES)
    interests = serializers.ListField(
        child=serializers.DictField(),
        required=False
    )
    intentions = serializers.ListField(
        child=serializers.ChoiceField(choices=UserIntention.INTENTION_CHOICES),
        required=False
    )
    hometown = serializers.CharField(required=False, allow_blank=True)
    availability = serializers.ChoiceField(choices=User.AVAILABILITY_CHOICES, required=False)
    motivation = serializers.CharField(required=False, allow_blank=True)
    wellness_looks_like = serializers.CharField(required=False, allow_blank=True)
    privacy_setting = serializers.ChoiceField(choices=User.PRIVACY_CHOICES, required=False)
    latitude = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)
