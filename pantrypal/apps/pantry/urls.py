"""Pantry URL patterns."""
from django.urls import path
from .views import PantryListCreateView, PantryItemDetailView, PantryItemByUPCView

urlpatterns = [
    path('pantry', PantryListCreateView.as_view(), name='pantry-list-create'),
    path('pantry/<int:pantry_id>', PantryItemDetailView.as_view(), name='pantry-item-detail'),
    path('pantry/product/<str:product_upc>', PantryItemByUPCView.as_view(), name='pantry-item-by-upc'),
]
