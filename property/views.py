import re
import requests
from django.views.generic import ListView
from django.http import HttpResponse, Http404
from .models import PropertyRecord

# Google API Imports
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials


# --- 1. Your Existing Dashboard View ---
class PropertyDashboardView(ListView):
    model = PropertyRecord
    template_name = 'property/dashboard.html'
    context_object_name = 'properties'
    ordering = ['-created_at']


# --- 2. The New Proxy View (Fixes the expired/private links) ---
def slide_proxy(request):
    """
    Acts as a bridge: Uses the server's token.json to fetch a fresh, 
    authorized thumbnail from Google and serves it to the browser.
    """
    # Get the PPT link passed from the HTML template
    full_url = request.GET.get('url')

    if not full_url:
        return HttpResponse("No URL provided", status=400)

    try:
        # Step A: Extract the File ID from the Google Slides URL
        # Looks for the long string between /d/ and /edit
        match = re.search(r'/d/([a-zA-Z0-9_-]{25,})', full_url)
        if not match:
            return HttpResponse("Invalid Google Drive URL", status=400)
        file_id = match.group(1)

        # Step B: Load your "Membership Badge" (token.json)
        # This allows the server to act as a member of your company group
        token_path = '/home/lk/property-approval-dashboard/token.json'
        creds = Credentials.from_authorized_user_file(token_path)
        service = build('drive', 'v3', credentials=creds)

        # Step C: Ask Google for a FRESH, high-quality thumbnail link
        file_meta = service.files().get(fileId=file_id, fields='thumbnailLink').execute()
        thumbnail_url = file_meta.get('thumbnailLink')

        if not thumbnail_url:
            return HttpResponse("Thumbnail not available", status=404)

        # Step D: Download the actual image bits from Google
        # We change =s220 to =s1000 to get a clear, large image
        high_res_url = thumbnail_url.replace('=s220', '=s1000')
        img_data = requests.get(high_res_url).content

        # Step E: Send the image bits back to the user's browser
        return HttpResponse(img_data, content_type="image/png")

    except Exception as e:
        print(f"Proxy Error: {e}")
        return HttpResponse(status=404)