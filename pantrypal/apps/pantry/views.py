"""Pantry views — CRUD for user pantry items."""
from django.conf import settings
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from pantrypal.apps.products.models import Product
from pantrypal.services.email_service import send_pantry_event
from .models import PantryItem
from .serializers import PantryItemSerializer, PantryItemCreateSerializer, PantryItemUpdateSerializer


class PantryListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        items = (
            PantryItem.objects
            .filter(user=request.user)
            .select_related('product')
            .order_by('-date_purchased')
        )
        serializer = PantryItemSerializer(items, many=True)
        return Response({'success': True, 'pantry_items': serializer.data})

    def post(self, request):
        serializer = PantryItemCreateSerializer(data=request.data)
        if not serializer.is_valid():
            field = next(iter(serializer.errors))
            return Response(
                {'success': False, 'error': f'{field} is required', 'status': 'VALIDATION_ERROR'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        upc = str(data['productUPC'])

        try:
            product = Product.objects.get(product_upc=upc)
        except Product.DoesNotExist:
            return Response(
                {'success': False, 'error': 'Product not found', 'status': 'NOT_FOUND'},
                status=status.HTTP_404_NOT_FOUND,
            )

        item = PantryItem.objects.create(
            user=request.user,
            product=product,
            quantity=data['quantity'],
            quantity_type=data.get('quantityType', 'items'),
            date_purchased=data.get('date_purchased'),
            expiration_date=data.get('expiration_date'),
        )

        # Fire-and-forget event to email worker
        send_pantry_event('pantry.item.added', {
            'user_id': request.user.id,
            'username': request.user.username,
            'email': request.user.email,
            'pantry_id': item.pantry_id,
            'product_name': product.product_name,
            'product_upc': product.product_upc,
            'quantity': float(item.quantity),
            'quantity_type': item.quantity_type,
            'expiration_date': str(item.expiration_date) if item.expiration_date else None,
        })

        out = PantryItemSerializer(item).data
        return Response({
            'success': True,
            'message': 'Product added to pantry successfully',
            'pantryItem': out,
        }, status=status.HTTP_201_CREATED)


class PantryItemDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_item(self, pantry_id, user):
        try:
            return PantryItem.objects.select_related('product').get(
                pantry_id=pantry_id, user=user
            )
        except PantryItem.DoesNotExist:
            return None

    def put(self, request, pantry_id):
        item = self._get_item(pantry_id, request.user)
        if not item:
            return Response(
                {'success': False, 'error': 'Pantry item not found or does not belong to user', 'status': 'NOT_FOUND'},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = PantryItemUpdateSerializer(item, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(
                {'success': False, 'error': str(serializer.errors), 'status': 'VALIDATION_ERROR'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        updated = serializer.save()
        return Response({'success': True, 'pantry_item': PantryItemSerializer(updated).data})

    def delete(self, request, pantry_id):
        item = self._get_item(pantry_id, request.user)
        if not item:
            return Response(
                {'success': False, 'error': 'Pantry item not found or does not belong to user', 'status': 'NOT_FOUND'},
                status=status.HTTP_404_NOT_FOUND,
            )

        product_name = item.product.product_name
        item.delete()

        # Notify email worker
        send_pantry_event('pantry.item.removed', {
            'user_id': request.user.id,
            'username': request.user.username,
            'email': request.user.email,
            'pantry_id': pantry_id,
            'product_name': product_name,
        })

        return Response({'success': True, 'message': 'Item removed from pantry'})


class PantryItemByUPCView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, product_upc):
        try:
            item = PantryItem.objects.select_related('product').get(
                user=request.user, product__product_upc=product_upc
            )
        except PantryItem.DoesNotExist:
            return Response(
                {'success': False, 'error': 'Product not found in user pantry', 'status': 'NOT_FOUND'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({'success': True, 'pantry_item': PantryItemSerializer(item).data})
