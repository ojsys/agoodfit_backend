from rest_framework import serializers
from .models import Event, RSVP, EventReview, EventInvitation, SavedEvent


class RSVPSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    
    class Meta:
        model = RSVP
        fields = ['id', 'user', 'status', 'guests_count', 'notes', 'checked_in', 'checked_in_at', 'created_at']
    
    def get_user(self, obj):
        from users.serializers import PublicUserSerializer
        return PublicUserSerializer(obj.user).data


class EventReviewSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    
    class Meta:
        model = EventReview
        fields = ['id', 'user', 'rating', 'review_text', 'vibe_tags', 'created_at']
    
    def get_user(self, obj):
        from users.serializers import PublicUserSerializer
        return PublicUserSerializer(obj.user).data


class EventSerializer(serializers.ModelSerializer):
    host = serializers.SerializerMethodField()
    attendee_count = serializers.ReadOnlyField()
    spots_remaining = serializers.ReadOnlyField()
    user_rsvp_status = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()
    
    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'event_type', 'vibe',
            'location_name', 'address', 'latitude', 'longitude',
            'start_date', 'start_time', 'end_date', 'end_time',
            'max_attendees', 'price_type', 'price', 'cover_image',
            'what_to_bring', 'status', 'is_public',
            'host', 'host_group', 'attendee_count', 'spots_remaining',
            'user_rsvp_status', 'is_saved',
            'created_at', 'updated_at'
        ]
    
    def get_host(self, obj):
        from users.serializers import PublicUserSerializer
        return PublicUserSerializer(obj.host).data
    
    def get_user_rsvp_status(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                rsvp = obj.rsvps.get(user=request.user)
                return rsvp.status
            except RSVP.DoesNotExist:
                return None
        return None
    
    def get_is_saved(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return SavedEvent.objects.filter(user=request.user, event=obj).exists()
        return False


class EventCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = [
            'title', 'description', 'event_type', 'vibe',
            'location_name', 'address', 'latitude', 'longitude',
            'start_date', 'start_time', 'end_date', 'end_time',
            'max_attendees', 'price_type', 'price', 'cover_image',
            'what_to_bring', 'is_public'
        ]


class EventDetailSerializer(serializers.ModelSerializer):
    host = serializers.SerializerMethodField()
    rsvps = RSVPSerializer(many=True, read_only=True)
    reviews = EventReviewSerializer(many=True, read_only=True)
    attendee_count = serializers.ReadOnlyField()
    spots_remaining = serializers.ReadOnlyField()
    user_rsvp_status = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()
    
    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'event_type', 'vibe',
            'location_name', 'address', 'latitude', 'longitude',
            'start_date', 'start_time', 'end_date', 'end_time',
            'max_attendees', 'price_type', 'price', 'cover_image',
            'what_to_bring', 'status', 'is_public',
            'host', 'host_group', 'rsvps', 'reviews',
            'attendee_count', 'spots_remaining',
            'user_rsvp_status', 'is_saved',
            'created_at', 'updated_at'
        ]
    
    def get_host(self, obj):
        from users.serializers import PublicUserSerializer
        return PublicUserSerializer(obj.host).data
    
    def get_user_rsvp_status(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                rsvp = obj.rsvps.get(user=request.user)
                return rsvp.status
            except RSVP.DoesNotExist:
                return None
        return None
    
    def get_is_saved(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return SavedEvent.objects.filter(user=request.user, event=obj).exists()
        return False


class RSVPUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RSVP
        fields = ['status', 'guests_count', 'notes']


class EventReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventReview
        fields = ['rating', 'review_text', 'vibe_tags']


class EventInvitationSerializer(serializers.ModelSerializer):
    sender = serializers.SerializerMethodField()
    recipient = serializers.SerializerMethodField()
    event = EventSerializer(read_only=True)
    
    class Meta:
        model = EventInvitation
        fields = ['id', 'sender', 'recipient', 'event', 'message', 'accepted', 'created_at']
    
    def get_sender(self, obj):
        from users.serializers import PublicUserSerializer
        return PublicUserSerializer(obj.sender).data
    
    def get_recipient(self, obj):
        from users.serializers import PublicUserSerializer
        return PublicUserSerializer(obj.recipient).data


class SavedEventSerializer(serializers.ModelSerializer):
    event = EventSerializer(read_only=True)
    
    class Meta:
        model = SavedEvent
        fields = ['id', 'event', 'created_at']
