from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Profile, Product, Category, Cart, CartItem, Order, OrderItem, Notification, Logistic, Review
from django.db.models import Count, Q, Avg


# REGISTER VIEW
def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        role = request.POST.get("role")

        # Basic Validation
        if not password or password != confirm_password:
            messages.error(request, "Passwords are required and must match.")
            return redirect("register_view")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("register_view")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect("register_view")

        # Create User
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        # Create Profile Based on Role
        if role == "farmer":
            farm_name = request.POST.get("farm_name")
            farm_location = request.POST.get("farm_location")
            bio = request.POST.get("bio")

            if not farm_name or not farm_location:
                messages.error(request, "Farm name and location are required.")
                user.delete()
                return redirect("register_view")

            Profile.objects.create(
                user=user,
                role=role,
                farm_name=farm_name,
                farm_location=farm_location,
                bio=bio
            )

        elif role == "buyer":
            delivery_address = request.POST.get("delivery_address")

            if not delivery_address:
                messages.error(request, "Delivery address is required.")
                user.delete()
                return redirect("register_view")

            Profile.objects.create(
                user=user,
                role=role,
                delivery_address=delivery_address
            )
        else:
            user.delete()
            messages.error(request, "Invalid role selected.")
            return redirect("register_view")

        messages.success(request, "Registration successful! You can now log in.")
        return redirect("login_view")

    return render(request, "F2M/register.html")



# LOGIN VIEW
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            
            # Merge session cart into database cart
            session_cart = request.session.get('cart', {})
            if session_cart and hasattr(user, 'profile') and user.profile.role == 'buyer':
                buyer_profile = user.profile
                cart, created = Cart.objects.get_or_create(buyer=buyer_profile)
                
                for product_id, quantity in session_cart.items():
                    try:
                        product = Product.objects.get(product_id=product_id)
                        cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)
                        if not item_created:
                            cart_item.quantity = min(cart_item.quantity + quantity, product.stock_quantity)
                        else:
                            cart_item.quantity = min(quantity, product.stock_quantity)
                        cart_item.save()
                    except Product.DoesNotExist:
                        continue
                
                # Clear session cart after merging
                del request.session['cart']

            if hasattr(user, 'profile') and user.profile.role == 'farmer':
                return redirect("farmer_dashboard_view")
            else:
                return redirect("home_view")
        else:
            messages.error(request, "Invalid username or password.")
            return redirect("login_view")

    return render(request, "F2M/login.html")


# LOGOUT VIEW
@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect("home_view")


# HOME VIEW
def home_view(request):
    categories = Category.objects.all()
    context = {'categories': categories}
    return render(request, "F2M/home.html", context)


# PRODUCT RELATED VIEWS
def product_list_view(request):
    products = Product.objects.select_related('farmer', 'category').annotate(
        avg_rating=Avg('reviews__rating'),
        review_count=Count('reviews', distinct=True)
    ).all().order_by('-created_at')
    categories = Category.objects.all()
    selected_category = None
    
    search_query = request.GET.get('search')
    if search_query:
        words = search_query.split()
        if words:
            query = Q()
            for word in words:
                query |= Q(name__icontains=word)
            products = products.filter(query)
    
    category_id = request.GET.get('category')
    if category_id:
        try:
            selected_category = Category.objects.get(category_id=category_id)
            products = products.filter(category=selected_category)
        except Category.DoesNotExist:
            pass
            
    context = {
        'products': products.distinct(),
        'categories': categories,
        'selected_category': selected_category,
        'search_query': search_query
    }
    return render(request, "F2M/products.html", context)

