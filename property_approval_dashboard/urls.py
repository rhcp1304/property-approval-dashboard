from django.contrib import admin
from django.urls import path
from property import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.dashboard, name='dashboard'),
    path('veto/<int:pk>/', views.veto_action, name='veto_action'),
]