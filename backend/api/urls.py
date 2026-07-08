from django.urls import path
from . import views

urlpatterns = [
    # Customer APIs
    path('auth/verify-token/', views.verify_token_api, name='api_verify_token'),
    path('categories/', views.get_categories_api, name='api_categories'),
    path('products/', views.get_products_api, name='api_products'),
    path('reviews/', views.reviews_api, name='api_reviews'),
    path('reviews/<str:review_id>/delete/', views.review_delete_api, name='api_review_delete'),
    
    # Cart & Checkout
    path('coupons/validate/', views.validate_coupon_api, name='api_validate_coupon'),
    path('orders/checkout/', views.checkout_api, name='api_checkout'),
    path('orders/cancel/', views.cancel_order_api, name='api_cancel_order'),
    path('orders/<str:order_id>/invoice/', views.download_invoice_api, name='api_download_invoice'),
    path('recommendations/', views.get_recommendations_api, name='api_recommendations'),
    path('contact/', views.submit_contact_api, name='api_submit_contact'),

    # Admin Dashboard APIs
    path('admin/products/', views.admin_products_api, name='api_admin_products'),
    path('admin/products/<str:product_id>/', views.admin_products_api, name='api_admin_product_detail'),
    path('admin/orders/', views.admin_orders_api, name='api_admin_orders'),
    path('admin/orders/<str:order_id>/', views.admin_orders_api, name='api_admin_order_detail'),
    path('admin/users/', views.admin_users_api, name='api_admin_users'),
    path('admin/users/<str:uid>/', views.admin_users_api, name='api_admin_user_detail'),
    path('admin/analytics/', views.admin_analytics_api, name='api_admin_analytics'),
]