def product_detail_view(request, product_id):
    try:
        product = Product.objects.select_related('farmer', 'category').annotate(
            avg_rating=Avg('reviews__rating'),
            review_count=Count('reviews', distinct=True)
        ).get(product_id=product_id)
    except Product.DoesNotExist:
        messages.error(request, "Product not found.")
        return redirect('product_list_view')
        
    can_rate = False
    user_rating = None
    
    if request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.role == 'buyer':
        has_bought = OrderItem.objects.filter(
            order__buyer=request.user.profile,
            order__status__in=['DELIVERED', 'COMPLETED'],
            product=product
        ).exists()
        
        if has_bought:
            can_rate = True
            try:
                user_review = Review.objects.get(product=product, buyer=request.user.profile)
                user_rating = user_review.rating
            except Review.DoesNotExist:
                pass
                
    context = {
        'product': product,
        'can_rate': can_rate,
        'user_rating': user_rating,
    }
    return render(request, "F2M/product_detail.html", context)

@login_required
def rate_product_view(request, product_id):
    if request.method == 'POST' and hasattr(request.user, 'profile') and request.user.profile.role == 'buyer':
        try:
            product = Product.objects.get(product_id=product_id)
            rating_val = int(request.POST.get('rating', 0))
            
            if 1 <= rating_val <= 5:
                has_bought = OrderItem.objects.filter(
                    order__buyer=request.user.profile,
                    order__status__in=['DELIVERED', 'COMPLETED'],
                    product=product
                ).exists()
                
                if has_bought:
                    Review.objects.update_or_create(
                        product=product,
                        buyer=request.user.profile,
                        defaults={'rating': rating_val}
                    )
                    messages.success(request, f"Thank you for rating {product.name}!")
                else:
                    messages.error(request, "You can only rate products you have purchased and received.")
            else:
                messages.error(request, "Invalid rating value.")
        except Product.DoesNotExist:
            messages.error(request, "Product not found.")
        except ValueError:
            messages.error(request, "Invalid rating format.")
            
    return redirect('product_detail_view', product_id=product_id)

@login_required
def edit_product_view(request, product_id):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'farmer':
        messages.error(request, "You must be a farmer to edit products.")
        return redirect('home_view')
    farmer_profile = request.user.profile
        
    try:
        product = Product.objects.get(product_id=product_id, farmer=farmer_profile)
    except Product.DoesNotExist:
        messages.error(request, "Product not found or you don't have permission to edit it.")
        return redirect('farmer_dashboard_view')
        
    if request.method == "POST":
        product.name = request.POST.get("name")
        
        category_id = request.POST.get("category")
        if category_id:
            try:
                product.category = Category.objects.get(category_id=category_id)
            except Category.DoesNotExist:
                pass
                
        price_per_unit = int(request.POST.get("price_per_unit", 0))
        stock_quantity = int(request.POST.get("stock_quantity", 0))
        
        if price_per_unit < 0 or stock_quantity < 0:
            messages.error(request, "Price and stock quantity cannot be negative.")
            return redirect('edit_product_view', product_id=product_id)
            
        product.price_per_unit = price_per_unit
        product.stock_quantity = stock_quantity
        product.unit = request.POST.get("unit")
        product.description = request.POST.get("description")
        
        if "image" in request.FILES:
            product.image = request.FILES.get("image")
        
        product.save()
        messages.success(request, "Product updated successfully!")
        return redirect('farmer_dashboard_view')
        
    categories = Category.objects.all()
    context = {
        'product': product,
        'categories': categories
    }
    return render(request, "F2M/edit_product.html", context)



