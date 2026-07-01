# This code defines the URL patterns for the API endpoints of a Django application. It includes routes for user authentication (signup, signin, signout, and retrieving user information), as well as routes for managing children, stories, reading logs, behavior tasks, and retrieving various configurations and statistics. The code also sets up a router for the ChildViewSet and StoryViewSet, allowing for easy handling of CRUD operations on these resources. Additionally, it serves media files during development when the DEBUG setting is enabled.
# Import necessary modules and functions from Django and Django REST Framework, including path for defining URL patterns, include for including other URL configurations, and DefaultRouter for creating a router for viewsets. The code also imports views for handling authentication, child and story management, reading logs, behavior tasks, statistics, configuration, genres, behaviors, and art styles.
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Import views for handling authentication, child and story management, reading logs, behavior tasks, statistics, configuration, genres, behaviors, and art styles. These views will be associated with specific URL patterns to handle incoming API requests.
from api.views import (
    signup,
    signin,
    signout,
    me,
    ChildViewSet,
    StoryViewSet,
    create_reading_log,
    create_behavior_task,
    stats,
    config,
    genres_list,
    behaviors_list,
    art_styles_list,
)

# Create a DefaultRouter instance to automatically generate URL patterns for the ChildViewSet and StoryViewSet. This allows for easy handling of CRUD operations on child and story resources without having to manually define each URL pattern for these viewsets.
router = DefaultRouter()
router.register(r"children", ChildViewSet, basename="child")
router.register(r"stories", StoryViewSet, basename="story")

# Define the URL patterns for the API endpoints, including routes for admin, authentication, statistics, configuration, genres, behaviors, art styles, reading logs, behavior tasks, and the child and story viewsets. The urlpatterns list maps URL paths to their corresponding views or viewsets, allowing the application to handle incoming requests appropriately.
urlpatterns = [
    path("admin/", admin.site.urls),

    path("api/auth/signup/", signup),
    path("api/auth/signin/", signin),
    path("api/auth/signout/", signout),
    path("api/auth/me/", me),

    path("api/stats/", stats),
    path("api/config/", config),
    path("api/genres/", genres_list),
    path("api/behaviors/", behaviors_list),
    path("api/art-styles/", art_styles_list),

    path("api/reading-logs/", create_reading_log),
    path("api/tasks/", create_behavior_task),

    path("api/", include(router.urls)),
]

# If the DEBUG setting is enabled, serve media files during development by appending the appropriate URL pattern to the urlpatterns list. This allows for access to media files (such as audio and images) through the specified MEDIA_URL and MEDIA_ROOT settings when running the application in a development environment.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
