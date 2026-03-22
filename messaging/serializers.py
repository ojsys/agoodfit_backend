from rest_framework import serializers
from .models import Conversation, Message, MessageReadStatus, ConversationParticipant, IcebreakerPrompt, Report


class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.SerializerMethodField()
    is_read = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = [
            'id', 'sender', 'message_type', 'content',
            'media_url', 'location_lat', 'location_lng', 'location_name',
            'reactions', 'reply_to', 'is_edited', 'edited_at',
            'is_read', 'created_at'
        ]
    
    def get_sender(self, obj):
        from users.serializers import PublicUserSerializer
        return PublicUserSerializer(obj.sender).data
    
    def get_is_read(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Check if message is read by anyone other than sender
            return obj.read_by.exclude(user=obj.sender).filter(is_read=True).exists()
        return False


class MessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = [
            'message_type', 'content', 'media_url',
            'location_lat', 'location_lng', 'location_name',
            'reply_to'
        ]


class ConversationParticipantSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    
    class Meta:
        model = ConversationParticipant
        fields = ['user', 'role', 'is_muted', 'notifications_enabled', 'joined_at']
    
    def get_user(self, obj):
        from users.serializers import PublicUserSerializer
        return PublicUserSerializer(obj.user).data


class ConversationSerializer(serializers.ModelSerializer):
    participants = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = [
            'id', 'conversation_type', 'title', 'is_group',
            'participants', 'last_message_at', 'last_message_preview',
            'unread_count', 'created_at', 'updated_at'
        ]
    
    def get_participants(self, obj):
        participants = obj.participants.all()[:5]
        from users.serializers import PublicUserSerializer
        return PublicUserSerializer(participants, many=True).data
    
    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.messages.exclude(sender=request.user).exclude(
                read_by__user=request.user, read_by__is_read=True
            ).count()
        return 0


class ConversationDetailSerializer(serializers.ModelSerializer):
    participants = serializers.SerializerMethodField()
    messages = MessageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Conversation
        fields = [
            'id', 'conversation_type', 'title', 'is_group',
            'participants', 'messages', 'event',
            'last_message_at', 'created_at', 'updated_at'
        ]
    
    def get_participants(self, obj):
        from users.serializers import PublicUserSerializer
        return PublicUserSerializer(obj.participants.all(), many=True).data


class ConversationCreateSerializer(serializers.ModelSerializer):
    participant_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True
    )
    
    class Meta:
        model = Conversation
        fields = ['conversation_type', 'title', 'participant_ids', 'event']


class IcebreakerPromptSerializer(serializers.ModelSerializer):
    class Meta:
        model = IcebreakerPrompt
        fields = ['id', 'prompt', 'category', 'usage_count']


class ReportSerializer(serializers.ModelSerializer):
    reporter = serializers.SerializerMethodField()
    reported_user = serializers.SerializerMethodField()
    
    class Meta:
        model = Report
        fields = [
            'id', 'reporter', 'reported_user', 'report_type',
            'description', 'status', 'created_at'
        ]
    
    def get_reporter(self, obj):
        from users.serializers import PublicUserSerializer
        return PublicUserSerializer(obj.reporter).data
    
    def get_reported_user(self, obj):
        from users.serializers import PublicUserSerializer
        return PublicUserSerializer(obj.reported_user).data


class ReportCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ['reported_user', 'message', 'conversation', 'report_type', 'description']
