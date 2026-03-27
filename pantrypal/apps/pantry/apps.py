"""Pantry app configuration."""
from django.apps import AppConfig


class PantryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pantrypal.apps.pantry'
    label = 'pantry'
    verbose_name = 'Pantry'
