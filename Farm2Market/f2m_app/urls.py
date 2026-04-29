from django.urls import path
from . import views

urlpatterns = [
    # Authentication related urls
    path('login/', views.login_view, name="login_view"),
    path('register/', views.register_view, name="register_view"),
    path('logout/', views.logout_view, name="logout_view"),

    # Home and Dashboard
    path('', views.home_view, name="home_view"),
    path('products/', views.product_list_view, name="product_list_view"),
    path('product/<int:product_id>/', views.product_detail_view, name="product_detail_view"),
    path('product/<int:product_id>/rate/', views.rate_product_view, name="rate_product_view"),
    path('farmer/dashboard/', views.farmer_dashboard_view, name="farmer_dashboard_view"),
    path('farmer/product/edit/<int:product_id>/', views.edit_product_view, name="edit_product_view"),
    path('buyer/dashboard/', views.buyer_dashboard_view, name="buyer_dashboard_view"),
    path('profile/', views.profile_view, name="profile_view"),
    
     # Cart & Orders
    path('cart/', views.cart_view, name="cart_view"),
    path('cart/add/<int:product_id>/', views.add_to_cart_view, name="add_to_cart_view"),
    path('cart/update/<int:item_id>/', views.update_cart_view, name="update_cart_view"),
    path('checkout/', views.checkout_view, name="checkout_view"),
    
    path('order/action/farmer/<int:order_id>/', views.farmer_order_action_view, name="farmer_order_action_view"),
    path('order/action/buyer/<int:order_id>/', views.buyer_order_action_view, name="buyer_order_action_view"),
]
