from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from django.db.models import Q, F
from .models import Post, PostLike, PostComment, CommentLike
from .serializers import PostSerializer, PostCreateSerializer, PostCommentSerializer
from users.models import Follow


class PostViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PostSerializer

    def get_queryset(self):
        # like / comments / retrieve need access to any post
        if self.action in ['like', 'comments', 'retrieve']:
            return Post.objects.all().select_related('author')
        return Post.objects.filter(author=self.request.user).select_related('author')

    def get_serializer_class(self):
        if self.action == 'create':
            return PostCreateSerializer
        return PostSerializer

    def create(self, request):
        serializer = PostCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        post = serializer.save(author=request.user)
        return Response(
            PostSerializer(post, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )

    def destroy(self, request, *args, **kwargs):
        post = self.get_object()
        if post.author != request.user:
            return Response({'error': 'Not authorised.'}, status=status.HTTP_403_FORBIDDEN)
        post.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def feed(self, request):
        """Posts from people the user follows plus their own, newest first."""
        following_ids = Follow.objects.filter(
            follower=request.user
        ).values_list('following_id', flat=True)

        queryset = (
            Post.objects
            .filter(Q(author__in=following_ids) | Q(author=request.user))
            .select_related('author')
            .prefetch_related('comments', 'likes')
            .order_by('-created_at')
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = PostSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = PostSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """Toggle like on a post."""
        post = self.get_object()
        like, created = PostLike.objects.get_or_create(user=request.user, post=post)
        if created:
            Post.objects.filter(pk=post.pk).update(likes_count=F('likes_count') + 1)
            post.refresh_from_db(fields=['likes_count'])
            return Response({'liked': True, 'likes_count': post.likes_count})
        like.delete()
        Post.objects.filter(pk=post.pk).update(likes_count=F('likes_count') - 1)
        post.refresh_from_db(fields=['likes_count'])
        return Response({'liked': False, 'likes_count': post.likes_count})

    @action(detail=True, methods=['get', 'post'])
    def comments(self, request, pk=None):
        """List top-level comments or add a new comment."""
        post = self.get_object()
        if request.method == 'GET':
            comments = (
                post.comments
                .filter(parent=None)
                .select_related('author')
                .prefetch_related('replies')
            )
            serializer = PostCommentSerializer(comments, many=True, context={'request': request})
            return Response(serializer.data)

        content = request.data.get('content', '').strip()
        if not content:
            return Response({'error': 'Comment cannot be empty.'}, status=status.HTTP_400_BAD_REQUEST)

        comment = PostComment.objects.create(author=request.user, post=post, content=content)
        Post.objects.filter(pk=post.pk).update(comments_count=F('comments_count') + 1)
        return Response(
            PostCommentSerializer(comment, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class PostCommentViewSet(viewsets.GenericViewSet):
    """Handles comment replies and comment likes."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PostCommentSerializer

    def get_queryset(self):
        return PostComment.objects.all().select_related('author')

    def destroy(self, request, *args, **kwargs):
        comment = get_object_or_404(PostComment, pk=kwargs['pk'], author=request.user)
        post_id = comment.post_id
        comment.delete()
        Post.objects.filter(pk=post_id).update(comments_count=F('comments_count') - 1)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get', 'post'])
    def replies(self, request, pk=None):
        """List or create replies to a comment."""
        comment = get_object_or_404(PostComment, pk=pk)
        if request.method == 'GET':
            replies = comment.replies.select_related('author').all()
            serializer = PostCommentSerializer(replies, many=True, context={'request': request})
            return Response(serializer.data)

        content = request.data.get('content', '').strip()
        if not content:
            return Response({'error': 'Reply cannot be empty.'}, status=status.HTTP_400_BAD_REQUEST)

        reply = PostComment.objects.create(
            author=request.user,
            post=comment.post,
            content=content,
            parent=comment,
        )
        Post.objects.filter(pk=comment.post_id).update(comments_count=F('comments_count') + 1)
        return Response(
            PostCommentSerializer(reply, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """Toggle like on a comment."""
        comment = get_object_or_404(PostComment, pk=pk)
        like, created = CommentLike.objects.get_or_create(user=request.user, comment=comment)
        if created:
            PostComment.objects.filter(pk=comment.pk).update(likes_count=F('likes_count') + 1)
            comment.refresh_from_db(fields=['likes_count'])
            return Response({'liked': True, 'likes_count': comment.likes_count})
        like.delete()
        PostComment.objects.filter(pk=comment.pk).update(likes_count=F('likes_count') - 1)
        comment.refresh_from_db(fields=['likes_count'])
        return Response({'liked': False, 'likes_count': comment.likes_count})
