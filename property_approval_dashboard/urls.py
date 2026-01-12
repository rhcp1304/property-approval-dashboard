from django.contrib import admin
from django.urls import path
from property import views  # Your existing app
from store.views import ApprovedStoreListView, ApprovedStoreDetailView  # The new app

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.dashboard, name='dashboard'),  # Your existing dashboard
    path('veto/<int:pk>/', views.veto_action, name='veto_action'),

    # --- NEW DASHBOARD ROUTES ---
    path('approved/', ApprovedStoreListView.as_view(), name='approved_list'),
    path('approved/<int:pk>/', ApprovedStoreDetailView.as_view(), name='approved_detail'),
]