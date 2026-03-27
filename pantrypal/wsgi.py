"""WSGI config for PantryPal."""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pantrypal.settings.base')
application = get_wsgi_application()
