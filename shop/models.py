from django.db import models

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.db.models.signals import post_save
from django.utils.timezone import now
from django.dispatch import receiver
from django.core.exceptions import ValidationError

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Phone number must be set')

        user = self.model(email=email, **extra_fields)
        user.set_password(password)  # Hash the password
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user( email, password, **extra_fields)



class CustomUser(AbstractUser):
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    username = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(max_length=255, blank=True, null=True, unique=True)
    roles = models.CharField(max_length=15)
    objects = CustomUserManager()  # Use the custom user manager
    USERNAME_FIELD = 'email'  # Set phone as the username field
    REQUIRED_FIELDS = [] 
    def __str__(self):
        return self.email



class Category(models.Model):
    title = models.CharField(max_length=100)
    img = models.ImageField(upload_to='categories/')  # store uploaded images
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title



from django.db import models

class Product(models.Model):
    title = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2)
    reviews = models.IntegerField(default=0)
    preview_images = models.JSONField(default=list)
    thumbnail_images = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Testimonial(models.Model):
    review = models.TextField()
    author_name = models.CharField(max_length=100)
    author_role = models.CharField(max_length=100)
    author_img = models.ImageField(upload_to="testimonials/")
    rating = models.PositiveIntegerField(default=5)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.author_name



from django.db import models
from django.contrib.auth.models import User
from .models import Product

class Order(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("shipped", "Shipped"),
        ("cancelled", "Cancelled"),
    )

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="orders")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.title} x {self.quantity}"

class Payment(models.Model):
    PAYMENT_STATUS = (
        ("initiated", "Initiated"),
        ("success", "Success"),
        ("failed", "Failed"),
    )
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="payment")
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    provider = models.CharField(max_length=50)  # stripe, paypal, telr, etc.
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default="initiated")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.provider} - {self.status}"


class Wishlist(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="wishlist_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')  # Prevent duplicate wishlist items
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.product.title}"


class RecentlyViewed(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="recently_viewed_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'product')  # One entry per user-product combination
        ordering = ['-viewed_at']
        indexes = [
            models.Index(fields=['user', '-viewed_at']),
        ]

    def __str__(self):
        return f"{self.user.email} viewed {self.product.title} at {self.viewed_at}"