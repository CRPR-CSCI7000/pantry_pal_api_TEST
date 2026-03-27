"""Product serializers."""
from rest_framework import serializers
from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    # Expose fields with camelCase names matching the frontend contract
    productUPC = serializers.CharField(source='product_upc')
    productName = serializers.CharField(source='product_name')
    productDescription = serializers.CharField(source='product_description')
    productBrand = serializers.CharField(source='product_brand')
    productCategory = serializers.CharField(source='product_category')
    productLowestPrice = serializers.DecimalField(source='product_lowest_price', max_digits=10, decimal_places=2)
    productHighestPrice = serializers.DecimalField(source='product_highest_price', max_digits=10, decimal_places=2)
    productCurrency = serializers.CharField(source='product_currency')
    productImages = serializers.ListField(source='product_images', child=serializers.CharField())
    productModel = serializers.CharField(source='product_model')
    productColor = serializers.CharField(source='product_color')
    productSize = serializers.CharField(source='product_size')
    productDimension = serializers.CharField(source='product_dimension')
    productWeight = serializers.CharField(source='product_weight')

    class Meta:
        model = Product
        fields = [
            'productUPC', 'productName', 'productDescription', 'productBrand',
            'productCategory', 'productLowestPrice', 'productHighestPrice',
            'productCurrency', 'productImages', 'productModel', 'productColor',
            'productSize', 'productDimension', 'productWeight',
        ]


class ProductCreateSerializer(serializers.ModelSerializer):
    productUPC = serializers.CharField(source='product_upc')
    productName = serializers.CharField(source='product_name', required=True)
    productBrand = serializers.CharField(source='product_brand', required=False, allow_blank=True, default='')
    productCategory = serializers.CharField(source='product_category', required=False, allow_blank=True, default='Other')
    productImages = serializers.ListField(
        source='product_images', child=serializers.CharField(), required=False, default=list
    )

    class Meta:
        model = Product
        fields = ['productUPC', 'productName', 'productBrand', 'productCategory', 'productImages']

    def create(self, validated_data):
        return Product.objects.update_or_create(
            product_upc=validated_data['product_upc'],
            defaults=validated_data,
        )[0]
