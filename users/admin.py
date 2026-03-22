from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserInterest, UserIntention, UserPhoto, UserPrompt, Follow, Block


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'username', 'user_type', 'primary_goal', 'is_active', 'created_at']
    list_filter = ['user_type', 'primary_goal', 'is_active', 'is_verified']
    search_fields = ['email', 'username', 'bio', 'hometown']
    ordering = ['-created_at']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Profile Info', {
            'fields': ('user_type', 'bio', 'profile_photo', 'hometown', 'latitude', 'longitude')
        }),
        ('Onboarding', {
            'fields': ('primary_goal', 'privacy_setting', 'availability', 'motivation', 'wellness_looks_like')
        }),
        ('Stats', {
            'fields': ('login_streak', 'workout_streak', 'last_login_date', 'last_workout_date')
        }),
    )


@admin.register(UserInterest)
class UserInterestAdmin(admin.ModelAdmin):
    list_display = ['user', 'interest', 'level', 'created_at']
    list_filter = ['interest', 'level']
    search_fields = ['user__email', 'interest']


@admin.register(UserIntention)
class UserIntentionAdmin(admin.ModelAdmin):
    list_display = ['user', 'intention', 'created_at']
    list_filter = ['intention']
    search_fields = ['user__email']


@admin.register(UserPhoto)
class UserPhotoAdmin(admin.ModelAdmin):
    list_display = ['user', 'order', 'is_primary', 'created_at']
    list_filter = ['is_primary']


@admin.register(UserPrompt)
class UserPromptAdmin(admin.ModelAdmin):
    list_display = ['user', 'prompt', 'answer', 'created_at']
    search_fields = ['user__email', 'prompt', 'answer']


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ['follower', 'following', 'created_at']
    search_fields = ['follower__email', 'following__email']


@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = ['blocker', 'blocked', 'reason', 'created_at']
    search_fields = ['blocker__email', 'blocked__email']
