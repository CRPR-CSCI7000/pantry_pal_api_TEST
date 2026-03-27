"""Product views — UPC lookup, product CRUD."""
from datetime import datetime

from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from pantrypal.services.ai_service import get_gpt_category, get_days_to_expire, estimate_expiry_date
from pantrypal.services.upc_service import validate_upc, call_upc_api
from .models import Product
from .serializers import ProductSerializer, ProductCreateSerializer


class UPCLookupView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        upc = request.query_params.get('upc')
        if not upc:
            return Response({
                'success': False, 'source': None, 'cached': False, 'items': None,
                'error': 'UPC is required', 'status': 'VALIDATION_ERROR', 'details': None,
            }, status=status.HTTP_400_BAD_REQUEST)

        is_valid, result = validate_upc(upc)
        if not is_valid:
            return Response({
                'success': False, 'source': None, 'cached': False, 'items': None,
                'error': 'Invalid UPC format', 'status': 'VALIDATION_ERROR', 'details': result,
            }, status=status.HTTP_400_BAD_REQUEST)

        upc = result

        # Check database cache
        try:
            product = Product.objects.get(product_upc=upc)
            normalized = {
                'title': product.product_name,
                'brand': product.product_brand,
                'category': product.product_category,
                'description': product.product_description,
                'lowest_recorded_price': float(product.product_lowest_price),
                'highest_recorded_price': float(product.product_highest_price),
                'currency': product.product_currency,
                'images': product.product_images,
                'model': product.product_model,
                'color': product.product_color,
                'size': product.product_size,
                'dimension': product.product_dimension,
                'weight': product.product_weight,
                'upc': product.product_upc,
            }
            normalized['category'] = get_gpt_category(normalized)
            days_to_expire = get_days_to_expire(normalized)
            normalized['expiryDate'] = estimate_expiry_date(days_to_expire)
            normalized['purchaseDate'] = datetime.now().strftime('%Y-%m-%d')

            return Response({
                'success': True, 'source': 'database', 'cached': True,
                'items': [normalized], 'error': None, 'status': None, 'details': None,
            })
        except Product.DoesNotExist:
            pass

        # Call external UPC API
        response = call_upc_api(upc)
        if not response:
            return Response({
                'success': False, 'source': 'api', 'cached': False, 'items': None,
                'error': 'API request failed', 'status': 'API_ERROR',
                'details': 'Failed to connect to UPC API',
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        if response.status_code != 200:
            return Response({
                'success': False, 'source': 'api', 'cached': False, 'items': None,
                'error': 'UPC lookup failed', 'status': 'API_ERROR',
                'details': f'API returned status code: {response.status_code}',
            }, status=response.status_code)

        api_data = response.json()

        if api_data.get('product'):
            gpt_category = get_gpt_category(api_data['product'])
            current_date = datetime.now().strftime('%Y-%m-%d')
            days_to_expire = get_days_to_expire(api_data['product'])
            expiry_date = estimate_expiry_date(days_to_expire)

            specs = api_data['product'].get('specs', [])
            product_data = {
                'upc': api_data.get('code'),
                'title': api_data['product'].get('name'),
                'brand': api_data['product'].get('brand'),
                'category': gpt_category,
                'description': api_data['product'].get('description'),
                'images': [api_data['product'].get('imageUrl')] if api_data['product'].get('imageUrl') else [],
                'model': '',
                'color': next((s[1] for s in specs if s[0] == 'Color'), ''),
                'size': next((s[1] for s in specs if s[0] == 'Size'), ''),
                'dimension': next((s[1] for s in specs if any(d in s[0].lower() for d in ['height', 'width', 'length'])), ''),
                'weight': next((s[1] for s in specs if 'weight' in s[0].lower()), ''),
                'lowest_recorded_price': 0.0,
                'highest_recorded_price': 0.0,
                'currency': 'USD',
                'purchaseDate': current_date,
                'expiryDate': expiry_date,
            }

            # Save to DB
            try:
                Product.objects.update_or_create(
                    product_upc=product_data['upc'],
                    defaults={
                        'product_name': product_data['title'] or '',
                        'product_description': (product_data['description'] or '')[:515],
                        'product_brand': product_data['brand'] or '',
                        'product_category': product_data['category'],
                        'product_lowest_price': product_data['lowest_recorded_price'],
                        'product_highest_price': product_data['highest_recorded_price'],
                        'product_currency': product_data['currency'],
                        'product_images': product_data['images'],
                        'product_model': product_data['model'],
                        'product_color': product_data['color'],
                        'product_size': product_data['size'],
                        'product_dimension': product_data['dimension'],
                        'product_weight': product_data['weight'],
                    }
                )
                cached = True
            except Exception as e:
                cached = False

            return Response({
                'success': True, 'source': 'api', 'cached': cached,
                'items': [product_data], 'error': None, 'status': None, 'details': None,
            })

        return Response({
            'success': False, 'source': 'api', 'cached': False, 'items': None,
            'error': 'Product not found', 'status': 'NOT_FOUND', 'details': None,
        }, status=status.HTTP_404_NOT_FOUND)


class ProductCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ProductCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'success': False, 'error': str(serializer.errors), 'status': 'VALIDATION_ERROR'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        product = serializer.save()
        return Response({'success': True, 'product': ProductSerializer(product).data})


class ProductDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, product_upc):
        try:
            product = Product.objects.get(product_upc=product_upc)
        except Product.DoesNotExist:
            return Response(
                {'success': False, 'error': 'Product not found', 'status': 'NOT_FOUND'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({'success': True, 'product': ProductSerializer(product).data})