# PROFILE RELATED VIEWS
@login_required
def profile_view(request):
    user = request.user

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "update_profile":
            user.first_name = request.POST.get("first_name", user.first_name)
            user.last_name = request.POST.get("last_name", user.last_name)
            user.email = request.POST.get("email", user.email)
            user.save()

            if hasattr(user, 'profile'):
                profile = user.profile
                if profile.role == 'farmer':
                    profile.farm_name = request.POST.get("farm_name", profile.farm_name)
                    profile.farm_location = request.POST.get("farm_location", profile.farm_location)
                    profile.bio = request.POST.get("bio", profile.bio)
                elif profile.role == 'buyer':
                    profile.delivery_address = request.POST.get("delivery_address", profile.delivery_address)
                profile.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('profile_view')

    # Compute initials from first+last name, or username
    full_name = user.get_full_name()
    if full_name.strip():
        parts = full_name.split()
        initials = (parts[0][0] + parts[-1][0]).upper() if len(parts) > 1 else parts[0][:2].upper()
    else:
        initials = user.username[:2].upper()

    # Detect role
    is_farmer = hasattr(user, 'profile') and user.profile.role == 'farmer'
    farmer_profile = None
    total_products = in_stock_products = out_of_stock_products = 0

    if is_farmer:
        farmer_profile = user.profile
        products_qs = Product.objects.filter(farmer=farmer_profile)
        
        stats = products_qs.aggregate(
            total=Count('product_id'),
            in_stock=Count('product_id', filter=Q(stock_quantity__gt=0)),
            out_stock=Count('product_id', filter=Q(stock_quantity=0))
        )
        total_products = stats['total'] or 0
        in_stock_products = stats['in_stock'] or 0
        out_of_stock_products = stats['out_stock'] or 0

    # Active tab is driven by the URL query param — default to 'profile'
    active_tab = request.GET.get('tab', 'profile')
    valid_tabs = ['profile', 'farm'] if is_farmer else ['profile']
    if active_tab not in valid_tabs:
        active_tab = 'profile'

    context = {
        'initials': initials,
        'is_farmer': is_farmer,
        'farmer_profile': farmer_profile,
        'total_products': total_products,
        'in_stock_products': in_stock_products,
        'out_of_stock_products': out_of_stock_products,
        'active_tab': active_tab,
    }
    
    template_name = "F2M/farmer_profile.html" if is_farmer else "F2M/buyer_profile.html"
    return render(request, template_name, context)

# FARMER
@login_required
def farmer_dashboard_view(request):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'farmer':
        messages.error(request, "You must be a farmer to view this page.")
        return redirect('home_view')
    farmer_profile = request.user.profile

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "add_product":
            category_id = request.POST.get("category")
            name = request.POST.get("name")
            description = request.POST.get("description")
            price_per_unit = int(request.POST.get("price_per_unit", 0))
            stock_quantity = int(request.POST.get("stock_quantity", 0))
            
            if price_per_unit < 0 or stock_quantity < 0:
                messages.error(request, "Price and stock quantity cannot be negative.")
                return redirect('farmer_dashboard_view')
                
            unit = request.POST.get("unit")
            image = request.FILES.get("image")
            
            try:
                category = Category.objects.get(category_id=category_id)
                Product.objects.create(
                    farmer=farmer_profile,
                    category=category,
                    name=name,
                    description=description,
                    price_per_unit=price_per_unit,
                    stock_quantity=stock_quantity,
                    unit=unit,
                    image=image
                )
                messages.success(request, "Product added successfully!")
            except Exception as e:
                messages.error(request, f"Error adding product: {str(e)}")
            
            return redirect('farmer_dashboard_view')

    products = Product.objects.select_related('category').filter(farmer=farmer_profile).order_by('-created_at')
    categories = Category.objects.all()

    stats = products.aggregate(
        in_stock=Count('product_id', filter=Q(stock_quantity__gt=0)),
        out_stock=Count('product_id', filter=Q(stock_quantity=0))
    )
    in_stock_count = stats['in_stock'] or 0
    out_of_stock_count = stats['out_stock'] or 0

    # Orders & Logistics fetching
    orders = Order.objects.filter(farmer=farmer_profile).prefetch_related('items__product', 'logistic', 'buyer__user').order_by('-created_at')
    logistics = Logistic.objects.all()

    # Active tab is driven by the URL query param
    active_tab = request.GET.get('tab', 'dashboard')
    valid_tabs = ['dashboard', 'orders']
    if active_tab not in valid_tabs:
        active_tab = 'dashboard'

    context = {
        'products': products,
        'categories': categories,
        'in_stock_count': in_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'orders': orders,
        'logistics': logistics,
        'active_tab': active_tab,
    }
    return render(request, "F2M/farmer_dashboard.html", context)


