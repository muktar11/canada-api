

from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from rest_framework import generics
from .models import Category, Product, Testimonial
from .serializers import CategorySerializer, ProductSerializer, TestimonialSerializer


from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Order, OrderItem, Product, Payment, Wishlist, RecentlyViewed
from .serializers import WishlistSerializer, RecentlyViewedSerializer



from django.shortcuts import render
from django.http import JsonResponse
from .models import (
    CustomUser
)
from .serializers import  (MyTokenObtainPairSerializer,  
RegisterStaffSerializer,TwoFactorAuthSerializer,
DeleteUserSerializer, CustomUserSerializer,
)

from datetime import timedelta
from django.utils.timezone import now
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed, ValidationError

from .serializers import  (MyTokenObtainPairSerializer,

ChangePasswordSerializer,  
  CustomUserSerializer, 
)
from rest_framework import generics
from rest_framework.exceptions import NotFound
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework import generics 
from rest_framework import status
from django.core.paginator import Paginator
from django.contrib.auth.hashers import make_password
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated
# Create your views here.
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json 
from rest_framework.decorators import api_view, permission_classes
from django.utils.timezone import make_aware
from datetime import datetime
from bs4 import BeautifulSoup
from rest_framework import serializers
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import UpdateAPIView
from django.shortcuts import get_object_or_404
from .models import CustomUser
from .serializers import ChangePasswordSerializer
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.exceptions import AuthenticationFailed
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser



class MyTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        serializer = MyTokenObtainPairSerializer(data=request.data, context={'request': request})
        try:
            serializer.is_valid(raise_exception=True)
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        except serializers.ValidationError as e:
            return Response({'detail': e.detail}, status=status.HTTP_400_BAD_REQUEST)
            
      
class TokenRefreshViewCustom(APIView):
    def post(self, request):
        # Get the refresh token from the request
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({"detail": "Refresh token is required."}, status=400)
        try:
            # Check if the refresh token is valid
            refresh = RefreshToken(refresh_token)
            # Generate a new access token
            access_token = str(refresh.access_token)
            return Response({
                "access": access_token,
            })
        except Exception as e:
            print(f"Error: {e}")  # Print the exception for debugging
            return Response({"detail": "Invalid refresh token."}, status=400)

class CustomUserUpdateView(generics.UpdateAPIView):
    queryset = CustomUser.objects.all()

    serializer_class = CustomUserSerializer
    permission_classes = [permissions.AllowAny]  # Change to IsAuthenticated if needed

    
    def get_object(self):
        user_id = self.kwargs.get('id')  # Get 'id' from URL kwargs
        return get_object_or_404(CustomUser, id=user_id)
 
