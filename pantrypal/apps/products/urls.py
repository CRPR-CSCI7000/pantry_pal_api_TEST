"""Product URL patterns."""
from django.urls import path
from .views import UPCLookupView, ProductCreateView, ProductDetailView

urlpatterns = [
    path('lookup-upc', UPCLookupView.as_view(), name='lookup-upc'),
    path('products', ProductCreateView.as_view(), name='product-create'),
    path('products/<str:product_upc>', ProductDetailView.as_view(), name='product-detail'),
]
