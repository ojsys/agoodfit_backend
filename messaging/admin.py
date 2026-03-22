from django.contrib import admin
from .models import (
    Conversation, Message, MessageReadStatus,
    ConversationParticipant, IcebreakerPrompt, Report
)


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'conversation_type', 'title', 'last_message_at', 'created_at']
    list_filter = ['conversation_type', 'is_group']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['conversation', 'sender', 'message_type', 'content', 'created_at']
    list_filter = ['message_type']


@admin.register(MessageReadStatus)
class MessageReadStatusAdmin(admin.ModelAdmin):
    list_display = ['message', 'user', 'is_read', 'read_at']
    list_filter = ['is_read']


@admin.register(ConversationParticipant)
class ConversationParticipantAdmin(admin.ModelAdmin):
    list_display = ['conversation', 'user', 'role', 'is_muted', 'joined_at']
    list_filter = ['role', 'is_muted']


@admin.register(IcebreakerPrompt)
class IcebreakerPromptAdmin(admin.ModelAdmin):
    list_display = ['prompt', 'category', 'usage_count', 'is_active']
    list_filter = ['category', 'is_active']


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['reporter', 'reported_user', 'report_type', 'status', 'created_at']
    list_filter = ['report_type', 'status']
