from django.views.generic import ListView
from .models import PropertyRecord

class PropertyDashboardView(ListView):
    model = PropertyRecord
    template_name = 'property/dashboard.html'
    context_object_name = 'properties'
    ordering = ['-created_at']