from django.contrib import admin
from .models import Event, RSVP, EventReview, EventInvitation, SavedEvent


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'host', 'event_type', 'start_date', 'status', 'attendee_count']
    list_filter = ['event_type', 'vibe', 'status', 'price_type']
    search_fields = ['title', 'description', 'location_name']
    date_hierarchy = 'start_date'


@admin.register(RSVP)
class RSVPAdmin(admin.ModelAdmin):
    list_display = ['event', 'user', 'status', 'checked_in', 'created_at']
    list_filter = ['status', 'checked_in']


@admin.register(EventReview)
class EventReviewAdmin(admin.ModelAdmin):
    list_display = ['event', 'user', 'rating', 'created_at']
    list_filter = ['rating']


@admin.register(EventInvitation)
class EventInvitationAdmin(admin.ModelAdmin):
    list_display = ['event', 'sender', 'recipient', 'accepted', 'created_at']
    list_filter = ['accepted']


@admin.register(SavedEvent)
class SavedEventAdmin(admin.ModelAdmin):
    list_display = ['user', 'event', 'created_at']
