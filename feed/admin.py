from django.contrib import admin
from .models import Post, PostLike, PostComment

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['author', 'post_type', 'likes_count', 'comments_count', 'created_at']
    list_filter = ['post_type', 'created_at']
    search_fields = ['author__username', 'content']

@admin.register(PostComment)
class PostCommentAdmin(admin.ModelAdmin):
    list_display = ['author', 'post', 'created_at']
    search_fields = ['author__username', 'content']

admin.site.register(PostLike)
