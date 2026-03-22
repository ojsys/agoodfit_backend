from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import Post, PostLike, PostComment
from .serializers import PostSerializer, PostCreateSerializer, PostCommentSerializer
from users.models import Follow


class PostViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PostSerializer

    def get_queryset(self):
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
        """Posts from people the user follows, plus their own, newest first."""
        following_ids = Follow.objects.filter(
            follower=request.user
        ).values_list('following_id', flat=True)

        queryset = Post.objects.filter(
            Q(author__in=following_ids) | Q(author=request.user)
        ).select_related('author').prefetch_related('comments', 'likes').order_by('-created_at')

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
            post.likes_count += 1
            post.save(update_fields=['likes_count'])
            return Response({'liked': True, 'likes_count': post.likes_count})
        else:
            like.delete()
            post.likes_count = max(0, post.likes_count - 1)
            post.save(update_fields=['likes_count'])
            return Response({'liked': False, 'likes_count': post.likes_count})

    @action(detail=True, methods=['get', 'post'])
    def comments(self, request, pk=None):
        """List or add comments on a post."""
        post = self.get_object()
        if request.method == 'GET':
            comments = post.comments.select_related('author').all()
            serializer = PostCommentSerializer(comments, many=True, context={'request': request})
            return Response(serializer.data)

        content = request.data.get('content', '').strip()
        if not content:
            return Response({'error': 'Comment cannot be empty.'}, status=status.HTTP_400_BAD_REQUEST)

        comment = PostComment.objects.create(
            author=request.user, post=post, content=content
        )
        post.comments_count += 1
        post.save(update_fields=['comments_count'])
        return Response(
            PostCommentSerializer(comment, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class PostCommentViewSet(viewsets.GenericViewSet):
    """Allows deleting a comment by its own author."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PostCommentSerializer

    def get_queryset(self):
        return PostComment.objects.filter(author=self.request.user)

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        post = comment.post
        comment.delete()
        post.comments_count = max(0, post.comments_count - 1)
        post.save(update_fields=['comments_count'])
        return Response(status=status.HTTP_204_NO_CONTENT)
