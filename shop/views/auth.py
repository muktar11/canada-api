
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import serializers

from shop.serializers import (
    MyTokenObtainPairSerializer,
    RegisterStaffSerializer,
    ChangePasswordSerializer,
    VerifyEmailSerializer,
)
from shop.models import CustomUser
from django.shortcuts import get_object_or_404


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class TokenRefreshViewCustom(APIView):
    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"detail": "Refresh token is required"}, status=400)

        try:
            refresh = RefreshToken(refresh_token)
            return Response({"access": str(refresh.access_token)})
        except Exception:
            return Response({"detail": "Invalid refresh token"}, status=400)


class RegisterStaffView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterStaffSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)

        return Response({
            "message": "User registered successfully",
            "user": serializer.data,
            "access_token": str(refresh.access_token)
        }, status=201)

'''
class RegisterStaffView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterStaffSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response({
            "message": "Registration successful. Please check your email to verify your account.",
            "user": serializer.data,
        }, status=201)
'''

class VerifyEmailView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data

        refresh = RefreshToken.for_user(user)

        return Response({
            "message": "Email verified successfully",
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user_id": user.id,
            "email": user.email,
            "username": user.username,
        }, status=200)


class GoogleLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        token = request.data.get('token')
        if not token:
            return Response({'error': 'Token is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Verify the token with Google
            response = requests.get('https://www.googleapis.com/oauth2/v3/userinfo', headers={'Authorization': f'Bearer {token}'})
            
            if response.status_code != 200:
                return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
            
            google_data = response.json()
            email = google_data.get('email')
            
            if not email:
                return Response({'error': 'Email not provided by Google'}, status=status.HTTP_400_BAD_REQUEST)

            # Check if user exists
            try:
                user = CustomUser.objects.get(email=email)
                if user.auth_provider != 'google':
                    return Response({'error': 'Account already exists with this email. Please login with password.'}, status=status.HTTP_400_BAD_REQUEST)
            except CustomUser.DoesNotExist:
                # Create new user
                base_username = email.split('@')[0]
                username = base_username
                counter = 1
                while CustomUser.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1

                user = CustomUser.objects.create_user(
                    email=email,
                    username=username,
                    password=CustomUser.objects.make_random_password(),
                    auth_provider='google',
                    is_email_verified=True,
                    is_active=True,
                    first_name=google_data.get('given_name', ''),
                    last_name=google_data.get('family_name', '')
                )

            # Generate tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'message': 'Login successful',
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user_id': user.id,
                'email': user.email,
                'username': user.username,
            })

        except Exception as e:
            return Response({'error': 'Something went wrong'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
