"""Recipe URL patterns."""
from django.urls import path
from .views import GetRecipesView, CookRecipeView

urlpatterns = [
    path('get-recipes', GetRecipesView.as_view(), name='get-recipes'),
    path('cook-recipe', CookRecipeView.as_view(), name='cook-recipe'),
]
