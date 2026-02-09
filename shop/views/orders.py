from .auth import IsVendor
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, generics, viewsets, filters
from django.shortcuts import get_object_or_404, render
from django.utils.timezone import now
from django_filters import rest_framework as django_filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.generics import ListAPIView

from shop.models import Order, OrderItem, Product, Category, Testimonial, Wishlist, RecentlyViewed
from shop.serializers import (
    AdminOrderSerializer, OrderSerializer, CategorySerializer, ProductSerializer, 
    TestimonialSerializer, VendorProductCreateSerializer, WishlistSerializer, RecentlyViewedSerializer
)


class CreateOrderAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        items = request.data.get("items", [])

        if not items:
            return Response({"detail": "No items provided"}, status=400)

        order = Order.objects.create(
            user=request.user,
            status="pending",
            total_amount=0
        )

        total = 0

        for item in items:
            product = get_object_or_404(Product, id=item["product_id"])
            quantity = int(item["quantity"])
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

        return Response(OrderSerializer(order).data, status=201)








class CartAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        order = Order.objects.filter(user=request.user, status='pending').order_by('-created_at').first()
        if not order:
            return Response([])

        items = []
        for item in order.items.all():
            product = item.product
            serializer = ProductSerializer(product, context={"request": request})
            items.append({
                "id": product.id,
                "title": product.title,
                "price": product.price,
                "discountedPrice": product.discounted_price,
                "quantity": item.quantity,
                "imgs": serializer.data["imgs"],
            })
        return Response(items)





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



class ProductFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr='icontains')
    category = django_filters.ModelChoiceFilter(queryset=Category.objects.all())

    class Meta:
        model = Product
        fields = ['title', 'category']


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
        





class VendorProductCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, IsVendor]

    def post(self, request):
        serializer = VendorProductCreateSerializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        product = serializer.save()

        return Response(
            ProductSerializer(product, context={"request": request}).data,
            status=status.HTTP_201_CREATED
        )

class VendorProductCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, IsVendor]

    def post(self, request):
        serializer = VendorProductCreateSerializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        product = serializer.save()

        return Response(
            ProductSerializer(product, context={"request": request}).data,
            status=status.HTTP_201_CREATED
        )


class VendorMyProductsAPIView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, IsVendor]

    def get_queryset(self):
        return Product.objects.filter(vendor=self.request.user).order_by("-created_at")


class VendorProductListAPIView(generics.ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        vendor_id = self.kwargs["vendor_id"]
        return Product.objects.filter(
            vendor_id=vendor_id,
            vendor__roles="vendor"
        ).order_by("-created_at")

class VendorOrderListAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsVendor]
    serializer_class = AdminOrderSerializer

    def get_queryset(self):
        return Order.objects.filter(
            items__product__vendor=self.request.user
        ).distinct().order_by("-created_at")