@login_required
def farmer_order_action_view(request, order_id):
    if request.method != "POST" or not hasattr(request.user, 'profile') or request.user.profile.role != 'farmer':
        return redirect('home_view')
        
    farmer_profile = request.user.profile
    try:
        order = Order.objects.get(order_id=order_id, farmer=farmer_profile)
    except Order.DoesNotExist:
        messages.error(request, "Order not found.")
        return redirect('farmer_dashboard_view')
        
    action = request.POST.get('action')
    if action == 'confirm' and order.status == 'PENDING':
        order.status = 'CONFIRMED'
        order.save()
        Notification.objects.create(
            recipient=order.buyer,
            order=order,
            message=f"Your order #{order.order_id} has been confirmed by {farmer_profile.farm_name}!"
        )
        messages.success(request, f"Order #{order.order_id} confirmed.")
    elif action == 'reject' and order.status == 'PENDING':
        order.status = 'REJECTED'
        order.save()
        # Restore stock
        for item in order.items.all():
            item.product.stock_quantity += item.quantity
            item.product.save()
        Notification.objects.create(
            recipient=order.buyer,
            order=order,
            message=f"Unfortunately, {farmer_profile.farm_name} could not fulfill your order #{order.order_id}."
        )
        messages.success(request, f"Order #{order.order_id} rejected.")
    elif action == 'assign_logistic' and order.status == 'CONFIRMED':
        logistic_id = request.POST.get('logistic_id')
        if logistic_id:
            try:
                logistic = Logistic.objects.get(id=logistic_id)
                order.logistic = logistic
                order.status = 'ASSIGNED'
                order.save()
                Notification.objects.create(
                    recipient=order.buyer,
                    order=order,
                    message=f"Logistic service ({logistic.name}) has been assigned to your order #{order.order_id}."
                )
                messages.success(request, f"Logistic {logistic.name} assigned to order #{order.order_id}.")
            except Logistic.DoesNotExist:
                messages.error(request, "Logistic not found.")
    elif action == 'mark_dispatched' and order.status == 'ASSIGNED':
        order.status = 'OUT_FOR_DELIVERY'
        order.save()
        Notification.objects.create(
            recipient=order.buyer,
            order=order,
            message=f"Your order #{order.order_id} is on the way! 🚚"
        )
        messages.success(request, f"Order #{order.order_id} marked as Out for Delivery.")
    elif action == 'mark_delivered' and order.status == 'OUT_FOR_DELIVERY':
        order.status = 'DELIVERED'
        order.save()
        Notification.objects.create(
            recipient=order.buyer,
            order=order,
            message=f"Your order #{order.order_id} has been delivered. Please confirm receipt."
        )
        messages.success(request, f"Order #{order.order_id} marked as Delivered.")
        
    return redirect('/farmer/dashboard/?tab=orders')


# BUYER
@login_required
def buyer_dashboard_view(request):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'buyer':
        messages.error(request, "Only buyers can access the dashboard.")
        return redirect('home_view')
        
    buyer_profile = request.user.profile
    buyer_orders = Order.objects.filter(buyer=buyer_profile).prefetch_related('items__product', 'farmer').order_by('-created_at')
    
    # Calculate stats
    stats = buyer_orders.aggregate(
        total_orders=Count('order_id'),
        completed=Count('order_id', filter=Q(status='COMPLETED'))
    )
    total_orders = stats['total_orders'] or 0
    completed_orders = stats['completed'] or 0
    
    # Optional logic for total spent:
    total_spent = 0
    for order in buyer_orders.filter(status='COMPLETED'):
        for item in order.items.all():
            total_spent += item.subtotal()
            
    active_tab = request.GET.get('tab', 'overview')
    valid_tabs = ['overview', 'orders']
    if active_tab not in valid_tabs:
        active_tab = 'overview'
        
    context = {
        'buyer_orders': buyer_orders,
        'total_orders': total_orders,
        'completed_orders': completed_orders,
        'total_spent': total_spent,
        'active_tab': active_tab,
    }
    return render(request, "F2M/buyer_dashboard.html", context)


