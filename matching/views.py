from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import Match, Wave, UserDiscoverySettings, Swipe, MatchSuggestion
from .serializers import (
    MatchSerializer, MatchCreateSerializer, WaveSerializer,
    UserDiscoverySettingsSerializer, SwipeSerializer, MatchSuggestionSerializer
)


class MatchViewSet(viewsets.ModelViewSet):
    """Match management viewset"""
    serializer_class = MatchSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return Match.objects.filter(
            Q(user1=user) | Q(user2=user)
        ).exclude(status='blocked')
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def create(self, request):
        """Create a new match"""
        user2_id = request.data.get('user2_id')
        match_type = request.data.get('match_type', 'fit_buddy')
        icebreaker = request.data.get('icebreaker_message', '')
        
        if not user2_id:
            return Response(
                {'error': 'user2_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            user2 = User.objects.get(id=user2_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if user2 == request.user:
            return Response(
                {'error': 'Cannot match with yourself'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if match already exists
        existing_match = Match.objects.filter(
            Q(user1=request.user, user2=user2) |
            Q(user1=user2, user2=request.user)
        ).first()
        
        if existing_match:
            return Response(
                MatchSerializer(existing_match, context={'request': request}).data
            )
        
        # Create match
        match = Match.objects.create(
            user1=request.user,
            user2=user2,
            match_type=match_type,
            initiated_by=request.user,
            icebreaker_message=icebreaker
        )
        
        return Response(
            MatchSerializer(match, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """Accept a match"""
        match = self.get_object()
        
        if match.status != 'pending':
            return Response(
                {'error': 'Match is not pending'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from django.utils import timezone
        match.status = 'accepted'
        match.matched_at = timezone.now()
        match.save()
        
        return Response(MatchSerializer(match, context={'request': request}).data)
    
    @action(detail=True, methods=['post'])
    def decline(self, request, pk=None):
        """Decline a match"""
        match = self.get_object()
        match.status = 'declined'
        match.save()
        
        return Response(MatchSerializer(match, context={'request': request}).data)
    
    @action(detail=True, methods=['post'])
    def block(self, request, pk=None):
        """Block a match"""
        match = self.get_object()
        match.status = 'blocked'
        match.save()
        
        return Response({'message': 'User blocked'})
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get pending matches"""
        matches = self.get_queryset().filter(status='pending')
        serializer = MatchSerializer(matches, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def accepted(self, request):
        """Get accepted matches"""
        matches = self.get_queryset().filter(status='accepted')
        serializer = MatchSerializer(matches, many=True, context={'request': request})
        return Response(serializer.data)


class WaveViewSet(viewsets.ModelViewSet):
    """Wave (light touch connection) management"""
    serializer_class = WaveSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Wave.objects.filter(
            Q(sender=self.request.user) | Q(recipient=self.request.user)
        )
    
    def create(self, request):
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
        
        if recipient == request.user:
            return Response(
                {'error': 'Cannot wave at yourself'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        wave, created = Wave.objects.get_or_create(
            sender=request.user,
            recipient=recipient,
            defaults={'message': message}
        )
        
        if not created:
            return Response(
                {'error': 'Already waved at this user'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response(WaveSerializer(wave).data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """Accept a wave"""
        wave = self.get_object()
        
        if wave.recipient != request.user:
            return Response(
                {'error': 'Only recipient can accept wave'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        from django.utils import timezone
        wave.status = 'accepted'
        wave.responded_at = timezone.now()
        wave.save()
        
        # Create a match
        Match.objects.get_or_create(
            user1=wave.sender,
            user2=wave.recipient,
            defaults={
                'match_type': 'community',
                'status': 'accepted',
                'matched_at': timezone.now()
            }
        )
        
        return Response(WaveSerializer(wave).data)
    
    @action(detail=True, methods=['post'])
    def decline(self, request, pk=None):
        """Decline a wave"""
        wave = self.get_object()
        
        if wave.recipient != request.user:
            return Response(
                {'error': 'Only recipient can decline wave'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        from django.utils import timezone
        wave.status = 'declined'
        wave.responded_at = timezone.now()
        wave.save()
        
        return Response(WaveSerializer(wave).data)


class UserDiscoverySettingsViewSet(viewsets.ModelViewSet):
    """User discovery settings management"""
    serializer_class = UserDiscoverySettingsSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserDiscoverySettings.objects.filter(user=self.request.user)
    
    def get_object(self):
        settings, created = UserDiscoverySettings.objects.get_or_create(
            user=self.request.user
        )
        return settings
    
    def list(self, request):
        """Get current user's discovery settings"""
        settings = self.get_object()
        serializer = self.get_serializer(settings)
        return Response(serializer.data)


class DiscoveryViewSet(viewsets.ViewSet):
    """Discovery/matching discovery viewset"""
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def discover(self, request):
        """Discover potential matches"""
        user = request.user
        
        # Get user's discovery settings
        try:
            settings = user.discovery_settings
        except UserDiscoverySettings.DoesNotExist:
            settings = UserDiscoverySettings.objects.create(user=user)
        
        # Get users to exclude (already matched, blocked, etc.)
        excluded_ids = set()
        
        # Already matched users
        matched_users = Match.objects.filter(
            Q(user1=user) | Q(user2=user)
        ).values_list('user1_id', 'user2_id')
        for match in matched_users:
            excluded_ids.update(match)
        
        # Blocked users
        from users.models import Block
        blocked = Block.objects.filter(
            Q(blocker=user) | Q(blocked=user)
        ).values_list('blocker_id', 'blocked_id')
        for b in blocked:
            excluded_ids.update(b)
        
        # Users already swiped
        swiped = Swipe.objects.filter(swiper=user).values_list('swiped_id', flat=True)
        excluded_ids.update(swiped)
        
        # Get discoverable users
        queryset = user.__class__.objects.filter(
            discovery_settings__discoverable=True
        ).exclude(
            id=user.id
        ).exclude(
            id__in=excluded_ids
        )
        
        # Filter by privacy
        queryset = queryset.filter(privacy_setting__in=['public', 'friends'])
        
        # Filter by location if available
        if user.latitude and user.longitude and settings.max_distance_km:
            # Simple bounding box filter
            lat_range = settings.max_distance_km / 111
            lng_range = settings.max_distance_km / (111 * abs(user.latitude))
            queryset = queryset.filter(
                latitude__isnull=False,
                longitude__isnull=False,
                latitude__range=(user.latitude - lat_range, user.latitude + lat_range),
                longitude__range=(user.longitude - lng_range, user.longitude + lng_range)
            )
        
        # Filter by interests if specified
        if settings.preferred_activities:
            user_interests = user.interests.values_list('interest', flat=True)
            queryset = queryset.filter(
                interests__interest__in=user_interests
            ).distinct()
        
        # Limit results
        users = queryset[:20]
        
        from users.serializers import PublicUserSerializer
        serializer = PublicUserSerializer(users, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def swipe(self, request):
        """Swipe on a user"""
        swiped_id = request.data.get('swiped_id')
        swipe_type = request.data.get('swipe_type', 'like')
        
        if not swiped_id:
            return Response(
                {'error': 'swiped_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            swiped = User.objects.get(id=swiped_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Record swipe
        Swipe.objects.create(
            swiper=request.user,
            swiped=swiped,
            swipe_type=swipe_type
        )
        
        # Check for mutual like (match)
        if swipe_type == 'like':
            mutual_like = Swipe.objects.filter(
                swiper=swiped,
                swiped=request.user,
                swipe_type='like'
            ).exists()
            
            if mutual_like:
                # Create match
                from django.utils import timezone
                match, created = Match.objects.get_or_create(
                    user1=request.user,
                    user2=swiped,
                    defaults={
                        'match_type': 'vibe_check',
                        'status': 'accepted',
                        'matched_at': timezone.now()
                    }
                )
                
                if created:
                    return Response({
                        'message': 'It\'s a match!',
                        'is_match': True,
                        'match': MatchSerializer(match, context={'request': request}).data
                    })
        
        return Response({'message': 'Swipe recorded', 'is_match': False})


class MatchSuggestionViewSet(viewsets.ReadOnlyModelViewSet):
    """Match suggestions viewset"""
    serializer_class = MatchSuggestionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return MatchSuggestion.objects.filter(
            user=self.request.user,
            is_acted_on=False
        ).order_by('-compatibility_score')[:10]
    
    @action(detail=True, methods=['post'])
    def dismiss(self, request, pk=None):
        """Dismiss a suggestion"""
        suggestion = self.get_object()
        suggestion.is_acted_on = True
        suggestion.action_taken = 'dismiss'
        suggestion.save()
        return Response({'message': 'Suggestion dismissed'})
