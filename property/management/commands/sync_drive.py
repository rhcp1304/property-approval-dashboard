import os.path
from django.core.management.base import BaseCommand
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from property.models import PropertyRecord

SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']


class Command(BaseCommand):
    help = "Groups PPT, PDF summary, and MP4 recording by folder and saves to DB"

    def handle(self, *args, **options):
        # 1. Auth (Same as your original code)
        creds = None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        if not creds or not creds.valid:
            flow = InstalledAppFlow.from_client_secrets_file('bdstorage_credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            with open('token.json', 'w') as token: token.write(creds.to_json())

        service = build('drive', 'v3', credentials=creds)

        # 2. Fetch all relevant files
        self.stdout.write("Scanning Drive for files...")
        # Query for Folders, PPTs, PDFs, and MP4s
        q = (
            "trashed = false and ("
            "mimeType = 'application/vnd.google-apps.folder' or "
            "mimeType contains 'presentation' or "
            "name = 'ai_summary.pdf' or "
            "name = 'recording.mp4'"
            ")"
        )
        all_items = self.get_all(service, q)

        # 3. Organize data by Folder ID
        # folder_data structure: { 'folder_id': { 'name': '...', 'ppt': link, 'pdf': link, 'mp4': link } }
        folder_data = {}

        # First, initialize the map with folder names
        for item in all_items:
            if item['mimeType'] == 'application/vnd.google-apps.folder':
                folder_data[item['id']] = {'name': item['name'], 'ppt': None, 'pdf': None, 'mp4': None}

        # Second, distribute files into their parent folders
        for item in all_items:
            parents = item.get('parents')
            if not parents: continue

            p_id = parents[0]
            if p_id not in folder_data: continue  # Skip if parent folder wasn't in our query

            link = item.get('webViewLink')
            name = item.get('name', '').lower()
            mime = item.get('mimeType', '')

            if 'presentation' in mime:
                folder_data[p_id]['ppt'] = link
            elif name == 'ai_summary.pdf':
                folder_data[p_id]['pdf'] = link
            elif name == 'recording.mp4':
                folder_data[p_id]['mp4'] = link

        # 4. Save to DB
        count = 0
        for f_id, content in folder_data.items():
            # We only create a record if at least a PPT exists
            if content['ppt']:
                PropertyRecord.objects.update_or_create(
                    ppt_link=content['ppt'],
                    defaults={
                        'presentation_date_context': content['name'],
                        'ai_summary_link': content['pdf'],
                        'recording_link': content['mp4'],
                    }
                )
                count += 1

        self.stdout.write(self.style.SUCCESS(f"Finished! Processed {count} property records."))

    def get_all(self, service, q):
        items, page_token = [], None
        while True:
            res = service.files().list(
                q=q,
                fields="nextPageToken, files(id, name, webViewLink, mimeType, parents)",
                pageToken=page_token,
                pageSize=1000
            ).execute()
            items.extend(res.get('files', []))
            page_token = res.get('nextPageToken')
            if not page_token: break
        return items