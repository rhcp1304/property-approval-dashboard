from django.urls import path
from .views import PropertyDashboardView, slide_proxy

urlpatterns = [
    # Your existing dashboard route
    path('dashboard/', PropertyDashboardView.as_view(), name='property_dashboard'),

    # The NEW proxy route for images
    # This matches the {% url 'slide_proxy' %} tag in your HTML
    path('slide-proxy/', slide_proxy, name='slide_proxy'),
]