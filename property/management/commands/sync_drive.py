import os.path
import io
import re
from urllib.parse import urlparse, parse_qs
from pptx import Presentation
from pdfminer.high_level import extract_text
from django.core.management.base import BaseCommand
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from property.models import PropertyRecord

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']


class Command(BaseCommand):
    help = "Syncs all properties; Status is derived from the last two lines of the AI PDF"

    def handle(self, *args, **options):
        # 1. Google Drive Authentication
        creds = None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('bdstorage_credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        service = build('drive', 'v3', credentials=creds)

        # 2. Database Cleanup
        self.stdout.write(self.style.WARNING("Wiping PropertyRecord table for fresh sync..."))
        PropertyRecord.objects.all().delete()

        # 3. Fetch Items (2025 onwards)
        q = (
            "trashed = false and "
            "createdTime > '2025-01-01T00:00:00Z' and ("
            "mimeType = 'application/vnd.google-apps.folder' or "
            "mimeType contains 'presentation' or "
            "name = 'ai_summary.pdf' or "
            "name = 'recording.mp4'"
            ")"
        )
        all_items = self.get_all_files(service, q)

        # 4. Folder Organization
        folder_data = {}
        for item in all_items:
            if item['mimeType'] == 'application/vnd.google-apps.folder':
                folder_data[item['id']] = {
                    'name': item['name'],
                    'ppt_id': None, 'ppt_link': None,
                    'pdf_id': None, 'pdf_link': None,
                    'mp4_link': None
                }

        for item in all_items:
            parents = item.get('parents')
            if not parents or parents[0] not in folder_data: continue
            p_id = parents[0]
            name = item.get('name', '').lower()
            if 'presentation' in item.get('mimeType', ''):
                folder_data[p_id]['ppt_id'] = item['id']
                folder_data[p_id]['ppt_link'] = item.get('webViewLink')
            elif name == 'ai_summary.pdf':
                folder_data[p_id]['pdf_id'] = item['id']
                folder_data[p_id]['pdf_link'] = item.get('webViewLink')
            elif name == 'recording.mp4':
                folder_data[p_id]['mp4_link'] = item.get('webViewLink')

        # 5. Extraction and Save
        count = 0
        if not os.path.exists('downloads'): os.makedirs('downloads')

        for f_id, data in folder_data.items():
            if data['ppt_id'] and data['pdf_id']:
                safe_name = re.sub(r'[\\/*?:"<>|]', "_", data['name'])
                local_pptx = os.path.join('downloads', f"{safe_name}.pptx")
                local_pdf = os.path.join('downloads', f"{safe_name}_sum.pdf")

                try:
                    self.stdout.write(f"Syncing: {data['name']}")
                    self.download_file(service, data['ppt_id'], local_pptx)
                    self.download_file(service, data['pdf_id'], local_pdf)

                    # Extract Property ID (can be NULL)
                    prop_id = self.get_property_id(self.extract_retail_link(local_pptx))

                    # Extract Status using the Last Two Lines logic
                    extracted_status = self.extract_status_from_pdf(local_pdf)

                    PropertyRecord.objects.create(
                        property_id=prop_id,
                        presentation_date_context=data['name'],
                        ppt_link=data['ppt_link'],
                        ai_summary_link=data['pdf_link'],
                        recording_link=data['mp4_link'],
                        status=extracted_status
                    )

                    color = self.style.SUCCESS if "Approved" in extracted_status else self.style.NOTICE
                    self.stdout.write(color(f"  -> Saved | ID: {prop_id or 'NULL'} | Status: {extracted_status}"))
                    count += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  -> Error: {e}"))

        self.stdout.write(self.style.SUCCESS(f"\nFinished! Processed {count} records."))

    def extract_status_from_pdf(self, path):
        """
        Fetches the last two non-empty lines and uses a priority
        check to differentiate between Conditionally Approved and Approved.
        """
        try:
            text = extract_text(path)
            # Filter for non-empty lines
            lines = [line.strip() for line in text.split('\n') if line.strip()]

            if not lines:
                return 'pending'

            # Get the last two lines and join them for searching
            last_two_context = " ".join(lines[-2:]).lower()

            # PRIORITY CHECK: Specific phrase first
            if 'conditionally approved' in last_two_context:
                return 'Conditionally Approved'
            elif 'approved' in last_two_context:
                return 'Approved'
            elif any(word in last_two_context for word in ['rejected', 'dropped', 'not feasible']):
                return 'Dropped/Rejected'
            elif 'hold' in last_two_context:
                return 'Hold'

            return 'pending'
        except Exception:
            return 'pending'

    def extract_retail_link(self, path):
        try:
            prs = Presentation(path)
            for slide in prs.slides:
                for shape in slide.shapes:
                    if not shape.has_text_frame: continue
                    for para in shape.text_frame.paragraphs:
                        for run in para.runs:
                            if "RetailIQ" in run.text and run.hyperlink and run.hyperlink.address:
                                return run.hyperlink.address
        except:
            return None
        return None

    def get_property_id(self, url):
        if not url: return None
        try:
            params = parse_qs(urlparse(url).query)
            return params.get('property_id', [None])[0]
        except:
            return None

    def get_all_files(self, service, q):
        items, page_token = [], None
        while True:
            res = service.files().list(q=q, fields="nextPageToken, files(id, name, webViewLink, mimeType, parents)",
                                       pageToken=page_token, pageSize=1000).execute()
            items.extend(res.get('files', []))
            page_token = res.get('nextPageToken')
            if not page_token: break
        return items

    def download_file(self, service, file_id, destination):
        request = service.files().get_media(fileId=file_id)
        meta = service.files().get(fileId=file_id, fields='mimeType').execute()
        if meta['mimeType'] == 'application/vnd.google-apps.presentation':
            request = service.files().export_media(fileId=file_id,
                                                   mimeType='application/vnd.openxmlformats-officedocument.presentationml.presentation')
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done: _, done = downloader.next_chunk()
        with open(destination, 'wb') as f:
            f.write(fh.getvalue())