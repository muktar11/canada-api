from django.urls import path
from . views.auth import (
    GoogleLoginView,
    MyTokenObtainPairView,
    TokenRefreshViewCustom,
    RegisterStaffView,
    VerifyEmailView,
    GoogleLoginView
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
)
from . views.payments import InitiatePaymentAPIView, InitiateStripePaymentAPIView
from . views.webhooks import stripe_webhook

urlpatterns = [
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


    
]