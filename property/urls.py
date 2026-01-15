from django.urls import path
from django.contrib.auth import views as auth_views
from property import views

urlpatterns = [
    path('dashboard/', views.PropertyDashboardView.as_view(), name='property_dashboard'),
    path('update-remarks/<int:pk>/', views.update_remarks, name='update_remarks'),
    path('slide-proxy/', views.slide_proxy, name='slide_proxy'),

    # --- NEW API PATH FOR ANDROID ---
    path('api/properties/', views.PropertyRecordListAPIView.as_view(), name='api_property_list'),

    path('login/', auth_views.LoginView.as_view(template_name='admin/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]