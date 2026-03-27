"""PantryPal URL Configuration."""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('pantrypal.apps.auth_app.urls')),
    path('api/', include('pantrypal.apps.products.urls')),
    path('api/', include('pantrypal.apps.pantry.urls')),
    path('api/', include('pantrypal.apps.recipes.urls')),
]
