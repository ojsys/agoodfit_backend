from django.contrib import admin
from .models import Match, Wave, UserDiscoverySettings, Swipe, MatchSuggestion


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ['user1', 'user2', 'match_type', 'status', 'created_at']
    list_filter = ['match_type', 'status']


@admin.register(Wave)
class WaveAdmin(admin.ModelAdmin):
    list_display = ['sender', 'recipient', 'status', 'created_at']
    list_filter = ['status']


@admin.register(UserDiscoverySettings)
class UserDiscoverySettingsAdmin(admin.ModelAdmin):
    list_display = ['user', 'discoverable', 'max_distance_km', 'created_at']
    list_filter = ['discoverable']


@admin.register(Swipe)
class SwipeAdmin(admin.ModelAdmin):
    list_display = ['swiper', 'swiped', 'swipe_type', 'created_at']
    list_filter = ['swipe_type']


@admin.register(MatchSuggestion)
class MatchSuggestionAdmin(admin.ModelAdmin):
    list_display = ['user', 'suggested_user', 'compatibility_score', 'reason', 'created_at']
    list_filter = ['reason']
