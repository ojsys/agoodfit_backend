from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import DeviceToken, PushNotificationLog, NotificationPreference
from .serializers import (
    DeviceTokenSerializer, PushNotificationLogSerializer, 
    NotificationPreferenceSerializer
)
from .services import notification_sender


class DeviceTokenViewSet(viewsets.ModelViewSet):
    """Device token management for push notifications"""
    serializer_class = DeviceTokenSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return DeviceToken.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        # Deactivate any existing tokens for this device
        platform = self.request.data.get('platform')
        if platform:
            DeviceToken.objects.filter(
                user=self.request.user,
                platform=platform
            ).update(is_active=False)
        
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def register(self, request):
        """Register a new device token"""
        token = request.data.get('token')
        platform = request.data.get('platform')
        device_name = request.data.get('device_name', '')
        
        if not token or not platform:
            return Response(
                {'error': 'token and platform are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Deactivate existing tokens for this platform
        DeviceToken.objects.filter(
            user=request.user,
            platform=platform
        ).update(is_active=False)
        
        # Create or update token
        device_token, created = DeviceToken.objects.update_or_create(
            user=request.user,
            token=token,
            defaults={
                'platform': platform,
                'device_name': device_name,
                'is_active': True
            }
        )
        
        return Response(
            DeviceTokenSerializer(device_token).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['post'])
    def unregister(self, request):
        """Unregister a device token"""
        token = request.data.get('token')
        
        if not token:
            return Response(
                {'error': 'token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        DeviceToken.objects.filter(
            user=request.user,
            token=token
        ).update(is_active=False)
        
        return Response({'message': 'Token unregistered'})


class PushNotificationLogViewSet(viewsets.ReadOnlyModelViewSet):
    """View notification history"""
    serializer_class = PushNotificationLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return PushNotificationLog.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Get unread notifications (pending status)"""
        notifications = self.get_queryset().filter(status='pending')[:20]
        serializer = self.get_serializer(notifications, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        self.get_queryset().filter(status='pending').update(status='delivered')
        return Response({'message': 'All notifications marked as read'})


class NotificationPreferenceViewSet(viewsets.ModelViewSet):
    """Manage notification preferences"""
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return NotificationPreference.objects.filter(user=self.request.user)
    
    def get_object(self):
        prefs, created = NotificationPreference.objects.get_or_create(
            user=self.request.user
        )
        return prefs
    
    def list(self, request):
        """Get current user's notification preferences"""
        prefs = self.get_object()
        serializer = self.get_serializer(prefs)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def test_notification(self, request):
        """Send a test notification to the user"""
        success = notification_sender.send_to_user(
            user=request.user,
            title="Test Notification 🔔",
            body="This is a test notification from A Good Fit!",
            data={'type': 'test'},
            notification_type='general'
        )
        
        if success:
            return Response({'message': 'Test notification sent'})
        else:
            return Response(
                {'error': 'Failed to send notification. Make sure you have registered a device token.'},
                status=status.HTTP_400_BAD_REQUEST
            )