@login_required
def buyer_order_action_view(request, order_id):
    if request.method != "POST" or not hasattr(request.user, 'profile') or request.user.profile.role != 'buyer':
        return redirect('home_view')
        
    buyer_profile = request.user.profile
    try:
        order = Order.objects.get(order_id=order_id, buyer=buyer_profile)
    except Order.DoesNotExist:
        messages.error(request, "Order not found.")
        return redirect('/buyer/dashboard/?tab=orders')
        
    action = request.POST.get('action')
    if action == 'cancel' and order.status == 'PENDING':
        order.status = 'CANCELLED'
        order.save()
        # Restore stock
        for item in order.items.all():
            item.product.stock_quantity += item.quantity
            item.product.save()
        Notification.objects.create(
            recipient=order.farmer,
            order=order,
            message=f"{buyer_profile.user.username} cancelled their order #{order.order_id}."
        )
        messages.success(request, f"Order #{order.order_id} cancelled successfully.")
        return redirect('/buyer/dashboard/?tab=orders#orders')
    elif action == 'confirm_receipt' and order.status == 'DELIVERED':
        order.status = 'COMPLETED'
        order.save()
        Notification.objects.create(
            recipient=order.farmer,
            order=order,
            message=f"Order #{order.order_id} has been marked as received. ✅"
        )
        messages.success(request, f"Order #{order.order_id} marked as completed.")
        return redirect('/buyer/dashboard/?tab=orders#orders')

    return redirect('/buyer/dashboard/?tab=orders#orders')


# CART & CHECKOUT VIEWS
def cart_view(request):
    if request.user.is_authenticated:
        if not hasattr(request.user, 'profile') or request.user.profile.role != 'buyer':
            messages.error(request, "Only buyers can access the cart.")
            return redirect('home_view')
        buyer_profile = request.user.profile

        cart, created = Cart.objects.get_or_create(buyer=buyer_profile)
        cart_items = cart.items.select_related('product', 'product__farmer').all()
        total_price = sum(item.subtotal() for item in cart_items)
        
        context = {
            'cart_items': cart_items,
            'total_price': total_price
        }
    else:
        # Handle session-based cart for anonymous users
        session_cart = request.session.get('cart', {})
        cart_items = []
        total_price = 0
        
        for product_id, quantity in session_cart.items():
            try:
                product = Product.objects.select_related('farmer').get(product_id=product_id)
                subtotal = product.price_per_unit * quantity
                total_price += subtotal
                cart_items.append({
                    'product': product,
                    'quantity': quantity,
                    'subtotal': subtotal,
                    'is_session': True,
                    'cart_item_id': product_id  # Use product_id as item_id for sessions
                })
            except Product.DoesNotExist:
                continue
        
        context = {
            'cart_items': cart_items,
            'total_price': total_price,
            'is_anonymous': True
        }
        
    return render(request, "F2M/cart.html", context)


def add_to_cart_view(request, product_id):
    if request.method != "POST":
        return redirect('product_list_view')
        
    try:
        product = Product.objects.get(product_id=product_id)
    except Product.DoesNotExist:
        messages.error(request, "Product not found.")
        return redirect('product_list_view')

    if product.stock_quantity <= 0:
        messages.error(request, f"Sorry, {product.name} is out of stock.")
        return redirect('product_list_view')

    if request.user.is_authenticated:
        if not hasattr(request.user, 'profile') or request.user.profile.role != 'buyer':
            messages.error(request, "Please create a buyer account to add items to cart.")
            return redirect('product_list_view')
        buyer_profile = request.user.profile

        cart, created = Cart.objects.get_or_create(buyer=buyer_profile)
        cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)

        if not item_created:
            if cart_item.quantity < product.stock_quantity:
                cart_item.quantity += 1
                cart_item.save()
                messages.success(request, f"Added another {product.name} to your cart.")
            else:
                messages.warning(request, f"Not enough stock to add more {product.name}.")
        else:
            messages.success(request, f"{product.name} added to your cart.")
    else:
        # Session-based cart for anonymous users
        cart = request.session.get('cart', {})
        product_id_str = str(product_id)
        
        if product_id_str in cart:
            if cart[product_id_str] < product.stock_quantity:
                cart[product_id_str] += 1
                messages.success(request, f"Added another {product.name} to your cart.")
            else:
                messages.warning(request, f"Not enough stock to add more {product.name}.")
        else:
            cart[product_id_str] = 1
            messages.success(request, f"{product.name} added to your cart.")
            
        request.session['cart'] = cart
        request.session.modified = True

    return redirect('product_list_view')


