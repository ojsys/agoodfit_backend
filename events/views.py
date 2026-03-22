from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone
from .models import Event, RSVP, EventReview, EventInvitation, SavedEvent
from .serializers import (
    EventSerializer, EventCreateSerializer, EventDetailSerializer,
    RSVPSerializer, RSVPUpdateSerializer, EventReviewSerializer,
    EventReviewCreateSerializer, EventInvitationSerializer, SavedEventSerializer
)


class EventViewSet(viewsets.ModelViewSet):
    """Event management viewset"""
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Event.objects.filter(status='published')
        
        # Filter by event type
        event_type = self.request.query_params.get('type')
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        
        # Filter by vibe
        vibe = self.request.query_params.get('vibe')
        if vibe:
            queryset = queryset.filter(vibe=vibe)
        
        # Filter by date
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            queryset = queryset.filter(start_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(start_date__lte=date_to)
        
        # Filter by location (nearby events)
        lat = self.request.query_params.get('lat')
        lng = self.request.query_params.get('lng')
        radius = self.request.query_params.get('radius', 50)  # km
        
        if lat and lng:
            # Simple distance filter (for production, use PostGIS)
            lat = float(lat)
            lng = float(lng)
            radius = float(radius)
            
            # Rough bounding box filter
            lat_range = radius / 111  # 1 degree lat ~ 111 km
            lng_range = radius / (111 * abs(lat))
            
            queryset = queryset.filter(
                latitude__isnull=False,
                longitude__isnull=False,
                latitude__range=(lat - lat_range, lat + lat_range),
                longitude__range=(lng - lng_range, lng + lng_range)
            )
        
        # Filter by price
        price_type = self.request.query_params.get('price_type')
        if price_type:
            queryset = queryset.filter(price_type=price_type)
        
        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(location_name__icontains=search)
            )
        
        return queryset.order_by('start_date', 'start_time')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return EventCreateSerializer
        elif self.action == 'retrieve':
            return EventDetailSerializer
        return EventSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def perform_create(self, serializer):
        serializer.save(host=self.request.user, status='published')
    
    @action(detail=True, methods=['post'])
    def rsvp(self, request, pk=None):
        """RSVP to an event"""
        event = self.get_object()
        
        status_choice = request.data.get('status', 'going')
        guests_count = request.data.get('guests_count', 0)
        notes = request.data.get('notes', '')
        
        if status_choice not in ['going', 'maybe', 'not_going', 'waitlist']:
            return Response(
                {'error': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if event is full
        if status_choice == 'going' and event.spots_remaining <= 0:
            status_choice = 'waitlist'
        
        rsvp, created = RSVP.objects.update_or_create(
            event=event,
            user=request.user,
            defaults={
                'status': status_choice,
                'guests_count': guests_count,
                'notes': notes
            }
        )
        
        serializer = RSVPSerializer(rsvp)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel_rsvp(self, request, pk=None):
        """Cancel RSVP to an event"""
        event = self.get_object()
        
        deleted, _ = RSVP.objects.filter(
            event=event,
            user=request.user
        ).delete()
        
        if deleted:
            return Response({'message': 'RSVP cancelled successfully'})
        
        return Response(
            {'error': 'No RSVP found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    @action(detail=True, methods=['post'])
    def check_in(self, request, pk=None):
        """Check in to an event"""
        event = self.get_object()
        
        try:
            rsvp = event.rsvps.get(user=request.user)
        except RSVP.DoesNotExist:
            return Response(
                {'error': 'Must RSVP before checking in'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        rsvp.checked_in = True
        rsvp.checked_in_at = timezone.now()
        rsvp.save()
        
        serializer = RSVPSerializer(rsvp)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        """Leave a review for an event"""
        event = self.get_object()
        
        # Check if user attended
        try:
            rsvp = event.rsvps.get(user=request.user, checked_in=True)
        except RSVP.DoesNotExist:
            return Response(
                {'error': 'Must attend event before reviewing'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = EventReviewCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        review, created = EventReview.objects.update_or_create(
            event=event,
            user=request.user,
            defaults=serializer.validated_data
        )
        
        return Response(EventReviewSerializer(review).data)
    
    @action(detail=True, methods=['post'])
    def invite(self, request, pk=None):
        """Invite a user to an event"""
        event = self.get_object()
        recipient_id = request.data.get('recipient_id')
        message = request.data.get('message', '')
        
        if not recipient_id:
            return Response(
                {'error': 'recipient_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            recipient = User.objects.get(id=recipient_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        invitation, created = EventInvitation.objects.get_or_create(
            event=event,
            sender=request.user,
            recipient=recipient,
            defaults={'message': message}
        )
        
        if not created:
            return Response(
                {'error': 'Already invited this user'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response(EventInvitationSerializer(invitation).data)
    
    @action(detail=True, methods=['post'])
    def save_event(self, request, pk=None):
        """Save an event for later"""
        event = self.get_object()
        
        saved_event, created = SavedEvent.objects.get_or_create(
            user=request.user,
            event=event
        )
        
        if not created:
            saved_event.delete()
            return Response({'message': 'Event unsaved'})
        
        return Response({'message': 'Event saved'})
    
    @action(detail=False, methods=['get'])
    def my_events(self, request):
        """Get events hosted by current user"""
        events = Event.objects.filter(host=request.user)
        serializer = EventSerializer(events, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def attending(self, request):
        """Get events current user is attending"""
        rsvps = RSVP.objects.filter(
            user=request.user,
            status__in=['going', 'maybe']
        ).select_related('event')
        
        events = [rsvp.event for rsvp in rsvps]
        serializer = EventSerializer(events, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def saved(self, request):
        """Get saved events"""
        saved = SavedEvent.objects.filter(user=request.user).select_related('event')
        events = [s.event for s in saved]
        serializer = EventSerializer(events, many=True, context={'request': request})
        return Response(serializer.data)


class RSVPViewSet(viewsets.ModelViewSet):
    """RSVP management viewset"""
    serializer_class = RSVPSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return RSVP.objects.filter(user=self.request.user)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = RSVPUpdateSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(RSVPSerializer(instance).data)


class EventInvitationViewSet(viewsets.ModelViewSet):
    """Event invitations management"""
    serializer_class = EventInvitationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return EventInvitation.objects.filter(
            Q(sender=self.request.user) | Q(recipient=self.request.user)
        )
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """Accept an event invitation"""
        invitation = self.get_object()
        
        if invitation.recipient != request.user:
            return Response(
                {'error': 'Only recipient can accept invitation'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        invitation.accepted = True
        invitation.responded_at = timezone.now()
        invitation.save()
        
        # Auto-RSVP to the event
        RSVP.objects.get_or_create(
            event=invitation.event,
            user=request.user,
            defaults={'status': 'going'}
        )
        
        return Response(EventInvitationSerializer(invitation).data)
    
    @action(detail=True, methods=['post'])
    def decline(self, request, pk=None):
        """Decline an event invitation"""
        invitation = self.get_object()
        
        if invitation.recipient != request.user:
            return Response(
                {'error': 'Only recipient can decline invitation'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        invitation.accepted = False
        invitation.responded_at = timezone.now()
        invitation.save()
        
        return Response(EventInvitationSerializer(invitation).data)
