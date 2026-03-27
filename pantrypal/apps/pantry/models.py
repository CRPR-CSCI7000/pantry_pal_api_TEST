"""Pantry model — maps to the `usersProducts` table."""
from django.conf import settings
from django.db import models

from pantrypal.apps.products.models import Product


class PantryItem(models.Model):
    """
    Represents a product in a user's pantry.
    Maps to the legacy `usersProducts` table.
    """
    pantry_id = models.AutoField(primary_key=True, db_column='pantryid')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        db_column='userid',
        related_name='pantry_items',
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        db_column='productupc',
        to_field='product_upc',
        related_name='pantry_entries',
    )
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    quantity_type = models.CharField(max_length=50, default='items', db_column='quantitytype')
    date_purchased = models.DateField(null=True, blank=True)
    expiration_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'usersproducts'
        verbose_name = 'Pantry Item'
        verbose_name_plural = 'Pantry Items'

    def __str__(self):
        return f"{self.user} - {self.product.product_name} ({self.quantity} {self.quantity_type})"
