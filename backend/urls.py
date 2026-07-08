from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('shop/', TemplateView.as_view(template_name='pages/shop.html'), name='shop'),
    path('product/<str:product_id>/', TemplateView.as_view(template_name='pages/product-details.html'), name='product_detail'),
    path('cart/', TemplateView.as_view(template_name='pages/cart.html'), name='cart'),
    path('checkout/', TemplateView.as_view(template_name='pages/checkout.html'), name='checkout'),
    path('dashboard/', TemplateView.as_view(template_name='pages/dashboard.html'), name='dashboard'),
    path('admin-dashboard/', TemplateView.as_view(template_name='pages/admin-dashboard.html'), name='admin_dashboard'),
    path('wishlist/', TemplateView.as_view(template_name='pages/wishlist.html'), name='wishlist'),
    path('about/', TemplateView.as_view(template_name='pages/about.html'), name='about'),
    path('contact/', TemplateView.as_view(template_name='pages/contact.html'), name='contact'),
    path('api/', include('api.urls')),
] + static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
