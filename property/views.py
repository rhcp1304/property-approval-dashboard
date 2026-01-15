import re
import os
import requests
from django.conf import settings
from django.views.generic import ListView
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

# Google API Imports
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# Local models
from .models import PropertyRecord


# --- 1. Dashboard View (Locked for entire page) ---
class PropertyDashboardView(LoginRequiredMixin, ListView):
    """
    The 'Command Center'. Only authenticated users can enter.
    Uses 'only()' to keep database memory usage low.
    """
    model = PropertyRecord
    template_name = 'property/dashboard.html'
    context_object_name = 'page_obj'
    paginate_by = 50  # Essential for long-term performance

    # Where to send people if they aren't logged in
    login_url = 'login'

    def get_queryset(self):
        # Professional practice: only fetch necessary fields to prevent 'Big Dump' slowdowns
        queryset = PropertyRecord.objects.all().only(
            'presentation_date', 'zone_name', 'final_market_name',
            'circle', 'hub', 'hub_rank', 'projected_revenue_lakhs',
            'total_rent_maintenance', 'status', 'ppt_link',
            'ai_summary_link', 'recording_link', 'remarks'
        )

        # 1. Zone Filter
        zone_filter = self.request.GET.get('zone')
        if zone_filter:
            queryset = queryset.filter(zone_name=zone_filter)

        # 2. Date Range Filters (Crucial for the 'Filtering not working' fix)
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')

        if start_date:
            queryset = queryset.filter(presentation_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(presentation_date__lte=end_date)

        # Force descending order so newest properties always appear first
        return queryset.order_by('-presentation_date', '-id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Pull distinct zones for the dropdown
        context['zones'] = (
            PropertyRecord.objects.values_list('zone_name', flat=True)
            .distinct()
            .exclude(zone_name__isnull=True)
            .order_by('zone_name')
        )

        context['current_zone'] = self.request.GET.get('zone', '')
        context['total_count'] = self.get_queryset().count()
        return context


# --- 2. Remarks Update View (Protected) ---
@login_required
@require_POST
def update_remarks(request, pk):
    """
    Securely updates remarks. require_POST prevents URL-based attacks.
    """
    property_record = get_object_or_404(PropertyRecord, pk=pk)
    new_remarks = request.POST.get('remarks', '').strip()

    property_record.remarks = new_remarks
    property_record.save(update_fields=['remarks'])  # Optimized save

    messages.success(request, f"Remarks for {property_record.final_market_name} updated successfully.")
    return redirect('property_dashboard')


# --- 3. The Proxy View (Protected & Robust) ---
@login_required
def slide_proxy(request):
    """
    Fetches the thumbnail from Google Drive using the server's credentials.
    Locked with @login_required so outsiders can't scrape your images.
    """
    full_url = request.GET.get('url')
    if not full_url:
        return HttpResponse("No URL provided", status=400)

    try:
        # Extract File ID from Google Drive Link
        match = re.search(r'/d/([a-zA-Z0-9_-]{25,})', full_url)
        if not match:
            return HttpResponse("Invalid Drive URL", status=400)
        file_id = match.group(1)

        # Auth setup
        token_path = os.path.join(settings.BASE_DIR, 'token.json')
        if not os.path.exists(token_path):
            return HttpResponse("Server Error: Auth Token Missing", status=500)

        creds = Credentials.from_authorized_user_file(token_path)
        service = build('drive', 'v3', credentials=creds)

        # Get Thumbnail Link from API
        file_meta = service.files().get(fileId=file_id, fields='thumbnailLink').execute()
        thumbnail_url = file_meta.get('thumbnailLink')

        if not thumbnail_url:
            # Fallback to a placeholder if no thumbnail exists
            return redirect('https://placehold.co/320x180?text=No+Preview')

        # Convert to High Res (=s1000)
        high_res_url = thumbnail_url.replace('=s220', '=s1000')

        # Fetch actual image bits
        response = requests.get(high_res_url, timeout=10)
        return HttpResponse(response.content, content_type="image/png")

    except Exception as e:
        # Fail gracefully without crashing the page
        return HttpResponse(status=404)