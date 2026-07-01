# This is a Django application that serves as the backend for the Gheras project. It is responsible for handling API requests, managing user authentication, and processing story generation tasks. The application is configured to use a PostgreSQL database and includes settings for CORS, static files, media files, and email backend. The main entry point of the application is defined in this file, which sets up the Django environment and runs the server when executed.
# import necessary modules and functions from Django and other libraries, including os for environment variable handling, sys for command-line arguments, Path for file path manipulation, django for setting up the Django environment, and settings from django.conf to configure the application settings.
import os
import sys
from pathlib import Path

import django
from django.conf import settings

# The code imports necessary modules and functions from Django and other libraries, including os for environment variable handling, sys for command-line arguments, Path for file path manipulation, and django for setting up the Django environment. It also imports settings from django.conf to configure the application settings.
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from a .env file to access configurations such as the OpenAI API key, debug mode, secret key, allowed hosts, and CORS allowed origins. This allows for flexible configuration of the application without hardcoding sensitive information in the codebase.
DEBUG = os.environ.get("DEBUG", "True").lower() in ("true", "1", "yes")
SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "django-insecure-dev-key-change-in-production",
)

# The ALLOWED_HOSTS variable is set by reading the ALLOWED_HOSTS environment variable, which is expected to be a comma-separated list of allowed hostnames. If the environment variable is not set, it defaults to allowing all hosts by using "*". The code splits the environment variable string by commas and strips any leading or trailing whitespace from each hostname to create a list of allowed hosts for the Django application.
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "*").split(",")

# The CORS_ALLOWED_ORIGINS variable is set by reading the CORS_ALLOWED_ORIGINS environment variable, which is expected to be a comma-separated list of allowed origins for Cross-Origin Resource Sharing (CORS). If the environment variable is not set, it defaults to allowing requests from "http://localhost:5173" and "http://localhost:5174". The code splits the environment variable string by commas and strips any leading or trailing whitespace from each origin to create a list of allowed origins for CORS requests to the Django application.
_cors_origins_env = os.environ.get("CORS_ALLOWED_ORIGINS", "")
if _cors_origins_env:
    CORS_ALLOWED_ORIGINS = [
        origin.strip()
        for origin in _cors_origins_env.split(",")
        if origin.strip()
    ]
else:
    CORS_ALLOWED_ORIGINS = [
        "http://localhost:5173",
        "http://localhost:5174",
    ]

