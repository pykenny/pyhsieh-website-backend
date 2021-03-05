"""
WSGI config for blog_backend project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/howto/deployment/wsgi/
"""

import os
from pathlib import Path

from django.core.wsgi import get_wsgi_application

import dotenv

dotenv.read_dotenv(
    os.environ["DOTENV_PATH"]
    if os.environ.get("DOTENV_PATH", None)
    else Path(__file__).resolve().parent.parent / ".env"
)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "blog_backend.settings")

application = get_wsgi_application()
