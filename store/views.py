from django.views.generic import ListView, DetailView
from .models import ApprovedLenskartStore

class ApprovedStoreListView(ListView):
    model = ApprovedLenskartStore
    template_name = 'dashboard/approved_list.html'
    context_object_name = 'properties'
    ordering = ['-latest_approval_date']

class ApprovedStoreDetailView(DetailView):
    model = ApprovedLenskartStore
    template_name = 'dashboard/approved_detail.html'
    context_object_name = 'property'