from .models import Cart, CartItem, Order

def cart_count(request):
    """
    Injects `cart_count` (total number of distinct items in the buyer's cart)
    into every template context. Supports both authenticated and session-based carts.
    """
    if request.user.is_authenticated:
        count = CartItem.objects.filter(cart__buyer__user=request.user).count()
        return {'cart_count': count}
    
    # Session-based cart count
    session_cart = request.session.get('cart', {})
    return {'cart_count': len(session_cart)}

def user_notifications(request):
    """
    Injects notification flags for farmers and buyers.
    """
    has_new_order = False
    has_delivered_order = False
    if request.user.is_authenticated:
        try:
            if hasattr(request.user, 'profile'):
                if request.user.profile.role == 'farmer':
                    has_new_order = Order.objects.filter(farmer=request.user.profile, status='PENDING').exists()
                elif request.user.profile.role == 'buyer':
                    has_delivered_order = Order.objects.filter(buyer=request.user.profile, status='DELIVERED').exists()
        except:
            pass
    return {'has_new_order': has_new_order, 'has_delivered_order': has_delivered_order}
