from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone
from .models import Conversation, Message, MessageReadStatus, ConversationParticipant, IcebreakerPrompt, Report
from .serializers import (
    ConversationSerializer, ConversationDetailSerializer, ConversationCreateSerializer,
    MessageSerializer, MessageCreateSerializer, IcebreakerPromptSerializer,
    ReportSerializer, ReportCreateSerializer
)


class ConversationViewSet(viewsets.ModelViewSet):
    """Conversation management viewset"""
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Conversation.objects.filter(
            participants=self.request.user
        ).order_by('-last_message_at')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ConversationCreateSerializer
        elif self.action == 'retrieve':
            return ConversationDetailSerializer
        return ConversationSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        participant_ids = serializer.validated_data.pop('participant_ids', [])
        
        # Create conversation
        conversation = Conversation.objects.create(
            created_by=request.user,
            **serializer.validated_data
        )
        
        # Add participants
        conversation.participants.add(request.user)
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        for user_id in participant_ids:
            try:
                user = User.objects.get(id=user_id)
                conversation.participants.add(user)
            except User.DoesNotExist:
                pass
        
        # Create participant settings
        ConversationParticipant.objects.create(
            conversation=conversation,
            user=request.user,
            role='owner'
        )
        
        return Response(
            ConversationSerializer(conversation, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )
    
    def retrieve(self, request, *args, **kwargs):
        """Get conversation with messages and mark as read"""
        conversation = self.get_object()
        
        # Mark messages as read
        self._mark_messages_as_read(conversation, request.user)
        
        serializer = self.get_serializer(conversation)
        return Response(serializer.data)
    
    def _mark_messages_as_read(self, conversation, user):
        """Mark all messages in conversation as read for user"""
        unread_messages = conversation.messages.exclude(sender=user)
        
        for message in unread_messages:
            MessageReadStatus.objects.get_or_create(
                message=message,
                user=user,
                defaults={'is_read': True, 'read_at': timezone.now()}
            )
    
    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """Send a message to conversation"""
        conversation = self.get_object()
        
        serializer = MessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            **serializer.validated_data
        )
        
        # Update conversation last message
        conversation.last_message_at = timezone.now()
        conversation.last_message_preview = message.content[:100]
        conversation.save()
        
        return Response(MessageSerializer(message, context={'request': request}).data)
    
    @action(detail=True, methods=['post'])
    def add_participant(self, request, pk=None):
        """Add participant to group conversation"""
        conversation = self.get_object()
        
        if not conversation.is_group:
            return Response(
                {'error': 'Can only add participants to group conversations'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user_id = request.data.get('user_id')
        if not user_id:
            return Response(
                {'error': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        conversation.participants.add(user)
        
        ConversationParticipant.objects.get_or_create(
            conversation=conversation,
            user=user,
            defaults={'role': 'member'}
        )
        
        return Response({'message': 'Participant added'})
    
    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        """Leave a conversation"""
        conversation = self.get_object()
        conversation.participants.remove(request.user)
        
        # Update participant settings
        ConversationParticipant.objects.filter(
            conversation=conversation,
            user=request.user
        ).update(left_at=timezone.now())
        
        return Response({'message': 'Left conversation'})
    
    @action(detail=True, methods=['post'])
    def mute(self, request, pk=None):
        """Mute/unmute conversation"""
        conversation = self.get_object()
        muted = request.data.get('muted', True)
        
        participant, created = ConversationParticipant.objects.get_or_create(
            conversation=conversation,
            user=request.user
        )
        
        participant.is_muted = muted
        participant.save()
        
        return Response({'message': f'Conversation {"muted" if muted else "unmuted"}'})


class MessageViewSet(viewsets.ModelViewSet):
    """Message management viewset"""
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Message.objects.filter(
            conversation__participants=self.request.user
        )
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    @action(detail=True, methods=['post'])
    def edit(self, request, pk=None):
        """Edit a message"""
        message = self.get_object()
        
        if message.sender != request.user:
            return Response(
                {'error': 'Can only edit your own messages'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        content = request.data.get('content')
        if not content:
            return Response(
                {'error': 'content is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        message.content = content
        message.is_edited = True
        message.edited_at = timezone.now()
        message.save()
        
        return Response(MessageSerializer(message, context={'request': request}).data)
    
    @action(detail=True, methods=['post'])
    def react(self, request, pk=None):
        """Add reaction to message"""
        message = self.get_object()
        reaction = request.data.get('reaction')
        
        if not reaction:
            return Response(
                {'error': 'reaction is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reactions = message.reactions or {}
        user_id = str(request.user.id)
        
        if user_id in reactions and reactions[user_id] == reaction:
            # Remove reaction if same
            del reactions[user_id]
        else:
            reactions[user_id] = reaction
        
        message.reactions = reactions
        message.save()
        
        return Response({'reactions': reactions})


class IcebreakerPromptViewSet(viewsets.ReadOnlyModelViewSet):
    """Icebreaker prompts viewset"""
    serializer_class = IcebreakerPromptSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return IcebreakerPrompt.objects.filter(is_active=True)
    
    @action(detail=False, methods=['get'])
    def random(self, request):
        """Get a random icebreaker prompt"""
        import random
        prompts = self.get_queryset()
        if prompts.exists():
            prompt = random.choice(list(prompts))
            # Increment usage count
            prompt.usage_count += 1
            prompt.save()
            return Response(IcebreakerPromptSerializer(prompt).data)
        return Response({'error': 'No prompts available'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get prompts by category"""
        category = request.query_params.get('category')
        if not category:
            return Response(
                {'error': 'category is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        prompts = self.get_queryset().filter(category=category)
        serializer = self.get_serializer(prompts, many=True)
        return Response(serializer.data)


class ReportViewSet(viewsets.ModelViewSet):
    """Report management viewset"""
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Report.objects.filter(reporter=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ReportCreateSerializer
        return ReportSerializer
    
    def perform_create(self, serializer):
        serializer.save(reporter=self.request.user)