def update_cart_view(request, item_id):
    if request.method == "POST":
        action = request.POST.get('action')
        
        if request.user.is_authenticated:
            if not hasattr(request.user, 'profile') or request.user.profile.role != 'buyer':
                messages.error(request, "Item not found in your cart.")
                return redirect('cart_view')
            buyer_profile = request.user.profile
            try:
                cart_item = CartItem.objects.get(cart_item_id=item_id, cart__buyer=buyer_profile)
            except CartItem.DoesNotExist:
                messages.error(request, "Item not found in your cart.")
                return redirect('cart_view')

            if action == 'increase':
                if cart_item.quantity < cart_item.product.stock_quantity:
                    cart_item.quantity += 1
                    cart_item.save()
                else:
                    messages.warning(request, f"Not enough stock to add more {cart_item.product.name}.")
            elif action == 'decrease':
                if cart_item.quantity > 1:
                    cart_item.quantity -= 1
                    cart_item.save()
                else:
                    cart_item.delete()
                    messages.success(request, f"{cart_item.product.name} removed from cart.")
            elif action == 'remove':
                cart_item.delete()
                messages.success(request, f"{cart_item.product.name} removed from cart.")
        else:
            # Session-based cart update
            cart = request.session.get('cart', {})
            product_id = str(item_id)
            
            if product_id in cart:
                try:
                    product = Product.objects.get(product_id=product_id)
                    if action == 'increase':
                        if cart[product_id] < product.stock_quantity:
                            cart[product_id] += 1
                        else:
                            messages.warning(request, f"Not enough stock to add more {product.name}.")
                    elif action == 'decrease':
                        if cart[product_id] > 1:
                            cart[product_id] -= 1
                        else:
                            del cart[product_id]
                            messages.success(request, f"{product.name} removed from cart.")
                    elif action == 'remove':
                        del cart[product_id]
                        messages.success(request, f"{product.name} removed from cart.")
                except Product.DoesNotExist:
                    if product_id in cart: del cart[product_id]
            
            request.session['cart'] = cart
            request.session.modified = True
            
    return redirect('cart_view')


@login_required
def checkout_view(request):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'buyer':
        messages.error(request, "Only buyers can proceed to checkout.")
        return redirect('home_view')
        
    buyer_profile = request.user.profile
    try:
        cart = Cart.objects.get(buyer=buyer_profile)
        cart_items = cart.items.select_related('product__farmer').all()
    except Cart.DoesNotExist:
        cart_items = []
        
    if not cart_items:
        messages.error(request, "Your cart is empty.")
        return redirect('cart_view')
        
    # Validate stock before proceeding
    for item in cart_items:
        if item.quantity > item.product.stock_quantity:
            messages.error(request, f"Sorry, only {item.product.stock_quantity} left in stock for {item.product.name}.")
            return redirect('cart_view')
            
    # Group items by farmer
    items_by_farmer = {}
    for item in cart_items:
        farmer = item.product.farmer
        if farmer not in items_by_farmer:
            items_by_farmer[farmer] = []
        items_by_farmer[farmer].append(item)
        
    # Create Order for each farmer
    for farmer, items in items_by_farmer.items():
        order = Order.objects.create(
            buyer=buyer_profile,
            farmer=farmer,
            status='PENDING'
        )
        for item in items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price_at_order=item.product.price_per_unit
            )
            # Decrease stock
            item.product.stock_quantity -= item.quantity
            item.product.save()
            
        Notification.objects.create(
            recipient=farmer,
            order=order,
            message=f"New order #{order.order_id} from {buyer_profile.user.username}"
        )
        
    # Clear cart
    cart.items.all().delete()
    
    messages.success(request, "Checkout successful! Your orders have been placed.")
    return redirect('/buyer/dashboard/?tab=orders#orders')




