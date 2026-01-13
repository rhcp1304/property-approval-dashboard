from django.urls import path
from .views import PropertyDashboardView

urlpatterns = [
    path('dashboard/', PropertyDashboardView.as_view(), name='property_dashboard'),
]