# The code sets up the Django environment by configuring the application settings and calling django.setup(). This allows the application to use Django's features and functionality, such as models, views, and middleware. After setting up the environment, it imports necessary modules for handling WSGI applications and executing management commands. Finally, it defines the main entry point of the application, which runs the server when executed.
settings.configure(
    DEBUG=DEBUG,
    SECRET_KEY=SECRET_KEY,
    ALLOWED_HOSTS=ALLOWED_HOSTS,
    ROOT_URLCONF="api.urls",
    WSGI_APPLICATION=f"{__name__}.application",

  # The INSTALLED_APPS setting defines the list of Django applications that are included in this project. It includes built-in Django apps for admin, authentication, content types, sessions, messages, and static files, as well as third-party apps for REST framework, token authentication, and CORS handling. Additionally, it includes the "api" app, which is likely where the main functionality of the application is implemented.
    INSTALLED_APPS=[
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.messages",
        "django.contrib.staticfiles",
        "rest_framework",
        "rest_framework.authtoken",
        "corsheaders",
        "api",
    ],

    # The MIDDLEWARE setting defines the list of middleware classes that are used by the Django application. Middleware is a way to process requests and responses globally before they reach the view or after the view has processed them. The middleware classes included in this setting handle CORS, security, static file serving, sessions, common HTTP processing, authentication, and messaging. The order of the middleware classes is important, as it determines the sequence in which they are applied to incoming requests and outgoing responses.
    MIDDLEWARE=[
        "corsheaders.middleware.CorsMiddleware",
        "django.middleware.security.SecurityMiddleware",
        "whitenoise.middleware.WhiteNoiseMiddleware",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.middleware.common.CommonMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "django.contrib.messages.middleware.MessageMiddleware",
    ],

    # The DATABASES setting configures the database connection for the Django application. In this case, it is set to use a PostgreSQL database with the specified name, user, password, host, and port. This allows the application to interact with the PostgreSQL database for storing and retrieving data.
    DATABASES={
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": "qura",
            "USER": "qura",
            "PASSWORD": "qura",
            "HOST": "localhost",
            "PORT": "5434",
        }
    },

    # The REST_FRAMEWORK setting configures the Django REST Framework for the application. It specifies the default authentication classes to be used for API requests, which in this case is TokenAuthentication, and the default permission classes, which require that the user is authenticated to access the API endpoints. This ensures that only authenticated users can interact with the API and helps secure the application.
    REST_FRAMEWORK={
        "DEFAULT_AUTHENTICATION_CLASSES": [
            "rest_framework.authentication.TokenAuthentication",
        ],
        "DEFAULT_PERMISSION_CLASSES": [
            "rest_framework.permissions.IsAuthenticated",
        ],
    },

    CORS_ALLOWED_ORIGINS=CORS_ALLOWED_ORIGINS,

    DEFAULT_AUTO_FIELD="django.db.models.BigAutoField",

    MEDIA_URL="/media/",
    MEDIA_ROOT=str(BASE_DIR / "media"),

    STATIC_URL="/static/",
    STATIC_ROOT=str(BASE_DIR / "staticfiles"),

    #   The STORAGES setting configures the storage backends for the Django application. It defines two storage backends: "default" and "staticfiles". The "default" backend uses Django's built-in FileSystemStorage for handling media files, while the "staticfiles" backend uses WhiteNoise's CompressedStaticFilesStorage for serving static files in production (when DEBUG is False) and Django's StaticFilesStorage for development (when DEBUG is True). This configuration allows the application to efficiently serve static files and manage media files based on the environment it is running in.
    STORAGES={
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": (
                "whitenoise.storage.CompressedStaticFilesStorage"
                if not DEBUG
                else "django.contrib.staticfiles.storage.StaticFilesStorage"
            ),
        },
    },

    # The TEMPLATES setting configures the template engine for the Django application. It specifies that the backend to be used is DjangoTemplates, and it includes options for template directories, enabling app directories, and context processors. The context processors are functions that inject additional context into templates, such as debug information, request data, authentication status, and messages. This configuration allows the application to render templates with the necessary context for dynamic content generation.
    TEMPLATES=[
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [],
            "APP_DIRS": True,
            "OPTIONS": {
                "context_processors": [
                    "django.template.context_processors.debug",
                    "django.template.context_processors.request",
                    "django.contrib.auth.context_processors.auth",
                    "django.contrib.messages.context_processors.messages",
                ],
            },
        },
    ],

    # The EMAIL_BACKEND setting configures the email backend for the Django application. It reads the EMAIL_BACKEND environment variable to determine which email backend to use, and if it is not set, it defaults to using Django's console email backend, which outputs emails to the console for development purposes. The other email settings (EMAIL_HOST, EMAIL_PORT, EMAIL_USE_TLS, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, DEFAULT_FROM_EMAIL) are also configured by reading from environment variables, allowing for flexible configuration of the email service used by the application.
    EMAIL_BACKEND=os.environ.get(
        "EMAIL_BACKEND",
        "django.core.mail.backends.console.EmailBackend",
    ),
    EMAIL_HOST=os.environ.get("EMAIL_HOST", "smtp.gmail.com"),
    EMAIL_PORT=int(os.environ.get("EMAIL_PORT", "587")),
    EMAIL_USE_TLS=os.environ.get("EMAIL_USE_TLS", "True").lower() in ("true", "1"),
    EMAIL_HOST_USER=os.environ.get("EMAIL_HOST_USER", ""),
    EMAIL_HOST_PASSWORD=os.environ.get("EMAIL_HOST_PASSWORD", ""),
    DEFAULT_FROM_EMAIL=os.environ.get("DEFAULT_FROM_EMAIL", "noreply@gheras.app"),

    # The security settings (SECURE_BROWSER_XSS_FILTER, SECURE_CONTENT_TYPE_NOSNIFF, SESSION_COOKIE_SECURE, CSRF_COOKIE_SECURE, X_FRAME_OPTIONS) are configured to enhance the security of the application. These settings enable browser security features such as XSS filtering and content type sniffing prevention, and they also ensure that cookies are only sent over secure connections (HTTPS) when the application is not in debug mode. The X_FRAME_OPTIONS setting is set to "DENY" to prevent the application from being embedded in iframes, which can help protect against clickjacking attacks.
    SECURE_BROWSER_XSS_FILTER=not DEBUG,
    SECURE_CONTENT_TYPE_NOSNIFF=not DEBUG,
    SESSION_COOKIE_SECURE=not DEBUG,
    CSRF_COOKIE_SECURE=not DEBUG,
    X_FRAME_OPTIONS="DENY",
)

django.setup()

from django.core.management import execute_from_command_line
from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

# The main entry point of the application is defined in this file, which sets up the Django environment and runs the server when executed. By calling execute_from_command_line with sys.argv, the application can handle various command-line arguments for running the development server, applying migrations, creating superusers, and other management tasks provided by Django's manage.py utility.
if __name__ == "__main__":
    execute_from_command_line(sys.argv)