from django.db import models
import uuid


class Conversation(models.Model):
    """Chat conversations between users"""
    
    CONVERSATION_TYPES = [
        ('direct', 'Direct Message'),
        ('event', 'Event Group Chat'),
        ('match', 'Match Chat'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Conversation Type
    conversation_type = models.CharField(max_length=20, choices=CONVERSATION_TYPES, default='direct')
    
    # For event group chats
    event = models.ForeignKey('events.Event', on_delete=models.CASCADE, null=True, blank=True, related_name='conversations')
    
    # Participants
    participants = models.ManyToManyField('users.User', related_name='conversations')
    
    # Conversation Details
    title = models.CharField(max_length=200, blank=True)
    is_group = models.BooleanField(default=False)
    
    # For match conversations
    match = models.ForeignKey('matching.Match', on_delete=models.CASCADE, null=True, blank=True, related_name='conversations')
    
    # Metadata
    created_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Last message info
    last_message_at = models.DateTimeField(null=True, blank=True)
    last_message_preview = models.TextField(blank=True)
    
    class Meta:
        db_table = 'conversations'
        ordering = ['-last_message_at', '-created_at']
    
    def __str__(self):
        if self.title:
            return self.title
        participants = self.participants.all()
        return f"Chat between {', '.join([p.email for p in participants[:3]])}"
    
    @property
    def unread_count(self, user):
        """Get unread message count for a user"""
        return self.messages.filter(read_by__user=user, read_by__is_read=False).count()


class Message(models.Model):
    """Individual messages"""
    
    MESSAGE_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('location', 'Location'),
        ('event_invite', 'Event Invite'),
        ('workout_share', 'Workout Share'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='sent_messages')
    
    # Message Content
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default='text')
    content = models.TextField()
    
    # For media messages
    media_url = models.URLField(blank=True)
    
    # For location messages
    location_lat = models.FloatField(null=True, blank=True)
    location_lng = models.FloatField(null=True, blank=True)
    location_name = models.CharField(max_length=200, blank=True)
    
    # For event invites
    invited_event = models.ForeignKey('events.Event', on_delete=models.SET_NULL, null=True, blank=True)
    
    # For workout shares
    shared_workout = models.ForeignKey('workouts.Workout', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Reactions
    reactions = models.JSONField(default=dict, blank=True)
    
    # Reply to
    reply_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies')
    
    # Status
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'messages'
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.sender.email}: {self.content[:50]}"


class MessageReadStatus(models.Model):
    """Track message read status for each participant"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='read_by')
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='message_read_status')
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'message_read_status'
        unique_together = ['message', 'user']
    
    def __str__(self):
        return f"{self.user.email} - Message {self.message.id} - {'Read' if self.is_read else 'Unread'}"


class ConversationParticipant(models.Model):
    """Additional participant settings for conversations"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='participant_settings')
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='conversation_settings')
    
    # Settings
    is_muted = models.BooleanField(default=False)
    muted_until = models.DateTimeField(null=True, blank=True)
    
    # Notification settings
    notifications_enabled = models.BooleanField(default=True)
    
    # Role (for group chats)
    ROLE_CHOICES = [
        ('member', 'Member'),
        ('admin', 'Admin'),
        ('owner', 'Owner'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    
    # Last read message
    last_read_message = models.ForeignKey(Message, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Timestamps
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'conversation_participants'
        unique_together = ['conversation', 'user']
    
    def __str__(self):
        return f"{self.user.email} in {self.conversation.id}"


class IcebreakerPrompt(models.Model):
    """Pre-made icebreaker prompts for conversations"""
    
    CATEGORY_CHOICES = [
        ('fitness', 'Fitness'),
        ('general', 'General'),
        ('fun', 'Fun'),
        ('deep', 'Deep'),
        ('event', 'Event Related'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    prompt = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    is_active = models.BooleanField(default=True)
    usage_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'icebreaker_prompts'
        ordering = ['-usage_count']
    
    def __str__(self):
        return self.prompt[:50]


class Report(models.Model):
    """Message/conversation reports for moderation"""
    
    REPORT_TYPES = [
        ('spam', 'Spam'),
        ('harassment', 'Harassment'),
        ('inappropriate', 'Inappropriate Content'),
        ('fake_profile', 'Fake Profile'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reviewing', 'Under Review'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reporter = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='reports_made')
    reported_user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='reports_received')
    
    # What was reported
    message = models.ForeignKey(Message, on_delete=models.CASCADE, null=True, blank=True)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, null=True, blank=True)
    
    # Report Details
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES)
    description = models.TextField(blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='reports_reviewed')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'reports'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.reporter.email} reported {self.reported_user.email} - {self.report_type}"
