from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from .models import Club, ClubMembership, PlatformStats, EventStats, UserActivityLog, ModerationAction, Notification
from .serializers import (
    ClubSerializer, ClubDetailSerializer, ClubCreateSerializer,
    ClubMembershipSerializer, PlatformStatsSerializer, EventStatsSerializer,
    UserActivityLogSerializer, ModerationActionSerializer, NotificationSerializer,
    AdminDashboardSerializer, SuperUserDashboardSerializer
)


class ClubViewSet(viewsets.ModelViewSet):
    """Club management viewset"""
    serializer_class = ClubSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Club.objects.filter(is_active=True)
        
        # Filter by city
        city = self.request.query_params.get('city')
        if city:
            queryset = queryset.filter(city__icontains=city)
        
        # Filter by type
        club_type = self.request.query_params.get('type')
        if club_type:
            queryset = queryset.filter(club_type=club_type)
        
        # Filter by search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
        
        return queryset.order_by('-member_count')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ClubCreateSerializer
        elif self.action == 'retrieve':
            return ClubDetailSerializer
        return ClubSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def perform_create(self, serializer):
        club = serializer.save(owner=self.request.user)
        # Add owner as member
        ClubMembership.objects.create(
            club=club,
            user=self.request.user,
            status='active',
            role='admin'
        )
    
    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        """Join a club"""
        club = self.get_object()
        user = request.user
        
        if club.members.filter(id=user.id).exists():
            return Response(
                {'error': 'Already a member'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        status_type = 'pending' if club.requires_approval else 'active'
        
        membership = ClubMembership.objects.create(
            club=club,
            user=user,
            status=status_type
        )
        
        club.update_member_count()
        
        return Response({
            'message': f'Membership request {status_type}',
            'status': status_type
        })
    
    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        """Leave a club"""
        club = self.get_object()
        
        deleted, _ = ClubMembership.objects.filter(
            club=club,
            user=request.user
        ).delete()
        
        if deleted:
            club.update_member_count()
            return Response({'message': 'Left club successfully'})
        
        return Response(
            {'error': 'Not a member of this club'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['post'])
    def approve_member(self, request, pk=None):
        """Approve a pending member (admin only)"""
        club = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user is admin
        try:
            membership = ClubMembership.objects.get(
                club=club,
                user=request.user,
                role__in=['admin', 'owner']
            )
        except ClubMembership.DoesNotExist:
            return Response(
                {'error': 'Only admins can approve members'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            pending_membership = ClubMembership.objects.get(
                club=club,
                user_id=user_id,
                status='pending'
            )
            pending_membership.status = 'active'
            pending_membership.save()
            
            club.update_member_count()
            
            return Response({'message': 'Member approved'})
        except ClubMembership.DoesNotExist:
            return Response(
                {'error': 'No pending membership found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def my_clubs(self, request):
        """Get clubs current user is a member of"""
        memberships = ClubMembership.objects.filter(
            user=request.user,
            status='active'
        ).select_related('club')
        
        clubs = [m.club for m in memberships]
        serializer = ClubSerializer(clubs, many=True, context={'request': request})
        return Response(serializer.data)


class PlatformStatsViewSet(viewsets.ReadOnlyModelViewSet):
    """Platform statistics viewset (Admin only)"""
    serializer_class = PlatformStatsSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Only admins can view platform stats
        if self.request.user.user_type != 'admin':
            return PlatformStats.objects.none()
        return PlatformStats.objects.all()
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get platform summary stats"""
        if request.user.user_type != 'admin':
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        from events.models import Event, RSVP
        from workouts.models import Workout
        from matching.models import Match
        from messaging.models import Report
        
        today = timezone.now().date()
        
        data = {
            'total_users': User.objects.count(),
            'active_users_today': User.objects.filter(
                last_login__date=today
            ).count(),
            'new_users_today': User.objects.filter(
                created_at__date=today
            ).count(),
            'total_events': Event.objects.count(),
            'events_today': Event.objects.filter(
                start_date=today
            ).count(),
            'total_workouts': Workout.objects.count(),
            'workouts_today': Workout.objects.filter(
                start_time__date=today
            ).count(),
            'total_matches': Match.objects.filter(status='accepted').count(),
            'matches_today': Match.objects.filter(
                matched_at__date=today
            ).count(),
            'pending_reports': Report.objects.filter(status='pending').count(),
            'recent_activity': UserActivityLogSerializer(
                UserActivityLog.objects.order_by('-created_at')[:10],
                many=True
            ).data
        }
        
        return Response(data)


class EventStatsViewSet(viewsets.ReadOnlyModelViewSet):
    """Event statistics viewset"""
    serializer_class = EventStatsSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Super users can see stats for their events
        if self.request.user.user_type == 'super':
            return EventStats.objects.filter(
                event__host=self.request.user
            )
        # Admins can see all
        elif self.request.user.user_type == 'admin':
            return EventStats.objects.all()
        return EventStats.objects.none()


class UserActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    """User activity log viewset (Admin only)"""
    serializer_class = UserActivityLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.user_type != 'admin':
            return UserActivityLog.objects.filter(user=self.request.user)
        return UserActivityLog.objects.all()


class ModerationActionViewSet(viewsets.ModelViewSet):
    """Moderation actions viewset (Admin only)"""
    serializer_class = ModerationActionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.user_type != 'admin':
            return ModerationAction.objects.filter(target_user=self.request.user)
        return ModerationAction.objects.all()
    
    def perform_create(self, serializer):
        serializer.save(moderator=self.request.user)


class NotificationViewSet(viewsets.ModelViewSet):
    """User notifications viewset"""
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Get unread notifications"""
        notifications = self.get_queryset().filter(is_read=False)
        serializer = self.get_serializer(notifications, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark notification as read"""
        notification = self.get_object()
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
        return Response({'message': 'Notification marked as read'})
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        self.get_queryset().filter(is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        return Response({'message': 'All notifications marked as read'})


class DashboardViewSet(viewsets.ViewSet):
    """Dashboard views for different user types"""
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def admin(self, request):
        """Admin dashboard"""
        if request.user.user_type != 'admin':
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        from events.models import Event, RSVP
        from workouts.models import Workout
        from matching.models import Match
        from messaging.models import Report
        
        today = timezone.now().date()
        
        data = {
            'total_users': User.objects.count(),
            'active_users_today': User.objects.filter(last_login__date=today).count(),
            'new_users_today': User.objects.filter(created_at__date=today).count(),
            'total_events': Event.objects.count(),
            'events_today': Event.objects.filter(start_date=today).count(),
            'total_workouts': Workout.objects.count(),
            'workouts_today': Workout.objects.filter(start_time__date=today).count(),
            'total_matches': Match.objects.filter(status='accepted').count(),
            'matches_today': Match.objects.filter(matched_at__date=today).count(),
            'pending_reports': Report.objects.filter(status='pending').count(),
            'recent_activity': UserActivityLogSerializer(
                UserActivityLog.objects.order_by('-created_at')[:10],
                many=True
            ).data
        }
        
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def super_user(self, request):
        """Super user (event host) dashboard"""
        if request.user.user_type not in ['super', 'admin']:
            return Response(
                {'error': 'Super user access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        from events.models import Event, RSVP, EventReview
        
        today = timezone.now().date()
        
        hosted_events = Event.objects.filter(host=request.user)
        upcoming_events = hosted_events.filter(start_date__gte=today)
        past_events = hosted_events.filter(start_date__lt=today)
        
        total_rsvps = RSVP.objects.filter(
            event__host=request.user,
            status='going'
        ).count()
        
        avg_rating = EventReview.objects.filter(
            event__host=request.user
        ).aggregate(Avg('rating'))['rating__avg'] or 0
        
        data = {
            'hosted_events_count': hosted_events.count(),
            'total_rsvps': total_rsvps,
            'average_event_rating': round(avg_rating, 2),
            'upcoming_events': upcoming_events.count(),
            'past_events': past_events.count(),
            'recent_events': [
                {
                    'id': str(e.id),
                    'title': e.title,
                    'start_date': e.start_date,
                    'attendee_count': e.attendee_count
                }
                for e in hosted_events.order_by('-created_at')[:5]
            ]
        }
        
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def user(self, request):
        """Regular user dashboard"""
        from events.models import RSVP
        from workouts.models import Workout
        from matching.models import Match
        
        user = request.user
        today = timezone.now().date()
        
        # Upcoming events
        upcoming_rsvps = RSVP.objects.filter(
            user=user,
            status__in=['going', 'maybe'],
            event__start_date__gte=today
        ).select_related('event')[:5]
        
        # Recent workouts
        recent_workouts = Workout.objects.filter(user=user).order_by('-start_time')[:5]
        
        # Matches
        matches = Match.objects.filter(
            Q(user1=user) | Q(user2=user),
            status='accepted'
        ).order_by('-matched_at')[:5]
        
        data = {
            'workout_streak': user.workout_streak,
            'login_streak': user.login_streak,
            'upcoming_events': [
                {
                    'id': str(rsvp.event.id),
                    'title': rsvp.event.title,
                    'start_date': rsvp.event.start_date,
                    'start_time': rsvp.event.start_time.strftime('%H:%M'),
                    'rsvp_status': rsvp.status
                }
                for rsvp in upcoming_rsvps
            ],
            'recent_workouts': [
                {
                    'id': str(w.id),
                    'activity_type': w.activity_type,
                    'duration_seconds': w.duration_seconds,
                    'distance_km': w.distance_km,
                    'start_time': w.start_time
                }
                for w in recent_workouts
            ],
            'recent_matches': [
                {
                    'id': str(m.id),
                    'match_type': m.match_type,
                    'matched_at': m.matched_at,
                    'other_user': m.user2.username if m.user1 == user else m.user1.username
                }
                for m in matches
            ]
        }
        
        return Response(data)
