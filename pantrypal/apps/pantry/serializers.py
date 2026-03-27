"""Pantry serializers."""
from rest_framework import serializers
from .models import PantryItem


class PantryItemSerializer(serializers.ModelSerializer):
    pantryID = serializers.IntegerField(source='pantry_id', read_only=True)
    userID = serializers.IntegerField(source='user_id', read_only=True)
    productUPC = serializers.CharField(source='product.product_upc', read_only=True)
    productName = serializers.CharField(source='product.product_name', read_only=True)
    productBrand = serializers.CharField(source='product.product_brand', read_only=True)
    productCategory = serializers.CharField(source='product.product_category', read_only=True)
    productImages = serializers.ListField(source='product.product_images', read_only=True)
    quantityType = serializers.CharField(source='quantity_type')
    date_purchased = serializers.DateField(allow_null=True, required=False)
    expiration_date = serializers.DateField(allow_null=True, required=False)

    class Meta:
        model = PantryItem
        fields = [
            'pantryID', 'userID', 'productUPC', 'quantity', 'quantityType',
            'date_purchased', 'expiration_date',
            'productName', 'productBrand', 'productCategory', 'productImages',
        ]


class PantryItemCreateSerializer(serializers.Serializer):
    productUPC = serializers.CharField()
    quantity = serializers.DecimalField(max_digits=10, decimal_places=2)
    quantityType = serializers.CharField(default='items')
    date_purchased = serializers.DateField(allow_null=True, required=False)
    expiration_date = serializers.DateField(allow_null=True, required=False)


class PantryItemUpdateSerializer(serializers.ModelSerializer):
    quantityType = serializers.CharField(source='quantity_type', required=False)

    class Meta:
        model = PantryItem
        fields = ['quantity', 'quantityType', 'expiration_date', 'date_purchased']
        extra_kwargs = {f: {'required': False} for f in fields}
