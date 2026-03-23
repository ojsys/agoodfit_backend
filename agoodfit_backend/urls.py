"""
URL configuration for agoodfit_backend project.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.generic import TemplateView
from django.views.static import serve

urlpatterns = [
    path('', TemplateView.as_view(template_name='landing.html'), name='landing'),
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls')),
    path('api/events/', include('events.urls')),
    path('api/workouts/', include('workouts.urls')),
    path('api/matching/', include('matching.urls')),
    path('api/messaging/', include('messaging.urls')),
    path('api/dashboard/', include('dashboard.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('api/feed/', include('feed.urls')),
]

# Media files — always served by Django (static() only works with DEBUG=True,
# so we use the serve view directly to cover production as well).
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]
