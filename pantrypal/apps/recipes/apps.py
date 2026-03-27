"""Recipes app configuration."""
from django.apps import AppConfig


class RecipesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pantrypal.apps.recipes'
    label = 'recipes'
    verbose_name = 'Recipes'
