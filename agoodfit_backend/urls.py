"""
URL configuration for agoodfit_backend project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls')),
    path('api/events/', include('events.urls')),
    path('api/workouts/', include('workouts.urls')),
    path('api/matching/', include('matching.urls')),
    path('api/messaging/', include('messaging.urls')),
    path('api/dashboard/', include('dashboard.urls')),
    path('api/notifications/', include('notifications.urls')),
]

# Media files — served by Django in both dev and production
# (WhiteNoise only handles static/, not media/)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
