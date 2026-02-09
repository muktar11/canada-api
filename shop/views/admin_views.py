from rest_framework import viewsets, permissions, views
from rest_framework.response import Response
from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from shop.models import CustomUser, Order, Product, Category, Testimonial
from shop.serializers import (
    AdminUserSerializer, 
    AdminOrderSerializer, 
    AdminProductSerializer,
    CategorySerializer, 
    TestimonialSerializer,
    VendorRegisterSerializer
)

class IsAdminUser(permissions.BasePermission):
    """
    Allows access only to admin users.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)

class AdminDashboardStatsView(views.APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        total_users = CustomUser.objects.count()
        total_orders = Order.objects.count()
        total_products = Product.objects.count()
        total_sales = Order.objects.filter(status='paid').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        
        return Response({
            "total_users": total_users,
            "total_orders": total_orders,
            "total_products": total_products,
            "total_sales": total_sales,
        })

class AdminUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all().order_by('-date_joined')
    serializer_class = AdminUserSerializer
    permission_classes = [IsAdminUser]

class AdminOrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().order_by('-created_at')
    serializer_class = AdminOrderSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status']


class AdminCategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by('-created_at')
    serializer_class = CategorySerializer
    permission_classes = [IsAdminUser]

class AdminTestimonialViewSet(viewsets.ModelViewSet):
    queryset = Testimonial.objects.all().order_by('-created_at')
    serializer_class = TestimonialSerializer
    permission_classes = [IsAdminUser]

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from shop.models import Order

class AdminUpdateOrderStatusView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def patch(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)

        new_status = request.data.get("status")

        allowed_statuses = ["pending", "paid", "shipped", "cancelled"]

        if new_status not in allowed_statuses:
            return Response(
                {"error": "Invalid order status"},
                status=status.HTTP_400_BAD_REQUEST
            )

        order.status = new_status
        order.save(update_fields=["status"])

        return Response(
            {
                "id": order.id,
                "status": order.status,
                "message": "Order status updated"
            },
            status=status.HTTP_200_OK
        )

from rest_framework import serializers
class AdminProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().order_by("-created_at")
    serializer_class = AdminProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user



        serializer.save(vendor=user)

    def get_queryset(self):
        user = self.request.user

        # Vendors only see their own products
        if user.roles == "vendor":
            return self.queryset.filter(vendor=user)

        # Admins see all
        return self.queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def perform_update(self, serializer):
        product = self.get_object()
        user = self.request.user

        serializer.save()



class AdminUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all().order_by("-date_joined")
    serializer_class = AdminUserSerializer
    permission_classes = [permissions.IsAdminUser]
    http_method_names = ["get", "patch", "delete"]

    def perform_update(self, serializer):
        # Prevent admin from deactivating themselves
        if self.request.user.pk == serializer.instance.pk:
            if "is_active" in serializer.validated_data:
                raise serializers.ValidationError(
                    {"is_active": "You cannot deactivate yourself."}
                )
            if "is_staff" in serializer.validated_data:
                raise serializers.ValidationError(
                    {"is_staff": "You cannot change your own staff status."}
                )

        serializer.save()


# shop/views/admin_vendor.py
from rest_framework import viewsets, permissions
from shop.models import CustomUser
from shop.serializers import AdminUserSerializer
from rest_framework.decorators import action

class AdminVendorViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return CustomUser.objects.filter(roles="vendor").order_by("-date_joined")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return VendorRegisterSerializer
        return AdminUserSerializer


    def perform_create(self, serializer):
        # VendorRegisterSerializer.create() already:
        # - hashes password
        # - sets role=vendor
        # - sends verification email
        serializer.save()

    @action(detail=True, methods=["patch"])
    def toggle_active(self, request, pk=None):
        vendor = self.get_object()
        vendor.is_active = not vendor.is_active
        vendor.save(update_fields=["is_active"])
        return Response({"is_active": vendor.is_active})
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import uuid
import os

class FileUploadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        file = request.FILES.get("file")

        if not file:
            return Response(
                {"error": "No file provided"},
                status=status.HTTP_400_BAD_REQUEST
            )

        ext = os.path.splitext(file.name)[1]
        filename = f"uploads/{uuid.uuid4()}{ext}"

        path = default_storage.save(filename, ContentFile(file.read()))
        url = default_storage.url(path)

        return Response(
            {"url": url},
            status=status.HTTP_201_CREATED
        )
