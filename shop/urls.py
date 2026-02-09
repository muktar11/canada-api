from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . views import admin_views
from . views.auth import (
    GoogleLoginView,
    MyTokenObtainPairView,
    TokenRefreshViewCustom,
    RegisterStaffView,
    VerifyEmailView,
    GoogleLoginView,
    VendorRegisterAPIView
)
from . views.orders import (
    CreateOrderAPIView,
    ProductSearchAPIView, 
    CategoryListAPIView,
    ProductListAPIView,
    TestimonialListAPIView, 
    CartAPIView,

    WishlistListCreateAPIView,
    WishlistDeleteAPIView,
    RecentlyViewedListCreateAPIView,
    RecentlyViewedDeleteAPIView,



    
    VendorProductCreateAPIView,
    VendorMyProductsAPIView,
    VendorProductListAPIView,
    VendorOrderListAPIView,
    
)


from . views.payments import InitiatePaymentAPIView, InitiateStripePaymentAPIView
from . views.webhooks import stripe_webhook



router = DefaultRouter()
router.register(r'admin/users', admin_views.AdminUserViewSet)
router.register(r'admin/orders', admin_views.AdminOrderViewSet)
router.register(r'admin/products', admin_views.AdminProductViewSet)
router.register(r'admin/categories', admin_views.AdminCategoryViewSet)
router.register(r'admin/testimonials', admin_views.AdminTestimonialViewSet)
router.register(r"admin/products", admin_views.AdminProductViewSet, basename="admin-products")
router.register(r"admin/vendors", admin_views.AdminVendorViewSet, basename="admin-vendors")
from . views.admin_views import FileUploadAPIView
urlpatterns = [
    path('', include(router.urls)),
    path("upload/", FileUploadAPIView.as_view(), name="file-upload"),
    path("orders/<int:order_id>/status/", admin_views.AdminUpdateOrderStatusView.as_view(),name="admin-update-order-status"),
    path('admin/stats/', admin_views.AdminDashboardStatsView.as_view()),
    path("token/", MyTokenObtainPairView.as_view()),
    path("refresh/", TokenRefreshViewCustom.as_view()),
    path("verify-email/", VerifyEmailView.as_view()),
    path("register/", RegisterStaffView.as_view()),
    path("google-login/", GoogleLoginView.as_view()),

    path('products-search/', ProductSearchAPIView.as_view(), name='product-search'),
    path('categories/', CategoryListAPIView.as_view(), name='category-list'),
    path("products/", ProductListAPIView.as_view()),
    path("testimonials/", TestimonialListAPIView.as_view()),
    path("orders/create/", CreateOrderAPIView.as_view()),
    path("cart/", CartAPIView.as_view()),
 
    # Wishlist endpoints
    path("wishlist/", WishlistListCreateAPIView.as_view(), name="wishlist-list-create"),
    path("wishlist/<int:product_id>/", WishlistDeleteAPIView.as_view(), name="wishlist-delete"),

    # Recently Viewed endpoints
    path("recently-viewed/", RecentlyViewedListCreateAPIView.as_view(), name="recently-viewed-list-create"),
    path("recently-viewed/<int:product_id>/", RecentlyViewedDeleteAPIView.as_view(), name="recently-viewed-delete"),
    

    path("payments/initiate/", InitiatePaymentAPIView.as_view()),
    path("payments/stripe/initiate/", InitiateStripePaymentAPIView.as_view()),
    path("payments/stripe/webhook/", stripe_webhook),




    path("vendors/register/", VendorRegisterAPIView.as_view()),
    path("vendors/products/", VendorProductCreateAPIView.as_view()),
    path("vendors/my-products/", VendorMyProductsAPIView.as_view()),
    path("vendors/<int:vendor_id>/products/", VendorProductListAPIView.as_view()),
    path("vendors/orders/", VendorOrderListAPIView.as_view()),

   
]



