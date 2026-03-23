from django.contrib import admin
from .models import Post, PostLike, PostComment, CommentLike


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['author', 'post_type', 'likes_count', 'comments_count', 'created_at']
    list_filter = ['post_type', 'created_at']
    search_fields = ['author__username', 'content']


@admin.register(PostComment)
class PostCommentAdmin(admin.ModelAdmin):
    list_display = ['author', 'post', 'parent', 'likes_count', 'created_at']
    search_fields = ['author__username', 'content']
    list_filter = ['created_at']


admin.site.register(PostLike)
admin.site.register(CommentLike)
