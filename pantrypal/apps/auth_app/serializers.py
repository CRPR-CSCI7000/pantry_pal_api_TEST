"""Auth app serializers."""
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])

    userFirstName = serializers.CharField(source='user_first_name', required=True)
    userLastName = serializers.CharField(source='user_last_name', required=True)
    
    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'password',
            'userFirstName',
            'userLastName',
        )

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('A user with this username already exists.')
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            user_first_name=validated_data.get('user_first_name', ''),
            user_last_name=validated_data.get('user_last_name', ''),
        )
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)


class UserResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'user_first_name', 'user_last_name')


def get_tokens_for_user(user):
    """Generate JWT access and refresh tokens for a user."""
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }
