"""Auth app views — signup and login."""
from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User
from .serializers import SignupSerializer, LoginSerializer, UserResponseSerializer, get_tokens_for_user


class SignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if not serializer.is_valid():
            # Flatten validation errors for UI compatibility
            errors = serializer.errors
            first_error = next(iter(errors.values()))[0] if errors else 'Validation error'
            return Response(
                {'success': False, 'error': str(first_error), 'status': 'VALIDATION_ERROR'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = serializer.save()
        tokens = get_tokens_for_user(user)

        return Response({
            'success': True,
            'userID': user.id,
            'token': tokens['access'],
            'refresh': tokens['refresh'],
            'username': user.username,
            'userFirstName': user.user_first_name,
            'userLastName': user.user_last_name,
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'success': False, 'error': 'Username and password are required', 'status': 'VALIDATION_ERROR'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        user = authenticate(request, username=username, password=password)
        if not user:
            return Response(
                {'success': False, 'error': 'Invalid username or password', 'status': 'INVALID_CREDENTIALS'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        tokens = get_tokens_for_user(user)

        return Response({
            'success': True,
            'userID': user.id,
            'token': tokens['access'],
            'refresh': tokens['refresh'],
            'username': user.username,
            'userFirstName': user.user_first_name,
            'userLastName': user.user_last_name,
        })
