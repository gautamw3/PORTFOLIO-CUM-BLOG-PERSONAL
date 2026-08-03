"""
WSGI config for portfolio_cum_blog project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/wsgi/
"""

import os
import pathlib

import dotenv
from django.core.wsgi import get_wsgi_application

CURRENT_DIR = pathlib.Path(__file__).resolve().parent
BASE_DIR = CURRENT_DIR.parent
ENV_FILE_PATH = BASE_DIR / ".env"

if ENV_FILE_PATH.exists():
    dotenv.read_dotenv(str(ENV_FILE_PATH))
else:
    print("Environment file not found. Please make sure it is there | WSGI:error")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "portfolio_cum_blog.settings")

application = get_wsgi_application()
