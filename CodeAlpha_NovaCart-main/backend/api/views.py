import json
import random
import string
import datetime
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from utils.firebase_helpers import get_firestore_client, verify_firebase_token
from utils.invoice_generator import generate_invoice_html

def get_auth_user(request):
    """Helper to authenticate requests using Authorization Bearer token"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    token = auth_header.split('Bearer ')[1]
    return verify_firebase_token(token)

@csrf_exempt
def verify_token_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    user = get_auth_user(request)
    if not user:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    db = get_firestore_client()
    uid = user['uid']
    user_ref = db.collection('users').document(uid)
    user_doc = user_ref.get()
    
    user_data = {
        'uid': uid,
        'email': user['email'],
        'displayName': user.get('name', user['email'].split('@')[0].capitalize()),
        'photoURL': user.get('picture', '/static/images/placeholder.svg'),
        'updatedAt': datetime.datetime.now().isoformat()
    }
    
    if not user_doc.exists:
        user_data['role'] = user.get('role', 'user')
        user_data['createdAt'] = datetime.datetime.now().isoformat()
        user_ref.set(user_data)
    else:
        existing = user_doc.to_dict()
        user_data['role'] = existing.get('role', 'user')
        user_ref.update(user_data)
        
    return JsonResponse({'status': 'success', 'user': user_data})

# GET /api/categories/
def get_categories_api(request):
    db = get_firestore_client()
    stream = db.collection('categories').stream()
    categories = [doc.to_dict() for doc in stream]
    return JsonResponse({'categories': categories})

# GET /api/products/
def get_products_api(request):
    db = get_firestore_client()
    stream = db.collection('products').stream()
    products = []
    for doc in stream:
        p = doc.to_dict()
        p['productId'] = doc.id
        products.append(p)
        
    # Get parameters
    search = request.GET.get('search', '').strip().lower()
    category = request.GET.get('category', '').strip()
    brand = request.GET.get('brand', '').strip().lower()
    min_price = request.GET.get('minPrice')
    max_price = request.GET.get('maxPrice')
    rating = request.GET.get('rating')
    sort_by = request.GET.get('sortBy', 'newest') # price-asc, price-desc, rating-desc, newest
    featured = request.GET.get('featured') # true/false
    bestseller = request.GET.get('bestseller') # true/false
    latest = request.GET.get('latest') # true/false
    
    # Filter
    filtered_products = []
    for p in products:
        # Search
        if search and search not in p.get('name', '').lower() and search not in p.get('brand', '').lower() and search not in p.get('description', '').lower():
            continue
        # Category
        if category and p.get('category') != category:
            continue
        # Brand
        if brand and p.get('brand', '').lower() != brand:
            continue
        # Price range
        disc_price = p.get('price', 0.0) * (1 - p.get('discount', 0.0) / 100.0)
        if min_price:
            try:
                if disc_price < float(min_price):
                    continue
            except ValueError:
                pass
        if max_price:
            try:
                if disc_price > float(max_price):
                    continue
            except ValueError:
                pass
        # Rating
        if rating:
            try:
                if p.get('rating', 0.0) < float(rating):
                    continue
            except ValueError:
                pass
        # Special flags
        if featured == 'true' and not p.get('isFeatured'):
            continue
        if bestseller == 'true' and not p.get('isBestSeller'):
            continue
        if latest == 'true' and not p.get('isLatest'):
            continue
            
        filtered_products.append(p)

    # Sort
    if sort_by == 'price-asc':
        filtered_products.sort(key=lambda x: x.get('price', 0.0) * (1 - x.get('discount', 0.0)/100.0))
    elif sort_by == 'price-desc':
        filtered_products.sort(key=lambda x: x.get('price', 0.0) * (1 - x.get('discount', 0.0)/100.0), reverse=True)
    elif sort_by == 'rating-desc':
        filtered_products.sort(key=lambda x: float(x.get('rating', 0.0)), reverse=True)
    else: # newest
        # parse date
        filtered_products.sort(key=lambda x: x.get('createdAt', ''), reverse=True)

    # Pagination parameters
    try:
        page = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit', 12))
    except ValueError:
        page = 1
        limit = 12

    total_count = len(filtered_products)
    start = (page - 1) * limit
    end = start + limit
    
    paginated_products = filtered_products[start:end]
    
    return JsonResponse({
        'products': paginated_products,
        'page': page,
        'limit': limit,
        'total': total_count,
        'pages': (total_count + limit - 1) // limit
    })

# GET/POST /api/reviews/
@csrf_exempt
def reviews_api(request):
    db = get_firestore_client()
    
    if request.method == 'GET':
        product_id = request.GET.get('productId')
        if not product_id:
            return JsonResponse({'error': 'productId parameter is required'}, status=400)
            
        stream = db.collection('reviews').stream()
        reviews = []
        for doc in stream:
            r = doc.to_dict()
            if r.get('productId') == product_id:
                r['reviewId'] = doc.id
                reviews.append(r)
                
        # Sort reviews newest first
        reviews.sort(key=lambda x: x.get('createdAt', ''), reverse=True)
        return JsonResponse({'reviews': reviews})
        
    elif request.method == 'POST':
        user = get_auth_user(request)
        if not user:
            return JsonResponse({'error': 'Unauthorized'}, status=401)
            
        try:
            data = json.loads(request.body)
            product_id = data.get('productId')
            rating = int(data.get('rating', 5))
            comment = data.get('comment', '').strip()
        except (ValueError, TypeError, json.JSONDecodeError):
            return JsonResponse({'error': 'Invalid request body'}, status=400)
            
        if not product_id:
            return JsonResponse({'error': 'productId is required'}, status=400)
            
        # Check if product exists
        prod_ref = db.collection('products').document(product_id)
        prod_doc = prod_ref.get()
        if not prod_doc.exists:
            return JsonResponse({'error': 'Product not found'}, status=404)
            
        # Add new review
        review_id = f"rev_{int(datetime.datetime.now().timestamp())}"
        review_data = {
            'reviewId': review_id,
            'productId': product_id,
            'userId': user['uid'],
            'userName': user.get('name', user['email'].split('@')[0].capitalize()),
            'userPhoto': user.get('picture', '/static/images/placeholder.svg'),
            'rating': rating,
            'comment': comment,
            'createdAt': datetime.datetime.now().isoformat()
        }
        
        db.collection('reviews').document(review_id).set(review_data)
        
        # Re-calculate average rating for product
        stream = db.collection('reviews').stream()
        all_ratings = [doc.to_dict().get('rating', 5) for doc in stream if doc.to_dict().get('productId') == product_id]
        avg_rating = round(sum(all_ratings) / len(all_ratings), 1) if all_ratings else rating
        
        prod_ref.update({
            'rating': avg_rating,
            'reviewCount': len(all_ratings)
        })
        
        return JsonResponse({'status': 'success', 'review': review_data})

    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def review_delete_api(request, review_id):
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    user = get_auth_user(request)
    if not user:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
        
    db = get_firestore_client()
    review_ref = db.collection('reviews').document(review_id)
    review_doc = review_ref.get()
    
    if not review_doc.exists:
        return JsonResponse({'error': 'Review not found'}, status=404)
        
    r_data = review_doc.to_dict()
    # Security: User must own the review or be admin
    if r_data.get('userId') != user['uid'] and user.get('role') != 'admin':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    product_id = r_data.get('productId')
    review_ref.delete()
    
    # Recalculate product rating
    prod_ref = db.collection('products').document(product_id)
    stream = db.collection('reviews').stream()
    all_ratings = [doc.to_dict().get('rating', 5) for doc in stream if doc.to_dict().get('productId') == product_id]
    avg_rating = round(sum(all_ratings) / len(all_ratings), 1) if all_ratings else 5.0
    
    prod_ref.update({
        'rating': avg_rating,
        'reviewCount': len(all_ratings)
    })
    
    return JsonResponse({'status': 'success', 'message': 'Review deleted successfully'})

@csrf_exempt
def validate_coupon_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        code = data.get('code', '').strip().upper()
        subtotal = float(data.get('subtotal', 0))
    except (ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse({'error': 'Invalid request body'}, status=400)
    
    db = get_firestore_client()
    coupons = db.collection('coupons').stream()
    
    coupon = None
    for doc in coupons:
        c_data = doc.to_dict()
        if c_data.get('code', '').upper() == code:
            coupon = c_data
            break
            
    if not coupon:
        return JsonResponse({'valid': False, 'message': 'Coupon code does not exist'}, status=200)
        
    if not coupon.get('isActive', True):
        return JsonResponse({'valid': False, 'message': 'Coupon is inactive'}, status=200)
        
    expiry = coupon.get('expiryDate')
    if expiry:
        if isinstance(expiry, str):
            try:
                expiry_dt = datetime.datetime.fromisoformat(expiry.replace('Z', '+00:00'))
                if expiry_dt.timestamp() < datetime.datetime.now().timestamp():
                    return JsonResponse({'valid': False, 'message': 'Coupon has expired'}, status=200)
            except ValueError:
                pass
                
    min_order = float(coupon.get('minOrder', 0))
    if subtotal < min_order:
        return JsonResponse({'valid': False, 'message': f'Minimum order subtotal of ${min_order:.2f} required'}, status=200)
        
    return JsonResponse({
        'valid': True,
        'code': coupon['code'],
        'type': coupon['type'],
        'value': float(coupon['value']),
        'message': 'Coupon applied successfully!'
    })

@csrf_exempt
def checkout_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    user = get_auth_user(request)
    if not user:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
        
    try:
        data = json.loads(request.body)
        items = data.get('items', [])
        shipping_address = data.get('shippingAddress', {})
        billing_address = data.get('billingAddress', shipping_address)
        coupon_code = data.get('couponCode', '').strip().upper()
        payment_method = data.get('paymentMethod', 'cod')
    except (ValueError, json.JSONDecodeError):
        return JsonResponse({'error': 'Invalid request body'}, status=400)
        
    if not items:
        return JsonResponse({'error': 'Cart is empty'}, status=400)
        
    db = get_firestore_client()
    
    subtotal = 0.0
    order_items_to_save = []
    products_to_update = []
    
    for cart_item in items:
        prod_id = cart_item.get('productId')
        qty = int(cart_item.get('quantity', 1))
        
        prod_doc = db.collection('products').document(prod_id).get()
        if not prod_doc.exists:
            return JsonResponse({'error': f'Product {prod_id} not found'}, status=404)
            
        prod_data = prod_doc.to_dict()
        stock = int(prod_data.get('stock', 0))
        if stock < qty:
            return JsonResponse({'error': f'Insufficient stock for product: {prod_data.get("name")}. Available: {stock}'}, status=400)
            
        price = float(prod_data.get('price', 0))
        discount_percent = float(prod_data.get('discount', 0))
        final_price = price * (1 - discount_percent / 100.0)
        
        subtotal += final_price * qty
        
        order_items_to_save.append({
            'productId': prod_id,
            'name': prod_data.get('name'),
            'price': final_price,
            'quantity': qty,
            'image': prod_data.get('images', [''])[0]
        })
        
        products_to_update.append((prod_id, stock - qty))

    discount = 0.0
    if coupon_code:
        coupons = db.collection('coupons').stream()
        coupon = None
        for doc in coupons:
            c_data = doc.to_dict()
            if c_data.get('code', '').upper() == coupon_code:
                coupon = c_data
                break
        if coupon and coupon.get('isActive', True) and subtotal >= float(coupon.get('minOrder', 0)):
            val = float(coupon.get('value', 0))
            if coupon['type'] == 'percentage':
                discount = subtotal * (val / 100.0)
            else:
                discount = val

    shipping_fee = 0.0 if subtotal > 200.0 else 15.00
    tax = (subtotal - discount) * 0.18
    if tax < 0:
        tax = 0.0
        
    total = (subtotal - discount) + shipping_fee + tax
    
    date_str = datetime.datetime.now().strftime('%Y%m%d')
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    order_id = f"NC-{date_str}-{random_str}"
    
    for prod_id, new_stock in products_to_update:
        db.collection('products').document(prod_id).update({'stock': new_stock})
        
    order_doc = {
        'orderId': order_id,
        'userId': user['uid'],
        'email': user['email'],
        'shippingAddress': shipping_address,
        'billingAddress': billing_address,
        'subtotal': subtotal,
        'shippingFee': shipping_fee,
        'tax': tax,
        'discount': discount,
        'total': total,
        'couponCode': coupon_code,
        'paymentMethod': payment_method,
        'paymentStatus': 'completed' if payment_method in ['card', 'upi'] else 'pending',
        'orderStatus': 'Confirmed' if payment_method in ['card', 'upi'] else 'Pending',
        'createdAt': datetime.datetime.now().isoformat(),
        'updatedAt': datetime.datetime.now().isoformat()
    }
    
    db.collection('orders').document(order_id).set(order_doc)
    
    for item in order_items_to_save:
        item['orderId'] = order_id
        db.collection('orderItems').add(item)
        
    db.collection('notifications').add({
        'userId': user['uid'],
        'title': 'Order Placed successfully!',
        'message': f'Your order {order_id} has been received. Thank you for shopping with us!',
        'type': 'order',
        'isRead': False,
        'createdAt': datetime.datetime.now().isoformat()
    })
    
    # Send simulated email
    print("\n" + "="*50)
    print(f"SIMULATED EMAIL NOTIFICATION SENT TO: {user['email']}")
    print(f"Subject: Order Confirmation - {order_id}")
    print(f"Hello, {user.get('name', 'Customer')}, your order for ${total:.2f} has been processed.")
    print("="*50 + "\n")
    
    return JsonResponse({
        'status': 'success',
        'orderId': order_id,
        'total': total
    })

@csrf_exempt
def cancel_order_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    user = get_auth_user(request)
    if not user:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
        
    try:
        data = json.loads(request.body)
        order_id = data.get('orderId')
    except (ValueError, json.JSONDecodeError):
        return JsonResponse({'error': 'Invalid request body'}, status=400)
        
    db = get_firestore_client()
    order_ref = db.collection('orders').document(order_id)
    order_doc = order_ref.get()
    
    if not order_doc.exists:
        return JsonResponse({'error': 'Order not found'}, status=404)
        
    order_data = order_doc.to_dict()
    
    if order_data.get('userId') != user['uid'] and user.get('role') != 'admin':
        return JsonResponse({'error': 'Unauthorized to cancel this order'}, status=403)
        
    current_status = order_data.get('orderStatus')
    if current_status not in ['Pending', 'Confirmed']:
        return JsonResponse({'error': f'Order cannot be cancelled. Current status is {current_status}'}, status=400)
        
    order_ref.update({
        'orderStatus': 'Cancelled',
        'updatedAt': datetime.datetime.now().isoformat()
    })
    
    order_items = db.collection('orderItems').stream()
    for item in order_items:
        it_data = item.to_dict()
        if it_data.get('orderId') == order_id:
            prod_id = it_data.get('productId')
            qty = int(it_data.get('quantity', 0))
            
            prod_ref = db.collection('products').document(prod_id)
            p_doc = prod_ref.get()
            if p_doc.exists:
                p_data = p_doc.to_dict()
                new_stock = int(p_data.get('stock', 0)) + qty
                prod_ref.update({'stock': new_stock})
                
    db.collection('notifications').add({
        'userId': order_data.get('userId'),
        'title': 'Order Cancelled',
        'message': f'Your order {order_id} has been cancelled successfully.',
        'type': 'order',
        'isRead': False,
        'createdAt': datetime.datetime.now().isoformat()
    })
    
    return JsonResponse({'status': 'success', 'message': f'Order {order_id} was successfully cancelled.'})

def download_invoice_api(request, order_id):
    db = get_firestore_client()
    order_doc = db.collection('orders').document(order_id).get()
    
    if not order_doc.exists:
        return HttpResponse("<h1>Order Not Found</h1>", status=404)
        
    order = order_doc.to_dict()
    
    items_stream = db.collection('orderItems').stream()
    items = []
    for doc in items_stream:
        i_data = doc.to_dict()
        if i_data.get('orderId') == order_id:
            items.append(i_data)
            
    html_content = generate_invoice_html(order, items)
    
    response = HttpResponse(html_content, content_type='text/html')
    response['Content-Disposition'] = f'inline; filename="invoice_{order_id}.html"'
    return response

def get_recommendations_api(request):
    user = get_auth_user(request)
    db = get_firestore_client()
    
    products_stream = db.collection('products').stream()
    all_products = []
    for doc in products_stream:
        p = doc.to_dict()
        p['productId'] = doc.id
        all_products.append(p)
        
    if not all_products:
        return JsonResponse({'recommendations': []})
        
    purchased_categories = set()
    if user:
        orders_stream = db.collection('orders').stream()
        user_orders = [doc.to_dict() for doc in orders_stream if doc.to_dict().get('userId') == user['uid']]
        
        if user_orders:
            order_ids = [o.get('orderId') for o in user_orders]
            items_stream = db.collection('orderItems').stream()
            for doc in items_stream:
                item = doc.to_dict()
                if item.get('orderId') in order_ids:
                    prod_id = item.get('productId')
                    product = next((p for p in all_products if p['productId'] == prod_id), None)
                    if product and product.get('category'):
                        purchased_categories.add(product.get('category'))
                        
    recommended = []
    if purchased_categories:
        recommended = [p for p in all_products if p.get('category') in purchased_categories]
        recommended.sort(key=lambda x: float(x.get('rating', 0)), reverse=True)
        
    if len(recommended) < 6:
        fallbacks = [p for p in all_products if p.get('isBestSeller') or p.get('isFeatured') or float(p.get('rating', 0)) >= 4.5]
        for f in fallbacks:
            if f not in recommended and f['productId'] not in [r['productId'] for r in recommended]:
                recommended.append(f)
                
    return JsonResponse({'recommendations': recommended[:6]})

@csrf_exempt
def submit_contact_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        subject = data.get('subject', '').strip()
        message = data.get('message', '').strip()
    except (ValueError, json.JSONDecodeError):
        return JsonResponse({'error': 'Invalid request body'}, status=400)
        
    if not name or not email or not message:
        return JsonResponse({'error': 'Please fill all required fields'}, status=400)
        
    db = get_firestore_client()
    db.collection('contactSubmissions').add({
        'name': name,
        'email': email,
        'subject': subject,
        'message': message,
        'createdAt': datetime.datetime.now().isoformat()
    })
    
    print("\n" + "="*50)
    print(f"CONTACT QUERY SUBMISSION RECEIVED")
    print(f"From: {name} <{email}>")
    print(f"Subject: {subject}")
    print(f"Message: {message}")
    print("="*50 + "\n")
    
    return JsonResponse({'status': 'success', 'message': 'Thank you! Your message has been sent successfully.'})

# Admin CRUD APIs
@csrf_exempt
def admin_products_api(request, product_id=None):
    user = get_auth_user(request)
    if not user or user.get('role') != 'admin':
        return JsonResponse({'error': 'Unauthorized admin access'}, status=403)
        
    db = get_firestore_client()
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            prod_id = data.get('productId', f"prod_{int(datetime.datetime.now().timestamp())}")
            p_data = {
                'productId': prod_id,
                'name': data.get('name'),
                'category': data.get('category'),
                'price': float(data.get('price', 0.0)),
                'discount': float(data.get('discount', 0.0)),
                'images': data.get('images', ['/static/images/placeholder.svg']),
                'brand': data.get('brand', 'Generic'),
                'rating': float(data.get('rating', 5.0)),
                'reviewCount': int(data.get('reviewCount', 0)),
                'stock': int(data.get('stock', 0)),
                'specs': data.get('specs', {}),
                'isFeatured': bool(data.get('isFeatured', False)),
                'isBestSeller': bool(data.get('isBestSeller', False)),
                'isLatest': bool(data.get('isLatest', True)),
                'flashSale': data.get('flashSale'),
                'createdAt': datetime.datetime.now().isoformat()
            }
            db.collection('products').document(prod_id).set(p_data)
            return JsonResponse({'status': 'success', 'product': p_data})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
            
    elif request.method == 'PUT':
        if not product_id:
            return JsonResponse({'error': 'productId is required'}, status=400)
        try:
            data = json.loads(request.body)
            # Update fields
            prod_ref = db.collection('products').document(product_id)
            if not prod_ref.get().exists:
                return JsonResponse({'error': 'Product not found'}, status=404)
                
            updates = {}
            for field in ['name', 'category', 'price', 'discount', 'images', 'brand', 'stock', 'specs', 'isFeatured', 'isBestSeller', 'isLatest', 'flashSale']:
                if field in data:
                    if field == 'price' or field == 'discount':
                        updates[field] = float(data[field])
                    elif field == 'stock':
                        updates[field] = int(data[field])
                    else:
                        updates[field] = data[field]
                        
            prod_ref.update(updates)
            return JsonResponse({'status': 'success', 'message': 'Product updated successfully'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
            
    elif request.method == 'DELETE':
        if not product_id:
            return JsonResponse({'error': 'productId is required'}, status=400)
        prod_ref = db.collection('products').document(product_id)
        if not prod_ref.get().exists:
            return JsonResponse({'error': 'Product not found'}, status=404)
        prod_ref.delete()
        return JsonResponse({'status': 'success', 'message': 'Product deleted successfully'})
        
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def admin_orders_api(request, order_id=None):
    user = get_auth_user(request)
    if not user:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
        
    db = get_firestore_client()
    
    if request.method == 'GET':
        stream = db.collection('orders').stream()
        orders = [doc.to_dict() for doc in stream]
        orders.sort(key=lambda x: x.get('createdAt', ''), reverse=True)
        # Filter orders if not admin
        if user.get('role') != 'admin':
            orders = [o for o in orders if o.get('userId') == user['uid']]
        return JsonResponse({'orders': orders})
        
    elif request.method == 'PUT':
        if user.get('role') != 'admin':
            return JsonResponse({'error': 'Unauthorized admin access'}, status=403)
        if not order_id:
            return JsonResponse({'error': 'orderId is required'}, status=400)
        try:
            data = json.loads(request.body)
            status = data.get('orderStatus')
            if status not in ['Pending', 'Confirmed', 'Packed', 'Shipped', 'Delivered', 'Cancelled']:
                return JsonResponse({'error': 'Invalid status'}, status=400)
                
            order_ref = db.collection('orders').document(order_id)
            if not order_ref.get().exists:
                return JsonResponse({'error': 'Order not found'}, status=404)
                
            order_ref.update({
                'orderStatus': status,
                'updatedAt': datetime.datetime.now().isoformat()
            })
            return JsonResponse({'status': 'success', 'message': f'Order status updated to {status}'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

            
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def admin_users_api(request, uid=None):
    user = get_auth_user(request)
    if not user or user.get('role') != 'admin':
        return JsonResponse({'error': 'Unauthorized admin access'}, status=403)
        
    db = get_firestore_client()
    
    if request.method == 'GET':
        stream = db.collection('users').stream()
        users = [doc.to_dict() for doc in stream]
        return JsonResponse({'users': users})
        
    elif request.method == 'PUT':
        if not uid:
            return JsonResponse({'error': 'uid is required'}, status=400)
        try:
            data = json.loads(request.body)
            status = data.get('status')
            role = data.get('role')
            
            user_ref = db.collection('users').document(uid)
            if not user_ref.get().exists:
                return JsonResponse({'error': 'User not found'}, status=404)
                
            updates = {}
            if status:
                updates['status'] = status
            if role:
                updates['role'] = role
                
            if updates:
                user_ref.update(updates)
            return JsonResponse({'status': 'success', 'message': 'User details updated'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
            
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def admin_analytics_api(request):
    user = get_auth_user(request)
    if not user or user.get('role') != 'admin':
        return JsonResponse({'error': 'Unauthorized admin access'}, status=403)
        
    db = get_firestore_client()
    
    orders = [doc.to_dict() for doc in db.collection('orders').stream()]
    products = [doc.to_dict() for doc in db.collection('products').stream()]
    users = [doc.to_dict() for doc in db.collection('users').stream()]
    
    total_revenue = sum(float(o.get('total', 0.0)) for o in orders if o.get('orderStatus') != 'Cancelled')
    total_sales = len([o for o in orders if o.get('orderStatus') != 'Cancelled'])
    
    low_stock = [p for p in products if int(p.get('stock', 0)) <= 5]
    
    # Prepare sales summary by date (last 7 days)
    sales_by_date = {}
    for o in orders:
        if o.get('orderStatus') == 'Cancelled':
            continue
        date_str = o.get('createdAt', '')[:10]
        if date_str:
            sales_by_date[date_str] = sales_by_date.get(date_str, 0.0) + float(o.get('total', 0.0))
            
    sorted_sales = sorted(sales_by_date.items())[-7:]
    
    return JsonResponse({
        'analytics': {
            'totalRevenue': total_revenue,
            'totalSales': total_sales,
            'totalUsers': len(users),
            'totalProducts': len(products),
            'lowStockAlerts': len(low_stock),
            'lowStockProducts': low_stock,
            'recentSalesChart': {
                'labels': [x[0] for x in sorted_sales],
                'data': [x[1] for x in sorted_sales]
            }
        }
    })
