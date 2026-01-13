from django.urls import path
from .views import PropertyDashboardView, slide_proxy, update_remarks

urlpatterns = [
    # Existing routes
    path('dashboard/', PropertyDashboardView.as_view(), name='property_dashboard'),
    path('slide-proxy/', slide_proxy, name='slide_proxy'),

    # NEW: The route to handle the Supreme Leader's remarks
    # 'pk' is the unique ID of the property being commented on
    path('update-remarks/<int:pk>/', update_remarks, name='update_remarks'),
]