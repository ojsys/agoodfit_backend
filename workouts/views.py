from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import (
    Workout, WorkoutPhoto, WorkoutGoal, WorkoutStreak, PersonalRecord, 
    WorkoutLike, WorkoutComment, LiveWorkoutSession, GPXRoute
)
from .serializers import (
    WorkoutSerializer, WorkoutCreateSerializer, WorkoutGoalSerializer,
    WorkoutGoalCreateSerializer, WorkoutStreakSerializer, PersonalRecordSerializer,
    WorkoutCommentSerializer, WorkoutFeedSerializer, WorkoutStatsSerializer,
    LiveWorkoutSessionSerializer, GPXRouteSerializer
)


class WorkoutViewSet(viewsets.ModelViewSet):
    """Workout tracking viewset"""
    serializer_class = WorkoutSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Workout.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return WorkoutCreateSerializer
        return WorkoutSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def perform_create(self, serializer):
        workout = serializer.save(user=self.request.user)
        
        # Update user's workout streak
        self._update_workout_streak(self.request.user)
        
        # Update active goals
        self._update_goals(self.request.user, workout)
    
    def _update_workout_streak(self, user):
        """Update user's workout streak"""
        streak, created = WorkoutStreak.objects.get_or_create(user=user)
        
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        if streak.last_workout_date == yesterday or streak.last_workout_date is None:
            streak.current_streak += 1
            if streak.current_streak > streak.longest_streak:
                streak.longest_streak = streak.current_streak
        elif streak.last_workout_date != today:
            streak.current_streak = 1
        
        streak.last_workout_date = today
        streak.save()
        
        # Update user's workout streak field
        user.workout_streak = streak.current_streak
        user.last_workout_date = today
        user.save()
    
    def _update_goals(self, user, workout):
        """Update user's active goals"""
        active_goals = WorkoutGoal.objects.filter(
            user=user,
            is_active=True,
            is_completed=False,
            end_date__gte=timezone.now().date()
        )
        
        for goal in active_goals:
            if goal.goal_type == 'weekly_workouts':
                goal.current_value += 1
            elif goal.goal_type == 'weekly_distance' and workout.distance_km:
                goal.current_value += workout.distance_km
            elif goal.goal_type == 'weekly_duration':
                goal.current_value += workout.duration_seconds / 60
            elif goal.goal_type == 'monthly_workouts':
                goal.current_value += 1
            elif goal.goal_type == 'monthly_distance' and workout.distance_km:
                goal.current_value += workout.distance_km
            
            if goal.current_value >= goal.target_value:
                goal.is_completed = True
                goal.completed_at = timezone.now()
            
            goal.save()
    
    @action(detail=True, methods=['post'])
    def share(self, request, pk=None):
        """Share workout to feed"""
        workout = self.get_object()
        workout.is_shared = True
        workout.shared_at = timezone.now()
        workout.save()
        
        return Response({'message': 'Workout shared successfully'})
    
    @action(detail=True, methods=['post'])
    def unshare(self, request, pk=None):
        """Unshare workout from feed"""
        workout = self.get_object()
        workout.is_shared = False
        workout.shared_at = None
        workout.save()
        
        return Response({'message': 'Workout unshared'})
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """Like a workout"""
        workout = self.get_object()
        
        like, created = WorkoutLike.objects.get_or_create(
            workout=workout,
            user=request.user
        )
        
        if not created:
            like.delete()
            return Response({'message': 'Workout unliked', 'liked': False})
        
        return Response({'message': 'Workout liked', 'liked': True})
    
    @action(detail=True, methods=['post'])
    def comment(self, request, pk=None):
        """Add comment to workout"""
        workout = self.get_object()
        text = request.data.get('text')
        
        if not text:
            return Response(
                {'error': 'Comment text is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        comment = WorkoutComment.objects.create(
            workout=workout,
            user=request.user,
            text=text
        )
        
        return Response(WorkoutCommentSerializer(comment).data)
    
    @action(detail=False, methods=['get'])
    def feed(self, request):
        """Get workout feed from followed users"""
        # Get users the current user follows
        following_ids = request.user.following.values_list('following_id', flat=True)
        
        # Get shared workouts from followed users
        workouts = Workout.objects.filter(
            user_id__in=following_ids,
            is_shared=True
        ).order_by('-shared_at')[:50]
        
        serializer = WorkoutFeedSerializer(workouts, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get workout statistics"""
        user = request.user
        
        # Get all workouts
        workouts = Workout.objects.filter(user=user)
        
        # Calculate stats
        total_workouts = workouts.count()
        total_distance = workouts.aggregate(Sum('distance_km'))['distance_km__sum'] or 0
        total_duration = workouts.aggregate(Sum('duration_seconds'))['duration_seconds__sum'] or 0
        total_calories = workouts.aggregate(Sum('calories_burned'))['calories_burned__sum'] or 0
        
        # Get streak info
        try:
            streak = WorkoutStreak.objects.get(user=user)
            current_streak = streak.current_streak
            longest_streak = streak.longest_streak
        except WorkoutStreak.DoesNotExist:
            current_streak = 0
            longest_streak = 0
        
        # This week
        week_start = timezone.now() - timedelta(days=7)
        this_week_workouts = workouts.filter(start_time__gte=week_start).count()
        
        # This month
        month_start = timezone.now() - timedelta(days=30)
        this_month_workouts = workouts.filter(start_time__gte=month_start).count()
        
        stats = {
            'total_workouts': total_workouts,
            'total_distance_km': round(total_distance, 2),
            'total_duration_seconds': total_duration,
            'total_calories_burned': total_calories,
            'current_streak': current_streak,
            'longest_streak': longest_streak,
            'this_week_workouts': this_week_workouts,
            'this_month_workouts': this_month_workouts
        }
        
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def activities(self, request):
        """Get available activity types"""
        activities = [
            {'value': value, 'label': label}
            for value, label in Workout.ACTIVITY_TYPES
        ]
        return Response(activities)


class WorkoutGoalViewSet(viewsets.ModelViewSet):
    """Workout goals management"""
    serializer_class = WorkoutGoalSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return WorkoutGoal.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return WorkoutGoalCreateSerializer
        return WorkoutGoalSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get active goals"""
        goals = self.get_queryset().filter(
            is_active=True,
            is_completed=False
        )
        serializer = self.get_serializer(goals, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def completed(self, request):
        """Get completed goals"""
        goals = self.get_queryset().filter(is_completed=True)
        serializer = self.get_serializer(goals, many=True)
        return Response(serializer.data)


class WorkoutStreakViewSet(viewsets.ReadOnlyModelViewSet):
    """Workout streak viewset"""
    serializer_class = WorkoutStreakSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return WorkoutStreak.objects.filter(user=self.request.user)


class PersonalRecordViewSet(viewsets.ModelViewSet):
    """Personal records management"""
    serializer_class = PersonalRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return PersonalRecord.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class WorkoutCommentViewSet(viewsets.ModelViewSet):
    """Workout comments management"""
    serializer_class = WorkoutCommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return WorkoutComment.objects.filter(workout__user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class LiveWorkoutSessionViewSet(viewsets.ModelViewSet):
    """Live workout tracking viewset"""
    serializer_class = LiveWorkoutSessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return LiveWorkoutSession.objects.filter(user=self.request.user)
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    @action(detail=False, methods=['post'])
    def start(self, request):
        """Start a new live workout session"""
        activity_type = request.data.get('activity_type')
        title = request.data.get('title', '')
        is_live_shared = request.data.get('is_live_shared', False)
        
        if not activity_type:
            return Response(
                {'error': 'activity_type is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if there's already an active session
        active_session = LiveWorkoutSession.objects.filter(
            user=request.user,
            status__in=['active', 'paused']
        ).first()
        
        if active_session:
            return Response(
                {'error': 'You already have an active workout session'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        session = LiveWorkoutSession.objects.create(
            user=request.user,
            activity_type=activity_type,
            title=title,
            is_live_shared=is_live_shared,
            status='active'
        )
        
        return Response(
            LiveWorkoutSessionSerializer(session).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def update_location(self, request, pk=None):
        """Update current location and metrics during live workout"""
        session = self.get_object()
        
        if session.status != 'active':
            return Response(
                {'error': 'Session is not active'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get location data
        lat = request.data.get('lat')
        lng = request.data.get('lng')
        altitude = request.data.get('altitude')
        speed = request.data.get('speed')
        cadence = request.data.get('cadence')
        power = request.data.get('power')
        heart_rate = request.data.get('heart_rate')
        distance = request.data.get('distance_km')
        
        # Add route point
        if lat is not None and lng is not None:
            point = {
                'lat': lat,
                'lng': lng,
                'timestamp': timezone.now().isoformat(),
                'altitude': altitude,
                'speed': speed,
            }
            session.route_points.append(point)
            session.current_lat = lat
            session.current_lng = lng
        
        # Update metrics
        if altitude is not None:
            session.current_altitude = altitude
        if speed is not None:
            session.current_speed_kmh = speed
        if cadence is not None:
            session.current_cadence = cadence
        if power is not None:
            session.current_power = power
        if heart_rate is not None:
            session.current_heart_rate = heart_rate
        if distance is not None:
            session.current_distance_km = distance
        
        # Update duration
        session.current_duration_seconds = session.elapsed_time_seconds
        
        session.save()
        
        return Response(LiveWorkoutSessionSerializer(session).data)
    
    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """Pause the workout session"""
        session = self.get_object()
        
        if session.status != 'active':
            return Response(
                {'error': 'Session is not active'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        session.status = 'paused'
        session.paused_at = timezone.now()
        session.save()
        
        return Response(LiveWorkoutSessionSerializer(session).data)
    
    @action(detail=True, methods=['post'])
    def resume(self, request, pk=None):
        """Resume the workout session"""
        session = self.get_object()
        
        if session.status != 'paused':
            return Response(
                {'error': 'Session is not paused'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calculate paused duration
        if session.paused_at:
            paused_duration = (timezone.now() - session.paused_at).total_seconds()
            session.total_paused_seconds += int(paused_duration)
        
        session.status = 'active'
        session.resumed_at = timezone.now()
        session.save()
        
        return Response(LiveWorkoutSessionSerializer(session).data)
    
    @action(detail=True, methods=['post'])
    def finish(self, request, pk=None):
        """Finish the workout and create a permanent record"""
        session = self.get_object()
        
        if session.status not in ['active', 'paused']:
            return Response(
                {'error': 'Session cannot be finished'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create the final workout record
        workout = Workout.objects.create(
            user=request.user,
            activity_type=session.activity_type,
            title=session.title or f"Live {session.activity_type.title()}",
            start_time=session.started_at,
            end_time=timezone.now(),
            duration_seconds=session.elapsed_time_seconds,
            distance_km=session.current_distance_km if session.current_distance_km > 0 else None,
            avg_speed_kmh=session.average_speed_kmh if session.average_speed_kmh > 0 else None,
            gps_data={'route_points': session.route_points},
            source='live_tracking'
        )
        
        # Update session
        session.status = 'completed'
        session.ended_at = timezone.now()
        session.final_workout = workout
        session.save()
        
        # Update streak and goals
        self._update_workout_streak(request.user)
        self._update_goals(request.user, workout)
        
        return Response({
            'session': LiveWorkoutSessionSerializer(session).data,
            'workout': WorkoutSerializer(workout).data
        })
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel the workout session without saving"""
        session = self.get_object()
        
        session.status = 'cancelled'
        session.ended_at = timezone.now()
        session.save()
        
        return Response(LiveWorkoutSessionSerializer(session).data)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get the current active session for the user"""
        session = LiveWorkoutSession.objects.filter(
            user=request.user,
            status__in=['active', 'paused']
        ).first()
        
        if session:
            return Response(LiveWorkoutSessionSerializer(session).data)
        
        return Response(
            {'message': 'No active session'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    def _update_workout_streak(self, user):
        """Update user's workout streak"""
        streak, created = WorkoutStreak.objects.get_or_create(user=user)
        
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        if streak.last_workout_date == yesterday or streak.last_workout_date is None:
            streak.current_streak += 1
            if streak.current_streak > streak.longest_streak:
                streak.longest_streak = streak.current_streak
        elif streak.last_workout_date != today:
            streak.current_streak = 1
        
        streak.last_workout_date = today
        streak.save()
        
        user.workout_streak = streak.current_streak
        user.last_workout_date = today
        user.save()
    
    def _update_goals(self, user, workout):
        """Update user's active goals"""
        active_goals = WorkoutGoal.objects.filter(
            user=user,
            is_active=True,
            is_completed=False,
            end_date__gte=timezone.now().date()
        )
        
        for goal in active_goals:
            if goal.goal_type == 'weekly_workouts':
                goal.current_value += 1
            elif goal.goal_type == 'weekly_distance' and workout.distance_km:
                goal.current_value += workout.distance_km
            elif goal.goal_type == 'weekly_duration':
                goal.current_value += workout.duration_seconds / 60
            elif goal.goal_type == 'monthly_workouts':
                goal.current_value += 1
            elif goal.goal_type == 'monthly_distance' and workout.distance_km:
                goal.current_value += workout.distance_km
            
            if goal.current_value >= goal.target_value:
                goal.is_completed = True
                goal.completed_at = timezone.now()
            
            goal.save()


class GPXRouteViewSet(viewsets.ModelViewSet):
    """GPX routes management"""
    serializer_class = GPXRouteSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return GPXRoute.objects.filter(
            Q(user=self.request.user) | Q(is_public=True)
        )
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def use(self, request, pk=None):
        """Mark route as used"""
        route = self.get_object()
        route.times_used += 1
        route.save()
        return Response({'message': 'Route usage recorded'})
    
    @action(detail=False, methods=['get'])
    def nearby(self, request):
        """Find routes near a location"""
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        radius = float(request.query_params.get('radius', 10))  # km
        
        if not lat or not lng:
            return Response(
                {'error': 'lat and lng are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        lat = float(lat)
        lng = float(lng)
        
        # Simple bounding box filter (for production, use PostGIS)
        lat_range = radius / 111
        lng_range = radius / (111 * abs(lat))
        
        # This is a simplified query - in production use proper geospatial queries
        routes = self.get_queryset().filter(
            is_public=True
        )[:20]
        
        serializer = self.get_serializer(routes, many=True)
        return Response(serializer.data)
