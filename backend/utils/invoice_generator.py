import datetime

def generate_invoice_html(order, items):
    """
    Generates a beautiful printable HTML invoice for an order.
    `order` is a dict of the order details.
    `items` is a list of dicts representing the orderItems.
    """
    order_id = order.get('orderId', 'N/A')
    created_at_raw = order.get('createdAt', '')
    
    # Parse date
    if isinstance(created_at_raw, str):
        try:
            # handle isoformat
            dt = datetime.datetime.fromisoformat(created_at_raw.replace('Z', '+00:00'))
            created_at = dt.strftime('%B %d, %Y %I:%M %p')
        except ValueError:
            created_at = created_at_raw
    else:
        created_at = datetime.datetime.now().strftime('%B %d, %Y %I:%M %p')

    billing = order.get('billingAddress', {})
    shipping = order.get('shippingAddress', {})
    
    bill_name = billing.get('name', shipping.get('name', 'Customer'))
    bill_phone = billing.get('phone', shipping.get('phone', 'N/A'))
    bill_street = billing.get('street', shipping.get('street', 'N/A'))
    bill_city = billing.get('city', shipping.get('city', 'N/A'))
    bill_state = billing.get('state', shipping.get('state', 'N/A'))
    bill_zip = billing.get('zip', shipping.get('zip', 'N/A'))
    bill_country = billing.get('country', shipping.get('country', 'N/A'))

    ship_name = shipping.get('name', 'Customer')
    ship_phone = shipping.get('phone', 'N/A')
    ship_street = shipping.get('street', 'N/A')
    ship_city = shipping.get('city', 'N/A')
    ship_state = shipping.get('state', 'N/A')
    ship_zip = shipping.get('zip', 'N/A')
    ship_country = shipping.get('country', 'N/A')

    subtotal = float(order.get('subtotal', 0.0))
    shipping_fee = float(order.get('shippingFee', 0.0))
    tax = float(order.get('tax', 0.0))
    discount = float(order.get('discount', 0.0))
    total = float(order.get('total', 0.0))
    
    payment_method = str(order.get('paymentMethod', 'N/A')).upper()
    payment_status = str(order.get('paymentStatus', 'Pending')).capitalize()

    # Generate item rows
    item_rows = ""
    for idx, item in enumerate(items, 1):
        name = item.get('name', 'Product')
        price = float(item.get('price', 0.0))
        qty = int(item.get('quantity', 1))
        item_total = price * qty
        item_rows += f"""
        <tr>
            <td style="padding: 12px; border-bottom: 1px solid #E2E8F0; text-align: center;">{idx}</td>
            <td style="padding: 12px; border-bottom: 1px solid #E2E8F0; font-weight: 500; color: #0F172A;">{name}</td>
            <td style="padding: 12px; border-bottom: 1px solid #E2E8F0; text-align: right;">${price:,.2f}</td>
            <td style="padding: 12px; border-bottom: 1px solid #E2E8F0; text-align: center;">{qty}</td>
            <td style="padding: 12px; border-bottom: 1px solid #E2E8F0; text-align: right; font-weight: 600; color: #0F172A;">${item_total:,.2f}</td>
        </tr>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Invoice - {order_id}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
        body {{
            font-family: 'Poppins', sans-serif;
            margin: 0;
            padding: 40px;
            color: #334155;
            background-color: #FFFFFF;
        }}
        .invoice-box {{
            max-width: 800px;
            margin: auto;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 40px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid #F1F5F9;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .logo {{
            font-size: 28px;
            font-weight: 700;
            color: #4F46E5;
            letter-spacing: -0.5px;
        }}
        .logo span {{
            color: #0F172A;
        }}
        .title {{
            font-size: 20px;
            font-weight: 600;
            color: #0F172A;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }}
        .info-block h3 {{
            font-size: 14px;
            color: #94A3B8;
            text-transform: uppercase;
            margin-top: 0;
            margin-bottom: 8px;
            letter-spacing: 0.5px;
        }}
        .info-block p {{
            margin: 0;
            line-height: 1.5;
            font-size: 14px;
            color: #0F172A;
        }}
        .address-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 40px;
            margin-bottom: 40px;
        }}
        .address-block h4 {{
            margin-top: 0;
            margin-bottom: 10px;
            font-size: 14px;
            text-transform: uppercase;
            color: #4F46E5;
            letter-spacing: 0.5px;
        }}
        .address-block p {{
            margin: 0 0 4px 0;
            line-height: 1.4;
            font-size: 13px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 30px;
        }}
        th {{
            background-color: #F8FAFC;
            color: #475569;
            font-weight: 600;
            font-size: 13px;
            text-transform: uppercase;
            padding: 12px;
            border-bottom: 2px solid #E2E8F0;
        }}
        .summary-wrapper {{
            display: flex;
            justify-content: flex-end;
        }}
        .summary-table {{
            width: 300px;
            margin-bottom: 0;
        }}
        .summary-table td {{
            padding: 8px 12px;
            font-size: 14px;
        }}
        .summary-table tr.total-row td {{
            border-top: 2px solid #4F46E5;
            font-size: 18px;
            font-weight: 700;
            color: #4F46E5;
            padding-top: 12px;
        }}
        .footer {{
            text-align: center;
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #F1F5F9;
            font-size: 12px;
            color: #94A3B8;
        }}
        .print-btn {{
            display: block;
            width: 120px;
            margin: 20px auto 0 auto;
            padding: 10px 20px;
            background-color: #4F46E5;
            color: white;
            border: none;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
            text-align: center;
            box-shadow: 0 4px 6px -1px rgba(79, 70, 229, 0.2);
            transition: all 0.2s;
        }}
        .print-btn:hover {{
            background-color: #4338CA;
        }}
        @media print {{
            body {{
                padding: 0;
            }}
            .invoice-box {{
                border: none;
                box-shadow: none;
                padding: 0;
            }}
            .print-btn {{
                display: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="invoice-box">
        <div class="header">
            <div class="logo">Nova<span>Cart</span></div>
            <div class="title">Invoice</div>
        </div>

        <div class="info-grid">
            <div class="info-block">
                <h3>Order ID</h3>
                <p style="font-weight: 600; color: #4F46E5;">{order_id}</p>
            </div>
            <div class="info-block" style="text-align: right;">
                <h3>Date Issued</h3>
                <p>{created_at}</p>
            </div>
        </div>

        <div class="address-grid">
            <div class="address-block">
                <h4>Billed To</h4>
                <p><strong>{bill_name}</strong></p>
                <p>{bill_street}</p>
                <p>{bill_city}, {bill_state} {bill_zip}</p>
                <p>{bill_country}</p>
                <p>Phone: {bill_phone}</p>
            </div>
            <div class="address-block">
                <h4>Shipped To</h4>
                <p><strong>{ship_name}</strong></p>
                <p>{ship_street}</p>
                <p>{ship_city}, {ship_state} {ship_zip}</p>
                <p>{ship_country}</p>
                <p>Phone: {ship_phone}</p>
            </div>
        </div>

        <table>
            <thead>
                <tr>
                    <th style="width: 8%; text-align: center;">#</th>
                    <th style="text-align: left;">Product Name</th>
                    <th style="width: 18%; text-align: right;">Price</th>
                    <th style="width: 12%; text-align: center;">Qty</th>
                    <th style="width: 20%; text-align: right;">Total</th>
                </tr>
            </thead>
            <tbody>
                {item_rows}
            </tbody>
        </table>

        <div class="summary-wrapper">
            <table class="summary-table">
                <tr>
                    <td style="color: #64748B;">Subtotal:</td>
                    <td style="text-align: right; font-weight: 500;">${subtotal:,.2f}</td>
                </tr>
                <tr>
                    <td style="color: #64748B;">Shipping:</td>
                    <td style="text-align: right; font-weight: 500;">${shipping_fee:,.2f}</td>
                </tr>
                <tr>
                    <td style="color: #64748B;">Tax (18%):</td>
                    <td style="text-align: right; font-weight: 500;">${tax:,.2f}</td>
                </tr>
                {"<tr><td style='color: #22C55E;'>Discount:</td><td style='text-align: right; font-weight: 500; color: #22C55E;'>-${discount:,.2f}</td></tr>" if discount > 0 else ""}
                <tr class="total-row">
                    <td>Total Due:</td>
                    <td style="text-align: right;">${total:,.2f}</td>
                </tr>
            </table>
        </div>

        <div class="info-grid" style="margin-top: 40px; border-top: 1px solid #F1F5F9; padding-top: 20px;">
            <div class="info-block">
                <h3>Payment Method</h3>
                <p>{payment_method} ({payment_status})</p>
            </div>
            <div class="info-block" style="text-align: right;">
                <h3>Status</h3>
                <p style="font-weight: 600; color: #22C55E;">Paid</p>
            </div>
        </div>

        <div class="footer">
            <p>Thank you for shopping at NovaCart!</p>
            <p>For support, contact support@novacart.com</p>
        </div>
    </div>
    
    <button class="print-btn" onclick="window.print()">Print Invoice</button>
</body>
</html>
"""
    return html