class CustomUserListExcludingParamView(generics.ListAPIView):
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.AllowAny]  # Ensure user is authenticated


    def get_queryset(self):
        user_id = self.kwargs.get('user_id')  # Get user ID from URL
        return CustomUser.objects.exclude(id=user_id)


    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)  # Allow partial updates
        instance = self.get_object()

        # Preprocess the data to leave fields as-is if they are null
        updated_data = request.data.copy()
        for field in ['username', 'email', 'first_name', 'last_name', 'phone', 'image_url', 'two_factor_required']:
            if field in updated_data and updated_data[field] is None:
                updated_data.pop(field)  # Remove null fields to leave them unchanged

        serializer = self.get_serializer(instance, data=updated_data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Serialize the updated instance
        updated_instance_serializer = self.get_serializer(instance)
        return Response({
            'message': 'Profile updated successfully',
            'updated_data': updated_instance_serializer.data
        }, status=status.HTTP_200_OK)

        
# Delete User View
class CustomUserDeleteView(generics.DestroyAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    def get_object(self):
        return get_object_or_404(CustomUser, id=self.request.user.id)
    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        user.delete()
        return Response({"message": "User deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


class RegisterStaffView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = RegisterStaffSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        print('data', serializer)
        if not serializer.is_valid():
            # Return detailed validation errors
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            return Response({
                'message': 'User registered successfully',
                'user': RegisterStaffSerializer(user).data,
                'access_token': access_token,
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ChangePasswordView(APIView):
    permission_classes = [AllowAny]
    def post(self, request, user_id, *args, **kwargs):
        # Fetch user by ID
        user = get_object_or_404(CustomUser, id=user_id)

        # Serialize and validate the data
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=user)
            return Response({'detail': _("Password changed successfully.")}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class CategoryListAPIView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer



class ProductListAPIView(APIView):
    def get(self, request):
        products = Product.objects.all()
        serializer = ProductSerializer(
            products,
            many=True,
            context={"request": request}  # ✅ IMPORTANT
        )
        return Response(serializer.data)



from rest_framework import viewsets, filters
from rest_framework.response import Response
from django_filters import rest_framework as django_filters
from .models import Product, Category
from .serializers import ProductSerializer, CategorySerializer

class ProductFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr='icontains')
    category = django_filters.ModelChoiceFilter(queryset=Category.objects.all())

    class Meta:
        model = Product
        fields = ['title', 'category']

from rest_framework import generics, filters
from django_filters.rest_framework import DjangoFilterBackend

class ProductSearchAPIView(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    ]

    filterset_class = ProductFilter
    search_fields = ['name', 'description']  # optional
    ordering_fields = ['price', 'created_at']
    ordering = ['-created_at']


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    

class TestimonialListAPIView(ListAPIView):
    queryset = Testimonial.objects.filter(is_active=True).order_by("-created_at")
    serializer_class = TestimonialSerializer


class CreateOrderAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        items = request.data.get("items", [])
        total = 0

        order = Order.objects.create(
            user=request.user,
            total_amount=0
        )

        for item in items:
            product = Product.objects.get(id=item["product_id"])
            quantity = item["quantity"]
            price = product.discounted_price
            total += price * quantity

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price=price
            )

        order.total_amount = total
        order.save()

        return Response({"order_id": order.id, "total": total})

class InitiatePaymentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        order_id = request.data.get("order_id")
        provider = request.data.get("provider")

        order = Order.objects.get(id=order_id, user=request.user)

        payment = Payment.objects.create(
            order=order,
            user=request.user,
            provider=provider,
            amount=order.total_amount,
        )

        return Response({
            "payment_id": payment.id,
            "amount": payment.amount,
            "provider": provider,
        })

class PaymentCallbackAPIView(APIView):
    def post(self, request):
        transaction_id = request.data.get("transaction_id")
        payment_id = request.data.get("payment_id")
        status = request.data.get("status")

        payment = Payment.objects.get(id=payment_id)
        payment.transaction_id = transaction_id
        payment.status = status
        payment.save()

        if status == "success":
            payment.order.status = "paid"
            payment.order.save()

        return Response({"status": "ok"})


# Wishlist API Views
class WishlistListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get user's wishlist items"""
        wishlist_items = Wishlist.objects.filter(user=request.user)
        serializer = WishlistSerializer(wishlist_items, many=True, context={"request": request})
        return Response(serializer.data)

    def post(self, request):
        """Add product to wishlist"""
        product_id = request.data.get("product_id")
        if not product_id:
            return Response({"error": "product_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

        wishlist_item, created = Wishlist.objects.get_or_create(
            user=request.user,
            product=product
        )

        if not created:
            return Response({"message": "Product already in wishlist"}, status=status.HTTP_200_OK)

        serializer = WishlistSerializer(wishlist_item, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class WishlistDeleteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, product_id):
        """Remove product from wishlist"""
        try:
            wishlist_item = Wishlist.objects.get(user=request.user, product_id=product_id)
            wishlist_item.delete()
            return Response({"message": "Product removed from wishlist"}, status=status.HTTP_200_OK)
        except Wishlist.DoesNotExist:
            return Response({"error": "Wishlist item not found"}, status=status.HTTP_404_NOT_FOUND)


# Recently Viewed API Views
class RecentlyViewedListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get user's recently viewed items (limit to 20 most recent)"""
        recently_viewed = RecentlyViewed.objects.filter(user=request.user)[:20]
        serializer = RecentlyViewedSerializer(recently_viewed, many=True, context={"request": request})
        return Response(serializer.data)

    def post(self, request):
        """Add or update recently viewed product"""
        product_id = request.data.get("product_id")
        if not product_id:
            return Response({"error": "product_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

        # Update or create - this will update viewed_at timestamp
        recently_viewed, created = RecentlyViewed.objects.update_or_create(
            user=request.user,
            product=product,
            defaults={'viewed_at': now()}
        )

        serializer = RecentlyViewedSerializer(recently_viewed, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED)


class RecentlyViewedDeleteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, product_id):
        """Remove product from recently viewed"""
        try:
            recently_viewed = RecentlyViewed.objects.get(user=request.user, product_id=product_id)
            recently_viewed.delete()
            return Response({"message": "Product removed from recently viewed"}, status=status.HTTP_200_OK)
        except RecentlyViewed.DoesNotExist:
            return Response({"error": "Recently viewed item not found"}, status=status.HTTP_404_NOT_FOUND)
