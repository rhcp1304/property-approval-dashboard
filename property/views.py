import re
import os
import requests
from django.conf import settings
from django.views.generic import ListView
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.contrib import messages
from .models import PropertyRecord
from django.contrib.auth.decorators import login_required

# Google API Imports
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials


# --- 1. Dashboard View ---
class PropertyDashboardView(ListView):
    """
    Main entry point for the dashboard.
    Handles Filtering (by Zone), Sorting (by Presentation Date), and Pagination.
    """
    model = PropertyRecord
    template_name = 'property/dashboard.html'
    # We use 'page_obj' to match standard Django pagination templates
    context_object_name = 'page_obj'

    def get_queryset(self):
        """
        1. Filters by Zone if selected in the UI.
        2. Sorts by Presentation Date (Descending) and then by creation date.
        """
        queryset = PropertyRecord.objects.all()

        # Get 'zone' from the URL parameters (e.g., ?zone=North)
        zone_filter = self.request.GET.get('zone')
        if zone_filter:
            queryset = queryset.filter(zone_name=zone_filter)

        # Force descending order of Presentation Date
        return queryset.order_by('-presentation_date', '-created_at')

    def get_context_data(self, **kwargs):
        """
        Passes extra data to the UI for the filter dropdowns and header count.
        """
        context = super().get_context_data(**kwargs)

        # 1. Provide a unique list of Zones for the dropdown menu
        context['zones'] = (
            PropertyRecord.objects.values_list('zone_name', flat=True)
            .distinct()
            .exclude(zone_name__isnull=True)
            .order_by('zone_name')
        )

        # 2. Keep track of the currently selected zone for the UI
        context['current_zone'] = self.request.GET.get('zone', '')

        # 3. Total count based on filtered results
        context['total_count'] = self.get_queryset().count()

        return context


# --- 2. Remarks Update View ---
@login_required
@require_POST
def update_remarks(request, pk):
    property_record = get_object_or_404(PropertyRecord, pk=pk)
    new_remarks = request.POST.get('remarks', '').strip()

    property_record.remarks = new_remarks
    property_record.save()

    messages.success(request,
                     f"Remark for {property_record.final_market_name or 'Property'} recorded.")
    return redirect('property_dashboard')


# --- 3. The Proxy View ---
def slide_proxy(request):
    full_url = request.GET.get('url')
    if not full_url:
        return HttpResponse("No URL provided", status=400)

    try:
        match = re.search(r'/d/([a-zA-Z0-9_-]{25,})', full_url)
        if not match:
            return HttpResponse("Invalid Google Drive URL", status=400)
        file_id = match.group(1)

        token_path = os.path.join(settings.BASE_DIR, 'token.json')
        if not os.path.exists(token_path):
            return HttpResponse("Credentials missing", status=500)

        creds = Credentials.from_authorized_user_file(token_path)
        service = build('drive', 'v3', credentials=creds)

        file_meta = service.files().get(fileId=file_id, fields='thumbnailLink').execute()
        thumbnail_url = file_meta.get('thumbnailLink')

        if not thumbnail_url:
            return HttpResponse("Thumbnail not available", status=404)

        high_res_url = thumbnail_url.replace('=s220', '=s1000')
        img_data = requests.get(high_res_url).content
        return HttpResponse(img_data, content_type="image/png")

    except Exception as e:
        return HttpResponse(status=404)