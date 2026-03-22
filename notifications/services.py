import requests
import json
from django.conf import settings
from django.utils import timezone


class FirebaseNotificationService:
    """Service for sending push notifications via Firebase Cloud Messaging"""
    
    FCM_API_URL = "https://fcm.googleapis.com/fcm/send"
    
    def __init__(self):
        self.server_key = getattr(settings, 'FCM_SERVER_KEY', None)
    
    def send_to_token(self, token, title, body, data=None, notification_type=None):
        """Send notification to a single device token"""
        if not self.server_key:
            print("FCM_SERVER_KEY not configured")
            return False
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'key={self.server_key}'
        }
        
        payload = {
            'to': token,
            'notification': {
                'title': title,
                'body': body,
                'sound': 'default',
                'badge': 1,
            },
            'data': data or {},
            'priority': 'high'
        }
        
        try:
            response = requests.post(
                self.FCM_API_URL,
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success', 0) > 0:
                    return True
                else:
                    print(f"FCM send failed: {result}")
                    return False
            else:
                print(f"FCM API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"Error sending FCM notification: {e}")
            return False
    
    def send_to_tokens(self, tokens, title, body, data=None):
        """Send notification to multiple device tokens"""
        if not self.server_key:
            print("FCM_SERVER_KEY not configured")
            return []
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'key={self.server_key}'
        }
        
        payload = {
            'registration_ids': tokens,
            'notification': {
                'title': title,
                'body': body,
                'sound': 'default',
                'badge': 1,
            },
            'data': data or {},
            'priority': 'high'
        }
        
        try:
            response = requests.post(
                self.FCM_API_URL,
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('results', [])
            else:
                print(f"FCM API error: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            print(f"Error sending FCM notification: {e}")
            return []
    
    def send_to_topic(self, topic, title, body, data=None):
        """Send notification to a topic"""
        if not self.server_key:
            print("FCM_SERVER_KEY not configured")
            return False
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'key={self.server_key}'
        }
        
        payload = {
            'to': f'/topics/{topic}',
            'notification': {
                'title': title,
                'body': body,
                'sound': 'default',
                'badge': 1,
            },
            'data': data or {},
            'priority': 'high'
        }
        
        try:
            response = requests.post(
                self.FCM_API_URL,
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('message_id') is not None
            else:
                print(f"FCM API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"Error sending FCM notification: {e}")
            return False


class NotificationSender:
    """High-level notification sender that handles user preferences and logging"""
    
    def __init__(self):
        self.fcm_service = FirebaseNotificationService()
    
    def send_to_user(self, user, title, body, data=None, notification_type='general'):
        """Send notification to a user respecting their preferences"""
        from .models import DeviceToken, PushNotificationLog, NotificationPreference
        
        # Check user preferences
        try:
            prefs = user.notification_preferences
            if not prefs.push_enabled:
                return False
            
            # Check notification type preference
            if notification_type == 'workout' and not prefs.push_workout_reminders:
                return False
            if notification_type == 'event' and not prefs.push_event_reminders:
                return False
            if notification_type == 'match' and not prefs.push_new_matches:
                return False
            if notification_type == 'message' and not prefs.push_new_messages:
                return False
            if notification_type == 'social' and not prefs.push_social_activity:
                return False
            
            # Check quiet hours
            if prefs.quiet_hours_enabled and prefs.quiet_hours_start and prefs.quiet_hours_end:
                from datetime import datetime
                now = timezone.now().time()
                if prefs.quiet_hours_start <= now <= prefs.quiet_hours_end:
                    return False
                    
        except NotificationPreference.DoesNotExist:
            pass  # Use default preferences
        
        # Get active device tokens
        tokens = DeviceToken.objects.filter(
            user=user,
            is_active=True
        ).values_list('token', flat=True)
        
        if not tokens:
            return False
        
        # Create notification log
        log = PushNotificationLog.objects.create(
            user=user,
            title=title,
            body=body,
            data=data or {},
            notification_type=notification_type,
            status='pending'
        )
        
        # Send notification
        if len(tokens) == 1:
            success = self.fcm_service.send_to_token(
                tokens[0], title, body, data, notification_type
            )
        else:
            results = self.fcm_service.send_to_tokens(
                list(tokens), title, body, data
            )
            success = any(r.get('message_id') for r in results if isinstance(r, dict))
        
        # Update log
        log.status = 'sent' if success else 'failed'
        log.sent_at = timezone.now()
        log.save()
        
        return success
    
    def send_workout_reminder(self, user, workout_title):
        """Send workout reminder notification"""
        return self.send_to_user(
            user=user,
            title="Time to Move! 💪",
            body=f"Don't forget your {workout_title} today!",
            data={'type': 'workout_reminder'},
            notification_type='workout'
        )
    
    def send_event_reminder(self, user, event_title, event_time):
        """Send event reminder notification"""
        return self.send_to_user(
            user=user,
            title="Event Starting Soon! 📅",
            body=f"{event_title} starts at {event_time}",
            data={'type': 'event_reminder'},
            notification_type='event'
        )
    
    def send_new_match(self, user, match_name):
        """Send new match notification"""
        return self.send_to_user(
            user=user,
            title="It's a Match! 🎉",
            body=f"You and {match_name} have matched!",
            data={'type': 'new_match'},
            notification_type='match'
        )
    
    def send_new_message(self, user, sender_name, message_preview):
        """Send new message notification"""
        return self.send_to_user(
            user=user,
            title=f"New message from {sender_name}",
            body=message_preview[:100],
            data={'type': 'new_message'},
            notification_type='message'
        )
    
    def send_wave_received(self, user, sender_name):
        """Send wave received notification"""
        return self.send_to_user(
            user=user,
            title="Someone Waved at You! 👋",
            body=f"{sender_name} sent you a wave",
            data={'type': 'wave_received'},
            notification_type='social'
        )
    
    def send_achievement_unlocked(self, user, achievement_name):
        """Send achievement unlocked notification"""
        return self.send_to_user(
            user=user,
            title="Achievement Unlocked! 🏆",
            body=f"You earned: {achievement_name}",
            data={'type': 'achievement'},
            notification_type='social'
        )


# Global notification sender instance
notification_sender = NotificationSender()
