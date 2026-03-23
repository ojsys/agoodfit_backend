from rest_framework import serializers
from .models import Post, PostLike, PostComment, CommentLike


class PostCommentSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source='author.username', read_only=True)
    author_display_name = serializers.SerializerMethodField()
    author_photo = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    replies_count = serializers.SerializerMethodField()

    class Meta:
        model = PostComment
        fields = [
            'id', 'author_username', 'author_display_name', 'author_photo',
            'content', 'parent', 'likes_count', 'is_liked', 'replies_count',
            'created_at',
        ]
        read_only_fields = ['id', 'likes_count', 'created_at']

    def get_author_display_name(self, obj):
        fn = (obj.author.first_name or '').strip()
        ln = (obj.author.last_name or '').strip()
        return f'{fn} {ln}'.strip() or obj.author.username

    def get_author_photo(self, obj):
        request = self.context.get('request')
        if obj.author.profile_photo and request:
            return request.build_absolute_uri(obj.author.profile_photo.url)
        return None

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return CommentLike.objects.filter(user=request.user, comment=obj).exists()
        return False

    def get_replies_count(self, obj):
        return obj.replies.count()


class PostSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source='author.username', read_only=True)
    author_display_name = serializers.SerializerMethodField()
    author_photo = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    recent_comments = serializers.SerializerMethodField()
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'author_username', 'author_display_name', 'author_photo',
            'content', 'post_type', 'photo_url',
            'likes_count', 'comments_count',
            'is_liked', 'recent_comments', 'created_at',
        ]
        read_only_fields = ['id', 'likes_count', 'comments_count', 'created_at']

    def get_author_display_name(self, obj):
        fn = (obj.author.first_name or '').strip()
        ln = (obj.author.last_name or '').strip()
        return f'{fn} {ln}'.strip() or obj.author.username

    def get_author_photo(self, obj):
        request = self.context.get('request')
        if obj.author.profile_photo and request:
            return request.build_absolute_uri(obj.author.profile_photo.url)
        return None

    def get_photo_url(self, obj):
        request = self.context.get('request')
        if obj.photo and request:
            return request.build_absolute_uri(obj.photo.url)
        return None

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return PostLike.objects.filter(user=request.user, post=obj).exists()
        return False

    def get_recent_comments(self, obj):
        # Only top-level comments for post preview
        comments = obj.comments.filter(parent=None).order_by('created_at')[:2]
        return PostCommentSerializer(comments, many=True, context=self.context).data


class PostCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['content', 'post_type', 'photo']
