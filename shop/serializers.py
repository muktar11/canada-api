from django.contrib.auth.password_validation import validate_password
from .models import CustomUser
import random
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime, timedelta
from django.utils.timezone import now
from urllib.parse import urljoin
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken 
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum, Avg
from .models import Category, Testimonial, Product, Wishlist, RecentlyViewed, Order, OrderItem, Payment

class ChangePasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    confirm_new_password = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        # Ensure new passwords match
        if attrs['new_password'] != attrs['confirm_new_password']:
            raise serializers.ValidationError(_("The new passwords do not match."))
        return attrs

    def save(self, user):
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user



class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    email = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)
    two_factor_required = serializers.BooleanField(read_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(request=self.context.get('request'), email=email, password=password)

            if not user:
                # Check if user exists to handle verification expiry logic
                try:
                    user_obj = CustomUser.objects.get(email=email)
                except CustomUser.DoesNotExist:
                    raise serializers.ValidationError(_('Invalid email or password.'))

                if user_obj.check_password(password):
                    if not user_obj.is_active:
                        # Check if this is an unverified user with an expired code
                        if not user_obj.is_email_verified:
                            if user_obj.email_code_expires_at and user_obj.email_code_expires_at < now():
                                user_obj.delete()
                                raise serializers.ValidationError(_('Verification code expired. User deleted. Please register again.'))
                            else:
                                raise serializers.ValidationError(_('Email not verified.'))
                        raise serializers.ValidationError(_('User account is disabled.'))

                raise serializers.ValidationError(_('Invalid email or password.'))

            if not user.is_active:
                raise serializers.ValidationError(_('User account is disabled.'))
            
           
            # If 2FA is not enabled, proceed to generate tokens
            refresh = RefreshToken.for_user(user)



            return {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user_id': user.id,
                'email': user.email,
                'username':user.username,
            }

        raise serializers.ValidationError(_('Email and password are required.'))
class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'id','username', 'email', 
    
        ]
        read_only_fields = ['email']  # Prevent phone from being updated


'''
class RegisterStaffSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password', 'password2')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Passwords do not match"})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')  # 🔥 VERY IMPORTANT

        password = validated_data.pop('password')

        user = CustomUser.objects.create_user(
            password=password,
            **validated_data
        )
        return user
'''
import random
from django.core.mail import send_mail
from django.utils.timezone import now
from datetime import timedelta

def send_email_verification(user):
    code = str(random.randint(100000, 999999))

    user.email_verification_code = code
    user.email_code_expires_at = now() + timedelta(minutes=10)
    user.save()

    send_mail(
        subject="Verify your account",
        message=f"Your verification code is: {code}",
        from_email=None,
        recipient_list=[user.email],
        fail_silently=False,
    )

class RegisterStaffSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password', 'password2')
        extra_kwargs = {
            'email': {'validators': [], 'required': True}  # Disable default UniqueValidator to handle manually
        }

    def validate_email(self, value):
        try:
            user = CustomUser.objects.get(email=value)
        except CustomUser.DoesNotExist:
            return value

        if not user.is_email_verified:
            # If the verification code has expired, delete the user so they can register again
            if user.email_code_expires_at and user.email_code_expires_at < now():
                user.delete()
                return value
            else:
                raise serializers.ValidationError(_("This email is already registered but not verified. Please check your inbox."))
        
        raise serializers.ValidationError(_("A user with this email already exists."))

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": _("Passwords do not match.")})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')

        user = CustomUser.objects.create_user(
            password=password,
            is_active=False,  # 🚫 block login until verification
            **validated_data
        )

        send_email_verification(user)
        return user

class VerifyEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)

    def validate(self, attrs):
        try:
            user = CustomUser.objects.get(email=attrs['email'])
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("Invalid email")

        if user.email_verification_code != attrs['code']:
            raise serializers.ValidationError("Invalid verification code")

        if user.email_code_expires_at < now():
            user.delete()
            raise serializers.ValidationError("Verification code expired")

        user.is_active = True
        user.is_email_verified = True
        user.email_verification_code = None
        user.save()

        return user


class TwoFactorAuthSerializer(serializers.Serializer):
    phone = serializers.CharField(write_only=True)
    code = serializers.IntegerField(write_only=True)
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)

    def validate(self, attrs):
        phone = attrs.get('phone')
        code = attrs.get('code')

        try:
            user = CustomUser.objects.get(phone=phone)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError(_('Invalid phone number.'))

        if user.two_factor_auth_code != code:
            raise serializers.ValidationError(_('Invalid two-factor authentication code.'))

        # Reset 2FA code after successful validation
        user.two_factor_auth_code = 0
        user.save()

        # Generate tokens
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user_id': user.id,
            'phone': user.phone,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'username':user.username,
            'image_url': user.image_url,
        }

class DeleteUserSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=15)

    def validate_phone(self, value):
        try:
            user = get_user_model().objects.get(phone=value)
        except get_user_model().DoesNotExist:
            raise ValidationError("User with this phone number does not exist.")
        return value



class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'title', 'img']


class ProductSerializer(serializers.ModelSerializer):
    imgs = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "title",
            "price",
            "discounted_price",
            "reviews",
            "imgs",
        ]

    def get_imgs(self, obj):
        request = self.context.get("request")

        previews = obj.preview_images
        thumbnails = obj.thumbnail_images

        if request:
            previews = [request.build_absolute_uri(img) for img in previews]
            thumbnails = [request.build_absolute_uri(img) for img in thumbnails]

        return {
            "previews": previews,
            "thumbnails": thumbnails,
        }



class TestimonialSerializer(serializers.ModelSerializer):
    authorImg = serializers.ImageField(source="author_img")
    authorName = serializers.CharField(source="author_name")
    authorRole = serializers.CharField(source="author_role")

    class Meta:
        model = Testimonial
        fields = [
            "id",
            "review",
            "authorName",
            "authorRole",
            "authorImg",
            "rating",
        ]

class OrderItemSerializer(serializers.ModelSerializer):
    product_title = serializers.ReadOnlyField(source="product.title")

    class Meta:
        model = OrderItem
        fields = ["id", "product", "product_title", "quantity", "price"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ["id", "total_amount", "status", "items", "created_at"]


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "id",
            "order",
            "provider",
            "transaction_id",
            "amount",
            "status",
            "created_at",
        ]


class WishlistSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Wishlist
        fields = ["id", "product", "product_id", "created_at"]
        read_only_fields = ["id", "created_at"]


class RecentlyViewedSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = RecentlyViewed
        fields = ["id", "product", "product_id", "viewed_at"]
        read_only_fields = ["id", "viewed_at"]
