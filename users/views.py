from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.db.models import Q
from .models import UserInterest, UserIntention, UserPhoto, UserPrompt, Follow, Block
from .serializers import (
    UserSerializer, UserProfileSerializer, UserCreateSerializer,
    UserUpdateSerializer, PublicUserSerializer, FollowSerializer,
    OnboardingSerializer, UserInterestSerializer, UserIntentionSerializer,
    UserPhotoSerializer, UserPromptSerializer, ChangePasswordSerializer
)

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """User management viewset"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        elif self.action == 'me':
            return UserProfileSerializer
        return UserSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'login', 'refresh']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]
    
    @action(detail=False, methods=['get', 'patch'])
    def me(self, request):
        """Get or update current user profile"""
        if request.method == 'PATCH':
            serializer = UserUpdateSerializer(
                request.user, data=request.data, partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            # Return the full profile after saving
            profile = UserProfileSerializer(request.user)
            return Response(profile.data)
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        """User login with email and password"""
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response(
                {'error': 'Please provide both email and password'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not user.check_password(password):
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not user.is_active:
            return Response(
                {'error': 'Account is deactivated'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data
        })
    
    @action(detail=False, methods=['post'])
    def refresh(self, request):
        """Refresh access token"""
        refresh_token = request.data.get('refresh')
        
        if not refresh_token:
            return Response(
                {'error': 'Please provide refresh token'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            refresh = RefreshToken(refresh_token)
            return Response({
                'access': str(refresh.access_token)
            })
        except Exception:
            return Response(
                {'error': 'Invalid refresh token'},
                status=status.HTTP_401_UNAUTHORIZED
            )
    
    @action(detail=False, methods=['post'])
    def onboarding(self, request):
        """Complete user onboarding"""
        serializer = OnboardingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        data = serializer.validated_data
        
        # Update user profile
        if 'primary_goal' in data:
            user.primary_goal = data['primary_goal']
        if 'hometown' in data:
            user.hometown = data['hometown']
        if 'availability' in data:
            user.availability = data['availability']
        if 'motivation' in data:
            user.motivation = data['motivation']
        if 'wellness_looks_like' in data:
            user.wellness_looks_like = data['wellness_looks_like']
        if 'privacy_setting' in data:
            user.privacy_setting = data['privacy_setting']
        if 'latitude' in data:
            user.latitude = data['latitude']
        if 'longitude' in data:
            user.longitude = data['longitude']
        
        user.save()
        
        # Create interests
        if 'interests' in data:
            for interest_data in data['interests']:
                UserInterest.objects.get_or_create(
                    user=user,
                    interest=interest_data['interest'],
                    defaults={'level': interest_data.get('level', 'beginner')}
                )
        
        # Create intentions
        if 'intentions' in data:
            for intention in data['intentions']:
                UserIntention.objects.get_or_create(
                    user=user,
                    intention=intention
                )
        
        return Response({
            'message': 'Onboarding completed successfully',
            'user': UserSerializer(user).data
        })
    
    @action(detail=False, methods=['post'], url_path='change_password')
    def change_password(self, request):
        """Change the authenticated user's password."""
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        if not user.check_password(serializer.validated_data['current_password']):
            return Response(
                {'current_password': ['Incorrect password.']},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(serializer.validated_data['new_password'])
        user.save()

        # Issue fresh tokens so the session stays alive after the password change
        refresh = RefreshToken.for_user(user)
        return Response({
            'message': 'Password changed successfully.',
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        })

    @action(detail=False, methods=['get'])
    def discover(self, request):
        """Discover users based on interests and location"""
        user = request.user
        
        # Get user's interests
        user_interests = user.interests.values_list('interest', flat=True)
        
        # Find users with similar interests, excluding already matched/blocked
        blocked_users = Block.objects.filter(
            Q(blocker=user) | Q(blocked=user)
        ).values_list('blocker_id', 'blocked_id')
        blocked_ids = set()
        for b in blocked_users:
            blocked_ids.update(b)
        
        similar_users = User.objects.filter(
            interests__interest__in=user_interests
        ).exclude(
            id=user.id
        ).exclude(
            id__in=blocked_ids
        ).distinct()
        
        # Filter by privacy settings
        similar_users = similar_users.filter(privacy_setting__in=['public', 'friends'])
        
        # Paginate results
        page = self.paginate_queryset(similar_users)
        if page is not None:
            serializer = PublicUserSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = PublicUserSerializer(similar_users, many=True)
        return Response(serializer.data)


class UserInterestViewSet(viewsets.ModelViewSet):
    """User interests management"""
    serializer_class = UserInterestSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserInterest.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserIntentionViewSet(viewsets.ModelViewSet):
    """User intentions management"""
    serializer_class = UserIntentionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserIntention.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserPhotoViewSet(viewsets.ModelViewSet):
    """User photos management"""
    serializer_class = UserPhotoSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserPhoto.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserPromptViewSet(viewsets.ModelViewSet):
    """User prompts management"""
    serializer_class = UserPromptSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserPrompt.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class FollowViewSet(viewsets.ModelViewSet):
    """Follow relationships management"""
    serializer_class = FollowSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Follow.objects.filter(follower=self.request.user)
    
    def create(self, request):
        following_id = request.data.get('following_id')
        
        if not following_id:
            return Response(
                {'error': 'following_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            following_user = User.objects.get(id=following_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if following_user == request.user:
            return Response(
                {'error': 'Cannot follow yourself'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        follow, created = Follow.objects.get_or_create(
            follower=request.user,
            following=following_user
        )
        
        if not created:
            return Response(
                {'error': 'Already following this user'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(follow)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def unfollow(self, request):
        following_id = request.data.get('following_id')
        
        if not following_id:
            return Response(
                {'error': 'following_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        deleted, _ = Follow.objects.filter(
            follower=request.user,
            following_id=following_id
        ).delete()
        
        if deleted:
            return Response({'message': 'Unfollowed successfully'})
        
        return Response(
            {'error': 'Not following this user'},
            status=status.HTTP_400_BAD_REQUEST
        )
