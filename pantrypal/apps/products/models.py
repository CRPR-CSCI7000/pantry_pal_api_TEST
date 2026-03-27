"""Product model — maps to the `products` table."""
from django.contrib.postgres.fields import ArrayField
from django.db import models


class Product(models.Model):
    """
    Represents a food product identified by UPC barcode.
    Matches the legacy schema from the Flask app.
    """
    product_upc = models.CharField(max_length=20, unique=True, db_column='productupc')
    product_name = models.CharField(max_length=500, blank=True, default='', db_column='productname')
    product_description = models.TextField(blank=True, default='', db_column='productdescription')
    product_brand = models.CharField(max_length=255, blank=True, default='', db_column='productbrand')
    product_category = models.CharField(max_length=100, blank=True, default='Other', db_column='productcategory')
    product_lowest_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, db_column='productlowestprice')
    product_highest_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, db_column='producthighestprice')
    product_currency = models.CharField(max_length=10, default='USD', db_column='productcurrency')
    product_images = ArrayField(
        models.TextField(), blank=True, default=list, db_column='productimages'
    )
    product_model = models.CharField(max_length=255, blank=True, default='', db_column='productmodel')
    product_color = models.CharField(max_length=100, blank=True, default='', db_column='productcolor')
    product_size = models.CharField(max_length=100, blank=True, default='', db_column='productsize')
    product_dimension = models.CharField(max_length=255, blank=True, default='', db_column='productdimension')
    product_weight = models.CharField(max_length=100, blank=True, default='', db_column='productweight')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'products'
        verbose_name = 'Product'
        verbose_name_plural = 'Products'

    def __str__(self):
        return f"{self.product_name} ({self.product_upc})"
