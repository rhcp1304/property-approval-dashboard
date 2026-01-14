import re
import os
import requests
from django.conf import settings
from django.views.generic import ListView
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.contrib import messages  # Added for user feedback assurance
from .models import PropertyRecord
from django.contrib.auth.decorators import login_required # Add this
# Google API Imports
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials


# --- 1. Dashboard View ---
class PropertyDashboardView(ListView):
    """
    Main entry point for the dashboard.
    Fetches all property records and displays them in the inventory.
    """
    model = PropertyRecord
    template_name = 'property/dashboard.html'
    context_object_name = 'properties'
    ordering = ['-created_at']


# --- 2. Remarks Update View (With Assurance Feedback) ---
@login_required  # <--- ADD THIS LINE
@require_POST
def update_remarks(request, pk):
    """
    Captures remarks from the UI Modal, saves them,
    and triggers a success message for the user.
    """
    property_record = get_object_or_404(PropertyRecord, pk=pk)
    new_remarks = request.POST.get('remarks', '').strip()

    # Update the record
    property_record.remarks = new_remarks
    property_record.save()

    # Success message provides the 'Assurance' that it was recorded
    messages.success(request,
                     f"Remark for {property_record.final_market_name or 'Property'} has been successfully recorded.")

    # Redirects back to the dashboard (matching name in urls.py)
    return redirect('property_dashboard')


# --- 3. The Proxy View (Dynamic Path Fix) ---
def slide_proxy(request):
    """
    Authorized bridge to fetch Google Slides thumbnails using the server's token.
    """
    full_url = request.GET.get('url')

    if not full_url:
        return HttpResponse("No URL provided", status=400)

    try:
        # Extract File ID from Google URL
        match = re.search(r'/d/([a-zA-Z0-9_-]{25,})', full_url)
        if not match:
            return HttpResponse("Invalid Google Drive URL", status=400)
        file_id = match.group(1)

        # Dynamic Token Path (Works on Mac/Linux/Windows)
        token_path = os.path.join(settings.BASE_DIR, 'token.json')

        if not os.path.exists(token_path):
            print(f"Error: token.json not found at {token_path}")
            return HttpResponse("Credentials missing on server", status=500)

        # Build Google Service
        creds = Credentials.from_authorized_user_file(token_path)
        service = build('drive', 'v3', credentials=creds)

        # Fetch Thumbnail
        file_meta = service.files().get(fileId=file_id, fields='thumbnailLink').execute()
        thumbnail_url = file_meta.get('thumbnailLink')

        if not thumbnail_url:
            return HttpResponse("Thumbnail not available", status=404)

        # Upscale to high-res
        high_res_url = thumbnail_url.replace('=s220', '=s1000')
        img_data = requests.get(high_res_url).content

        return HttpResponse(img_data, content_type="image/png")

    except Exception as e:
        print(f"Proxy Error: {e}")
        return HttpResponse(status=404)