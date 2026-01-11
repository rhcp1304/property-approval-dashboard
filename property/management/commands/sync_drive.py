import os.path
from django.core.management.base import BaseCommand
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from property.models import PropertyRecord

# CONFIGURATION
ROOT_FOLDER_ID = '1RC8sAC3ejgYCZ97LXaXGjzwXanGywm63'
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']


class Command(BaseCommand):
    help = "Extracts all PPT links and their folder names starting from a Root ID"

    def handle(self, *args, **options):
        # 1. Auth
        creds = None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        if not creds or not creds.valid:
            flow = InstalledAppFlow.from_client_secrets_file('bdstorage_credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            with open('token.json', 'w') as token: token.write(creds.to_json())

        service = build('drive', 'v3', credentials=creds)

        # 2. Fetch All Presentation Files & All Folders (to get names)
        self.stdout.write("Scanning Drive for Presentations...")

        # We query for both folders (to get names) and presentations
        q = f"trashed = false and (mimeType = 'application/vnd.google-apps.folder' or mimeType contains 'presentation')"
        all_items = self.get_all(service, q)

        # Create a folder ID -> Name map for quick lookup
        folder_map = {i['id']: i['name'] for i in all_items if i['mimeType'] == 'application/vnd.google-apps.folder'}
        ppt_files = [i for i in all_items if 'presentation' in i['mimeType']]

        # 3. Save to DB
        count = 0
        for ppt in ppt_files:
            parent_id = ppt.get('parents', [None])[0]
            # Get the name of the folder containing the PPT
            folder_name = folder_map.get(parent_id, "Unknown Folder")
            link = ppt.get('webViewLink')

            if link:
                PropertyRecord.objects.update_or_create(
                    ppt_link=link,
                    defaults={
                        'presentation_date_context': folder_name,
                    }
                )
                count += 1

        self.stdout.write(self.style.SUCCESS(f"Finished! Found and saved {count} PPT links."))

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