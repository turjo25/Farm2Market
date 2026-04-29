from django.db import models
from django.contrib.auth.models import User


# Profile (Unified)
class Profile(models.Model):
    ROLE_CHOICES = (
        ("farmer", "Farmer"),
        ("buyer", "Buyer"),
    )
    profile_id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="buyer")

    # Extensible fields
    farm_name = models.CharField(max_length=255, blank=True, null=True)
    farm_location = models.CharField(max_length=255, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    delivery_address = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"


# Category
class Category(models.Model):
    category_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


# Product
class Product(models.Model):
    product_id = models.AutoField(primary_key=True)
    farmer = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="products"
    )
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="products"
    )
    name = models.CharField(max_length=255)
    description = models.TextField()
    price_per_unit = models.IntegerField(default=0)
    stock_quantity = models.IntegerField(default=0)
    unit = models.CharField(max_length=50)
    image = models.ImageField(upload_to="product_images/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# Cart
class Cart(models.Model):
    cart_id = models.AutoField(primary_key=True)
    buyer = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name="cart")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart - {self.buyer.user.username}"


# Cart Item
class CartItem(models.Model):
    cart_item_id = models.AutoField(primary_key=True)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def subtotal(self):
        return self.product.price_per_unit * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product.name} (Cart: {self.cart.buyer.user.username})"


# Logistic
class Logistic(models.Model):
    name = models.CharField(max_length=100) # e.g., Pathao, Uber, Steadfast
    contact_number = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.name


# Order Workflow Models
class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING',           'Order Placed'),
        ('CONFIRMED',         'Order Confirmed'),
        ('ASSIGNED',          'Delivery Assigned'),
        ('OUT_FOR_DELIVERY',  'Out for Delivery'),
        ('DELIVERED',         'Delivered'),
        ('COMPLETED',         'Completed'),
        ('REJECTED',          'Rejected'),
        ('CANCELLED',         'Cancelled'),
    ]

    order_id        = models.AutoField(primary_key=True)
    buyer           = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='orders')
    farmer          = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='received_orders')
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    logistic        = models.ForeignKey(Logistic, on_delete=models.SET_NULL, null=True, blank=True)
    delivery_note   = models.TextField(blank=True, null=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.order_id} | {self.buyer} → {self.farmer} | {self.status}"


class OrderItem(models.Model):
    order_item_id = models.AutoField(primary_key=True)
    order         = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product       = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity      = models.PositiveIntegerField(default=1)
    price_at_order = models.IntegerField()  # snapshot of price when ordered

    def subtotal(self):
        return self.price_at_order * self.quantity


class Notification(models.Model):
    notification_id = models.AutoField(primary_key=True)
    recipient       = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='notifications')
    order           = models.ForeignKey(Order, on_delete=models.CASCADE, null=True, blank=True)
    message         = models.TextField()
    is_read         = models.BooleanField(default=False)
    created_at      = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification → {self.recipient.user.username}: {self.message[:40]}"

# Review
class Review(models.Model):
    review_id = models.AutoField(primary_key=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    buyer = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='reviews_given')
    rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('product', 'buyer')

    def __str__(self):
        return f"{self.rating} star - {self.product.name} by {self.buyer.user.username}"
