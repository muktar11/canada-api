from django.urls import path
from .views import CategoryListAPIView,  ProductListAPIView, ProductSearchAPIView, TestimonialListAPIView
from django.urls import path
from .views import (
    CategoryListAPIView,
    ProductListAPIView,
    TestimonialListAPIView,
    CreateOrderAPIView,
    InitiatePaymentAPIView,
    PaymentCallbackAPIView,
)
from django.urls import path
from .views import(
    RegisterStaffView,
    MyTokenObtainPairView,
    ChangePasswordView,
    TokenRefreshViewCustom, 
    CustomUserUpdateView,
    CustomUserListExcludingParamView,
    CustomUserDeleteView,
    WishlistListCreateAPIView,
    WishlistDeleteAPIView,
    RecentlyViewedListCreateAPIView,
    RecentlyViewedDeleteAPIView,
)
from . import views


urlpatterns = [
    path('token/', MyTokenObtainPairView.as_view(), name='auth-login'),
    path('token/refresh/', TokenRefreshViewCustom.as_view(), name='token_refresh'),
    path('users/exclude/<int:user_id>/', CustomUserListExcludingParamView.as_view(), name='exclude-user'),
    path('register/', RegisterStaffView.as_view(), name='auth-register'),

    path('products-search/', ProductSearchAPIView.as_view(), name='product-search'),
    
    path('user/update/<int:id>/', CustomUserUpdateView.as_view(), name='user-update'),
    path('user/delete/', CustomUserDeleteView.as_view(), name='user-delete'),
    
    path('categories/', CategoryListAPIView.as_view(), name='category-list'),
    path("products/", ProductListAPIView.as_view()),
    path("testimonials/", TestimonialListAPIView.as_view()),

    path("orders/create/", CreateOrderAPIView.as_view()),
    path("payments/initiate/", InitiatePaymentAPIView.as_view()),
    path("payments/callback/", PaymentCallbackAPIView.as_view()),

    # Wishlist endpoints
    path("wishlist/", WishlistListCreateAPIView.as_view(), name="wishlist-list-create"),
    path("wishlist/<int:product_id>/", WishlistDeleteAPIView.as_view(), name="wishlist-delete"),

    # Recently Viewed endpoints
    path("recently-viewed/", RecentlyViewedListCreateAPIView.as_view(), name="recently-viewed-list-create"),
    path("recently-viewed/<int:product_id>/", RecentlyViewedDeleteAPIView.as_view(), name="recently-viewed-delete"),
]
