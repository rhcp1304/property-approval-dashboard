# ~/property-approval-dashboard/property_approval_dashboard/urls.py

from django.urls import path
from django.contrib.auth import views as auth_views
from property import views  # Ensure this matches your app name

urlpatterns = [
    path('dashboard/', views.PropertyDashboardView.as_view(), name='property_dashboard'),
    path('update-remarks/<int:pk>/', views.update_remarks, name='update_remarks'),
    path('slide-proxy/', views.slide_proxy, name='slide_proxy'),

    # This uses the clean admin login but redirects back to dashboard
    path('login/', auth_views.LoginView.as_view(template_name='admin/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]