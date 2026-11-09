import os
from pathlib import Path

from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DEBUG = os.getenv("DJANGO_DEBUG", "False").lower() == "true"
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
if not DEBUG and not SECRET_KEY:
    raise ImproperlyConfigured("Set DJANGO_SECRET_KEY to a private random value before production startup.")
SECRET_KEY = SECRET_KEY or "unsafe-development-key-change-before-use"

render_hostname = os.getenv("RENDER_EXTERNAL_HOSTNAME")
configured_hosts = os.getenv("DJANGO_ALLOWED_HOSTS") or render_hostname
if not DEBUG and not configured_hosts:
    raise ImproperlyConfigured("Set DJANGO_ALLOWED_HOSTS to the public hostname before production startup.")
ALLOWED_HOSTS = [host.strip() for host in (configured_hosts or "localhost,127.0.0.1").split(",") if host.strip()]
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if origin.strip()]
if render_hostname:
    CSRF_TRUSTED_ORIGINS.append(f"https://{render_hostname}")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "health.apps.HealthConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
if not DEBUG:
    MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

ROOT_URLCONF = "pcos_insight.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]
WSGI_APPLICATION = "pcos_insight.wsgi.application"

database_url = os.getenv("DATABASE_URL")
if database_url:
    import dj_database_url
    DATABASES = {"default": dj_database_url.parse(database_url, conn_max_age=600)}
elif os.getenv("DB_ENGINE", "mysql").lower() == "sqlite":
    sqlite_path = Path(os.getenv("SQLITE_DB_PATH", str(BASE_DIR / "db.sqlite3")))
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": sqlite_path}}
else:
    DATABASES = {"default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.getenv("DB_NAME", "pcos_insight"),
        "USER": os.getenv("DB_USER", "pcos_user"),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", "127.0.0.1"),
        "PORT": os.getenv("DB_PORT", "3306"),
        "OPTIONS": {"charset": "utf8mb4"},
    }}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
# Private uploads are deliberately not mapped to a public MEDIA_URL. Serve them only
# through the authenticated, owner-scoped image view in health.views.
MEDIA_ROOT = Path(os.getenv("PRIVATE_MEDIA_ROOT", str(BASE_DIR / "private_media")))
if not DEBUG and not os.getenv("PRIVATE_MEDIA_ROOT"):
    raise ImproperlyConfigured("Set PRIVATE_MEDIA_ROOT to a persistent private volume before production startup.")
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = "home"

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
if not DEBUG:
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
    }
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    if render_hostname or os.getenv("DJANGO_TRUST_PROXY_SSL", "False").lower() == "true":
        SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
