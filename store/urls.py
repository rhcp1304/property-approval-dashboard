from django.urls import path
from .views import ApprovedStoreListView, ApprovedStoreDetailView

urlpatterns = [
    path('approved/', ApprovedStoreListView.as_view(), name='approved_list'),
    path('approved/<int:pk>/', ApprovedStoreDetailView.as_view(), name='approved_detail'),
]