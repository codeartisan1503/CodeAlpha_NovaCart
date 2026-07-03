import os
import sys
import random
import datetime

# Add backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Initialize Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
import django
django.setup()

from utils.firebase_helpers import get_firestore_client

def seed_db():
    print("Initializing Database Client...")
    db = get_firestore_client()
    
    # Check if we are running in mock mode or real firestore
    is_mock = hasattr(db, 'filepath')
    if is_mock:
        print(f"Seeding local Mock Database at: {db.filepath}")
        # Clear mock db completely for clean seeding
        db._write_db({})
    else:
        print("Seeding REAL Firebase Firestore Database...")

    # 1. Seed Categories (10 categories)
    print("Seeding Categories...")
    categories_data = [
        {"categoryId": "electronics", "name": "Electronics", "slug": "electronics", "image": "https://images.unsplash.com/photo-1526738549149-8e07eca6c147?w=500&auto=format&fit=crop"},
        {"categoryId": "fashion", "name": "Fashion", "slug": "fashion", "image": "https://images.unsplash.com/photo-1483985988355-763728e1935b?w=500&auto=format&fit=crop"},
        {"categoryId": "shoes", "name": "Shoes", "slug": "shoes", "image": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=500&auto=format&fit=crop"},
        {"categoryId": "watches", "name": "Watches", "slug": "watches", "image": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500&auto=format&fit=crop"},
        {"categoryId": "furniture", "name": "Furniture", "slug": "furniture", "image": "https://images.unsplash.com/photo-1524758631624-e2822e304c36?w=500&auto=format&fit=crop"},
        {"categoryId": "beauty", "name": "Beauty", "slug": "beauty", "image": "https://images.unsplash.com/photo-1596462502278-27bfdc403348?w=500&auto=format&fit=crop"},
        {"categoryId": "grocery", "name": "Grocery", "slug": "grocery", "image": "https://images.unsplash.com/photo-1542838132-92c53300491e?w=500&auto=format&fit=crop"},
        {"categoryId": "sports", "name": "Sports", "slug": "sports", "image": "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=500&auto=format&fit=crop"},
        {"categoryId": "books", "name": "Books", "slug": "books", "image": "https://images.unsplash.com/photo-1497633762265-9d179a990aa6?w=500&auto=format&fit=crop"},
        {"categoryId": "decor", "name": "Home Decor", "slug": "decor", "image": "https://images.unsplash.com/photo-1513519245088-0e12902e5a38?w=500&auto=format&fit=crop"}
    ]
    for cat in categories_data:
        db.collection('categories').document(cat['categoryId']).set(cat)

    # 2. Seed Coupons
    print("Seeding Coupons...")
    coupons_data = [
        {"code": "WELCOME10", "type": "percentage", "value": 10.0, "minOrder": 50.0, "isActive": True, "expiryDate": (datetime.datetime.now() + datetime.timedelta(days=30)).isoformat()},
        {"code": "FLASH25", "type": "percentage", "value": 25.0, "minOrder": 150.0, "isActive": True, "expiryDate": (datetime.datetime.now() + datetime.timedelta(days=5)).isoformat()},
        {"code": "FLAT50", "type": "flat", "value": 50.0, "minOrder": 300.0, "isActive": True, "expiryDate": (datetime.datetime.now() + datetime.timedelta(days=15)).isoformat()},
        {"code": "FREESHIP", "type": "flat", "value": 15.0, "minOrder": 100.0, "isActive": True, "expiryDate": (datetime.datetime.now() + datetime.timedelta(days=10)).isoformat()}
    ]
    for coup in coupons_data:
        db.collection('coupons').document(coup['code']).set(coup)

    # 3. Seed Users (20 users: 1 Admin, 19 Regular Users)
    print("Seeding Users...")
    users_data = []
    
    # Add Admin User
    admin_uid = "admin_uid_xyz"
    admin_user = {
        "uid": admin_uid,
        "email": "admin@novacart.com",
        "displayName": "NovaCart Admin",
        "photoURL": "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150&auto=format&fit=crop",
        "role": "admin",
        "status": "active",
        "createdAt": datetime.datetime.now().isoformat(),
        "updatedAt": datetime.datetime.now().isoformat()
    }
    db.collection('users').document(admin_uid).set(admin_user)
    users_data.append(admin_user)

    first_names = ["John", "Emily", "Michael", "Sarah", "David", "Jessica", "James", "Ashley", "Robert", "Amanda", "William", "Megan", "Joseph", "Elizabeth", "Thomas", "Lauren", "Charles", "Stephanie", "Daniel"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson"]

    for i in range(1, 20):
        uid = f"user_uid_{i}"
        fname = first_names[i-1]
        lname = last_names[i-1]
        user_doc = {
            "uid": uid,
            "email": f"{fname.lower()}.{lname.lower()}@example.com",
            "displayName": f"{fname} {lname}",
            "photoURL": f"https://images.unsplash.com/photo-{1500000000000 + i*10000}?w=150&auto=format&fit=crop",
            "role": "user",
            "status": "active",
            "createdAt": (datetime.datetime.now() - datetime.timedelta(days=random.randint(10, 100))).isoformat(),
            "updatedAt": datetime.datetime.now().isoformat()
        }
        db.collection('users').document(uid).set(user_doc)
        users_data.append(user_doc)

    # 4. Seed Products (50 items across categories)
    print("Seeding Products...")
    product_catalogue = [
        # Electronics
        ("iPhone 15 Pro", "electronics", 999.00, 5, ["https://images.unsplash.com/photo-1510557880182-3d4d3cba35a5?w=500&auto=format&fit=crop", "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=500&auto=format&fit=crop"], "Apple", {"Screen": "6.1 inches OLED", "Camera": "48MP Triple", "Processor": "A17 Pro", "Battery": "3274 mAh"}),
        ("Samsung Galaxy S24 Ultra", "electronics", 1299.00, 10, ["https://images.unsplash.com/photo-1610945265064-0e34e5519bbf?w=500&auto=format&fit=crop"], "Samsung", {"Screen": "6.8 inches QHD+", "Camera": "200MP Quad", "Processor": "Snapdragon 8 Gen 3", "Battery": "5000 mAh"}),
        ("MacBook Air M3", "electronics", 1099.00, 0, ["https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=500&auto=format&fit=crop"], "Apple", {"RAM": "8GB Unified", "Storage": "256GB SSD", "Processor": "Apple M3 Chip", "Screen": "13.6 Liquid Retina"}),
        ("Sony WH-1000XM5 Headphones", "electronics", 399.00, 12, ["https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500&auto=format&fit=crop"], "Sony", {"Type": "Over-Ear Wireless", "Battery": "30 Hours", "ANC": "Industry Leading", "Weight": "250g"}),
        ("iPad Pro 11-inch", "electronics", 799.00, 15, ["https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=500&auto=format&fit=crop"], "Apple", {"Screen": "11 Liquid Retina", "Processor": "M2 Chip", "Storage": "128GB", "Weight": "466g"}),
        ("Dell XPS 13 Gaming Laptop", "electronics", 1399.00, 8, ["https://images.unsplash.com/photo-1593642632823-8f785ba67e45?w=500&auto=format&fit=crop"], "Dell", {"CPU": "Intel i7-13th Gen", "RAM": "16GB", "GPU": "Intel Iris Xe", "Storage": "512GB SSD"}),
        ("Logitech MX Master 3S Mouse", "electronics", 99.00, 30, ["https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?w=500&auto=format&fit=crop"], "Logitech", {"Sensor": "8K DPI Track-anywhere", "Battery": "Rechargeable", "Buttons": "7 Programmable"}),
        
        # Fashion
        ("Levis 511 Slim Jeans", "fashion", 69.50, 15, ["https://images.unsplash.com/photo-1542272604-787c3835535d?w=500&auto=format&fit=crop"], "Levis", {"Material": "99% Cotton, 1% Elastane", "Fit": "Slim Fit", "Color": "Dark Indigo"}),
        ("Polo Ralph Lauren T-Shirt", "fashion", 45.00, 0, ["https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=500&auto=format&fit=crop"], "Ralph Lauren", {"Material": "100% Pima Cotton", "Fit": "Custom Slim", "Neckline": "Crew Neck"}),
        ("Zara Wool Blend Coat", "fashion", 189.00, 8, ["https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?w=500&auto=format&fit=crop"], "Zara", {"Material": "60% Wool, 40% Polyester", "Color": "Camel", "Length": "Mid-length"}),
        ("H&M Knitted Sweater", "fashion", 34.99, 25, ["https://images.unsplash.com/photo-1574164904299-3a102b110380?w=500&auto=format&fit=crop"], "H&M", {"Material": "Acrylic & Wool Mix", "Neckline": "Turtleneck", "Color": "Off-White"}),
        ("Nike Windrunner Jacket", "fashion", 110.00, 15, ["https://images.unsplash.com/photo-1548883354-7622d03aca27?w=500&auto=format&fit=crop"], "Nike", {"Material": "100% Polyester", "Type": "Windbreaker", "Color": "Black/White"}),

        # Shoes
        ("Nike Air Max 270", "shoes", 160.00, 12, ["https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=500&auto=format&fit=crop"], "Nike", {"Type": "Running", "Sole": "Max Air Unit", "Upper": "Mesh", "Weight": "290g"}),
        ("Adidas Ultraboost Light", "shoes", 190.00, 8, ["https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?w=500&auto=format&fit=crop"], "Adidas", {"Type": "Running/Lifestyle", "Midsole": "Boost Light", "Upper": "Primeknit"}),
        ("Converse Chuck Taylor All Star", "shoes", 65.00, 40, ["https://images.unsplash.com/photo-1491553895911-0055eca6402d?w=500&auto=format&fit=crop"], "Converse", {"Type": "Casual High Top", "Upper": "Canvas", "Sole": "Vulcanized Rubber"}),
        ("Dr. Martens 1460 Leather Boots", "shoes", 170.00, 14, ["https://images.unsplash.com/photo-1608256246200-53e635b5b65f?w=500&auto=format&fit=crop"], "Dr. Martens", {"Type": "8-Eyelet Boot", "Leather": "Smooth Bovine", "Sole": "AirWair Cushioning"}),
        ("Puma Suede Classic", "shoes", 75.00, 20, ["https://images.unsplash.com/photo-1539185441755-769473a23570?w=500&auto=format&fit=crop"], "Puma", {"Type": "Casual Retro", "Upper": "Premium Suede", "Sole": "Rubber Grid"}),

        # Watches
        ("Apple Watch Series 9", "watches", 399.00, 8, ["https://images.unsplash.com/photo-1543512214-318c7553f230?w=500&auto=format&fit=crop"], "Apple", {"Screen": "Always-On Retina", "Sensors": "ECG, Temp, Blood Oxygen", "Battery": "18 Hours"}),
        ("Fossil Gen 6 Smartwatch", "watches", 229.00, 12, ["https://images.unsplash.com/photo-1522312346375-d1a52e2b99b3?w=500&auto=format&fit=crop"], "Fossil", {"OS": "Wear OS by Google", "Case Size": "44mm", "Processor": "Snapdragon Wear 4100+"}),
        ("Casio G-Shock Classic", "watches", 99.00, 50, ["https://images.unsplash.com/photo-1612817159949-195b6eb9e31a?w=500&auto=format&fit=crop"], "Casio", {"Resistances": "200M Water/Shock", "Functions": "Stopwatch, Alarm", "Battery life": "7 Years"}),
        ("Seiko Presage Automatic", "watches", 450.00, 6, ["https://images.unsplash.com/photo-1524805444758-089113d48a6d?w=500&auto=format&fit=crop"], "Seiko", {"Movement": "4R35 Automatic", "Jewels": "23", "Dial": "Sunburst Blue"}),

        # Furniture
        ("Mid-Century Velvet Sofa", "furniture", 899.00, 4, ["https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=500&auto=format&fit=crop"], "NovaHome", {"Seating Capacity": "3 Seater", "Fabric": "Premium Velvet", "Legs": "Solid Eucalyptus"}),
        ("Minimalist Wooden Coffee Table", "furniture", 149.00, 10, ["https://images.unsplash.com/photo-1533090161767-e6ffed986c88?w=500&auto=format&fit=crop"], "NovaHome", {"Material": "Solid Oak Wood", "Dimensions": "40\"W x 22\"D x 16\"H", "Shape": "Rectangular"}),
        ("Ergonomic Mesh Office Chair", "furniture", 249.00, 15, ["https://images.unsplash.com/photo-1505797149-43b0069ec26b?w=500&auto=format&fit=crop"], "Herman Miller", {"Support": "Adjustable Lumbar/3D Armrests", "Base": "Nylon Castors", "Mesh": "Breathable Elastomer"}),
        ("Modern Lounge Armchair", "furniture", 320.00, 5, ["https://images.unsplash.com/photo-1567538096630-e0c55bd6374c?w=500&auto=format&fit=crop"], "IKEA", {"Frame": "Molded Plywood", "Cushions": "High-resiliency foam", "Cover": "Genuine Leather"}),

        # Beauty
        ("Estée Lauder Advanced Night Repair", "beauty", 85.00, 30, ["https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=500&auto=format&fit=crop"], "Estée Lauder", {"Volume": "50ml", "Skin Type": "All Skins", "Purpose": "Anti-Aging Serum"}),
        ("Dior Sauvage Eau de Parfum", "beauty", 145.00, 20, ["https://images.unsplash.com/photo-1541643600914-78b084683601?w=500&auto=format&fit=crop"], "Dior", {"Volume": "100ml", "Notes": "Bergamot, Sichuan Pepper, Ambroxan", "Type": "EDP Spray"}),
        ("MAC Matte Lipstick (Ruby Woo)", "beauty", 23.00, 100, ["https://images.unsplash.com/photo-1586495777744-4413f21062fa?w=500&auto=format&fit=crop"], "MAC", {"Finish": "Retro Matte", "Color": "Vivid Blue-Red", "Weight": "3g"}),
        ("CeraVe Hydrating Facial Cleanser", "beauty", 16.99, 60, ["https://images.unsplash.com/photo-1556228720-195a672e8a03?w=500&auto=format&fit=crop"], "CeraVe", {"Volume": "16 oz", "Ingredients": "Ceramides, Hyaluronic Acid", "Skin Type": "Normal to Dry"}),

        # Grocery
        ("Organic Matcha Green Tea Powder", "grocery", 24.99, 45, ["https://images.unsplash.com/photo-1536256263959-770b48d82b0a?w=500&auto=format&fit=crop"], "EcoHerb", {"Weight": "100g", "Origin": "Uji, Japan", "Grade": "Ceremonial Grade"}),
        ("Extra Virgin Olive Oil (Cold Pressed)", "grocery", 18.50, 40, ["https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=500&auto=format&fit=crop"], "Tuscany Gold", {"Volume": "500ml", "Acidity": "< 0.3%", "Type": "Cold Pressed"}),
        ("Premium Raw Manuka Honey (MGO 400+)", "grocery", 42.00, 25, ["https://images.unsplash.com/photo-1587049352846-4a222e784d38?w=500&auto=format&fit=crop"], "Kiva", {"Weight": "250g", "MGO Rating": "400+", "Origin": "New Zealand"}),
        ("Single Origin Colombian Coffee Beans", "grocery", 14.99, 50, ["https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=500&auto=format&fit=crop"], "Roasters Pride", {"Weight": "1 lb", "Roast Level": "Medium Roast", "Flavors": "Caramel, Citrus"}),

        # Sports
        ("Wilson NFL Duke Official Football", "sports", 120.00, 10, ["https://images.unsplash.com/photo-1508098682722-e99c43a406b2?w=500&auto=format&fit=crop"], "Wilson", {"Material": "Genuine Leather", "Size": "Official Pro Size"}),
        ("Fitbit Charge 6 Fitness Tracker", "sports", 159.95, 15, ["https://images.unsplash.com/photo-1575311373937-040b8e1fd5b6?w=500&auto=format&fit=crop"], "Fitbit", {"Sensors": "Heart Rate, GPS, EDA Scan", "Battery Life": "7 Days"}),
        ("Spalding NBA Zi/O Basketball", "sports", 44.99, 25, ["https://images.unsplash.com/photo-1519766304817-4f37bda74a27?w=500&auto=format&fit=crop"], "Spalding", {"Size": "Official 29.5\"", "Material": "Composite Leather", "Use": "Indoor/Outdoor"}),
        ("Titleist Pro V1 Golf Balls (Dozen)", "sports", 55.00, 50, ["https://images.unsplash.com/photo-1530541930197-ff16ac917b0e?w=500&auto=format&fit=crop"], "Titleist", {"Quantity": "12 Pack", "Layer Count": "3-Piece Design", "Core": "2.0 ZG Process"}),

        # Books
        ("Atomic Habits by James Clear", "books", 16.20, 80, ["https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=500&auto=format&fit=crop"], "Penguin", {"Format": "Hardcover", "Pages": "320", "Genre": "Self-Help"}),
        ("The Creative Act by Rick Rubin", "books", 21.00, 45, ["https://images.unsplash.com/photo-1512820790803-83ca734da794?w=500&auto=format&fit=crop"], "Penguin Press", {"Format": "Hardcover", "Pages": "432", "Genre": "Art & Philosophy"}),
        ("Dune Deluxe Edition by Frank Herbert", "books", 32.00, 30, ["https://images.unsplash.com/photo-1543002588-bfa74002ed7e?w=500&auto=format&fit=crop"], "Ace Books", {"Format": "Deluxe Hardcover", "Pages": "688", "Genre": "Sci-Fi"}),
        ("Thinking, Fast and Slow by Kahneman", "books", 18.00, 60, ["https://images.unsplash.com/photo-1618666012174-83b441c0bc76?w=500&auto=format&fit=crop"], "Farrar Straus", {"Format": "Paperback", "Pages": "499", "Genre": "Psychology/Economics"}),

        # Home Decor
        ("Minimalist Ceramic Vases (Set of 3)", "decor", 39.99, 25, ["https://images.unsplash.com/photo-1578500494198-246f612d3b3d?w=500&auto=format&fit=crop"], "NovaHome", {"Material": "Matte Glazed Ceramic", "Quantity": "3 Vases", "Color": "Earth Tones"}),
        ("Soft Textured Throw Blanket", "decor", 48.00, 35, ["https://images.unsplash.com/photo-1580301762395-21ce84d00bc6?w=500&auto=format&fit=crop"], "NovaHome", {"Material": "Chenille Yarn", "Dimensions": "50\" x 60\"", "Wash": "Machine Washable"}),
        ("Smart LED Table Lamp (RGB)", "decor", 59.99, 20, ["https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=500&auto=format&fit=crop"], "Xiaomi", {"Connectivity": "Wi-Fi & Bluetooth", "Compatibility": "Alexa & Google Assistant", "Lumen": "400 lm"}),
        ("Aromatic Scented Candle (Lavender)", "decor", 18.50, 100, ["https://images.unsplash.com/photo-1603006905003-be475563bc59?w=500&auto=format&fit=crop"], "NovaHome", {"Wax Type": "100% Soy Wax", "Burn Time": "50 Hours", "Weight": "8 oz"})
    ]

    # Expand slightly to get exactly 50 products as requested
    while len(product_catalogue) < 50:
        # Clone items from the catalogue to make up the number
        item = random.choice(product_catalogue[:10])
        idx = len(product_catalogue)
        product_catalogue.append((
            f"{item[0]} Special Edition {idx}",
            item[1],
            item[2] * random.choice([0.9, 1.0, 1.1]),
            item[3] + random.randint(10, 30),
            item[4],
            item[5],
            item[6]
        ))

    products_list = []
    for idx, item in enumerate(product_catalogue, 1):
        prod_id = f"prod_{idx:03d}"
        
        # Random parameters
        discount = random.choice([0, 10, 15, 20, 25])
        rating = round(random.uniform(4.0, 4.9), 1)
        review_count = random.randint(5, 45)
        
        is_featured = random.random() < 0.25
        is_bestseller = random.random() < 0.25
        is_latest = random.random() < 0.25
        
        # Ensure a few have high ratings & stock
        if idx in [1, 2, 4, 13, 14, 22, 26]:
            is_featured = True
            is_bestseller = True
            rating = 4.8
            
        p_doc = {
            "productId": prod_id,
            "name": item[0],
            "category": item[1],
            "price": round(item[2], 2),
            "discount": discount,
            "images": item[4],
            "brand": item[5],
            "rating": rating,
            "reviewCount": review_count,
            "stock": item[3],
            "specs": item[6],
            "isFeatured": is_featured,
            "isBestSeller": is_bestseller,
            "isLatest": is_latest,
            "flashSale": {"discount": 20, "endsAt": (datetime.datetime.now() + datetime.timedelta(hours=6)).isoformat()} if idx in [4, 13, 27] else None,
            "createdAt": (datetime.datetime.now() - datetime.timedelta(days=random.randint(1, 40))).isoformat()
        }
        db.collection('products').document(prod_id).set(p_doc)
        products_list.append(p_doc)

    # 5. Seed Reviews (50 reviews)
    print("Seeding Reviews...")
    comments_pool = [
        "Absolutely amazing! Build quality is top notch and it works flawlessly.",
        "Really good value for money. Very satisfied with the purchase.",
        "Decent product, does what it says. Shipping took a little longer though.",
        "Exceeded my expectations! Highly recommend buying this.",
        "The design is gorgeous. Feels premium in hand.",
        "Average quality. Had some minor issues, but customer service was helpful.",
        "Perfect purchase! Will buy again for sure.",
        "Best in class product. You won't regret buying this!"
    ]
    
    for i in range(1, 51):
        product = random.choice(products_list)
        user = random.choice(users_data)
        
        review_doc = {
            "reviewId": f"rev_{i:03d}",
            "productId": product['productId'],
            "userId": user['uid'],
            "userName": user['displayName'],
            "userPhoto": user['photoURL'],
            "rating": random.choice([4, 5, 5, 5, 3, 4, 5]),
            "comment": random.choice(comments_pool),
            "createdAt": (datetime.datetime.now() - datetime.timedelta(days=random.randint(1, 15))).isoformat()
        }
        db.collection('reviews').document(review_doc['reviewId']).set(review_doc)

    # 6. Seed Orders (20 Orders & OrderItems)
    print("Seeding Orders...")
    statuses = ["Pending", "Confirmed", "Packed", "Shipped", "Delivered", "Cancelled"]
    payment_methods = ["cod", "upi", "card"]
    
    for i in range(1, 21):
        order_id = f"NC-{datetime.date.today().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
        user = random.choice(users_data)
        
        # Assemble 1-3 random items
        order_subtotal = 0.0
        num_items = random.randint(1, 3)
        order_items = random.sample(products_list, num_items)
        
        for idx, p in enumerate(order_items):
            qty = random.randint(1, 2)
            disc_price = p['price'] * (1 - p['discount']/100.0)
            item_total = disc_price * qty
            order_subtotal += item_total
            
            oi_doc = {
                "orderId": order_id,
                "productId": p['productId'],
                "name": p['name'],
                "price": round(disc_price, 2),
                "quantity": qty,
                "image": p['images'][0]
            }
            db.collection('orderItems').add(oi_doc)
            
        shipping_fee = 0.0 if order_subtotal > 200.0 else 15.00
        coupon_applied = random.choice(["", "WELCOME10"])
        discount_val = 0.0
        if coupon_applied == "WELCOME10":
            discount_val = order_subtotal * 0.1
            
        tax_val = (order_subtotal - discount_val) * 0.18
        order_total = (order_subtotal - discount_val) + shipping_fee + tax_val
        
        pm = random.choice(payment_methods)
        ps = "completed" if pm in ["card", "upi"] else "pending"
        status = random.choice(statuses) if pm == "cod" else random.choice(["Confirmed", "Packed", "Shipped", "Delivered"])
        
        if status == "Cancelled":
            ps = "refunded" if pm in ["card", "upi"] else "cancelled"
            
        order_doc = {
            "orderId": order_id,
            "userId": user['uid'],
            "email": user['email'],
            "shippingAddress": {
                "name": user['displayName'],
                "phone": "+1 (555) 123-4567",
                "street": f"{random.randint(100, 999)} Maple Ave",
                "city": "San Francisco",
                "state": "CA",
                "zip": "94103",
                "country": "United States"
            },
            "billingAddress": {
                "name": user['displayName'],
                "phone": "+1 (555) 123-4567",
                "street": f"{random.randint(100, 999)} Maple Ave",
                "city": "San Francisco",
                "state": "CA",
                "zip": "94103",
                "country": "United States"
            },
            "subtotal": round(order_subtotal, 2),
            "shippingFee": shipping_fee,
            "tax": round(tax_val, 2),
            "discount": round(discount_val, 2),
            "total": round(order_total, 2),
            "couponCode": coupon_applied,
            "paymentMethod": pm,
            "paymentStatus": ps,
            "orderStatus": status,
            "createdAt": (datetime.datetime.now() - datetime.timedelta(days=random.randint(1, 20))).isoformat(),
            "updatedAt": datetime.datetime.now().isoformat()
        }
        db.collection('orders').document(order_id).set(order_doc)
        
        # Save payments collection records
        if ps == "completed":
            db.collection('payments').add({
                "paymentId": f"pay_{i:03d}",
                "orderId": order_id,
                "userId": user['uid'],
                "amount": round(order_total, 2),
                "method": pm,
                "transactionId": f"TXN{random.randint(100000000, 999999999)}",
                "status": "success",
                "createdAt": order_doc['createdAt']
            })

        # Save notifications for some orders
        if random.random() < 0.3:
            db.collection('notifications').add({
                "userId": user['uid'],
                "title": f"Order {status}",
                "message": f"Your order {order_id} is currently: {status}.",
                "type": "order",
                "isRead": False,
                "createdAt": datetime.datetime.now().isoformat()
            })

    print("Seeding Complete!")

if __name__ == '__main__':
    seed_db()
