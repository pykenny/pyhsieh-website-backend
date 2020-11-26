"""
Django settings for blog_backend project.

Generated by 'django-admin startproject' using Django 3.1.3.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""

from os import environ
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured


# Helper Functions
def get_env_value(name):
    """ Wrapper of os.environ access. """
    try:
        return environ[name]
    except KeyError:
        error_msg = "Missing environment variable for settings: '{0:s}'".format(name)
        raise ImproperlyConfigured(error_msg)


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = get_env_value("SECRET_KEY")

DEBUG = bool(environ.get("DEBUG", 0))

ALLOWED_HOSTS = (
    (environ.get("ALLOWED_HOSTS", "").split(",") or [])
    if DEBUG
    else get_env_value("ALLOWED_HOSTS").split(",")
)

# Application definition

INSTALLED_APPS = [
    "django_extensions",
    "safedelete",
    "resource_management.apps.ResourceManagementConfig",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
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

ROOT_URLCONF = "blog_backend.urls"

TEMPLATES = [
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
]

WSGI_APPLICATION = "blog_backend.wsgi.application"


# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": get_env_value("DB_NAME"),
        "USER": get_env_value("DB_USER"),
        "PASSWORD": get_env_value("DB_PASSWORD"),
        "HOST": get_env_value("DB_HOST"),
        "PORT": get_env_value("DB_PORT"),
        "TEST": {
            "NAME": "",
        }
    }
}

if DEBUG:
    DATABASES["default"]["TEST"]["NAME"] = get_env_value("DB_TEST_NAME")


# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# File access settings
OPENED_IMAGE_GROUP = get_env_value("OPENED_IMAGE_GROUP")
PROTECTED_IMAGE_GROUP = get_env_value("PROTECTED_IMAGE_GROUP")

OPENED_IMAGE_DIR = get_env_value("OPENED_IMAGE_DIR")
PROTECTED_IMAGE_DIR = get_env_value("PROTECTED_IMAGE_DIR")

OPENED_IMAGE_GROUP_TEST = None
PROTECTED_IMAGE_GROUP_TEST = None
OPENED_IMAGE_DIR_TEST = None
PROTECTED_IMAGE_DIR_TEST = None

if DEBUG:
    OPENED_IMAGE_GROUP_TEST = get_env_value("OPENED_IMAGE_GROUP_TEST")
    PROTECTED_IMAGE_GROUP_TEST = get_env_value("PROTECTED_IMAGE_GROUP_TEST")
    OPENED_IMAGE_DIR_TEST = get_env_value("OPENED_IMAGE_DIR_TEST")
    PROTECTED_IMAGE_DIR_TEST = get_env_value("PROTECTED_IMAGE_DIR_TEST")
