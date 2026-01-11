import requests
import json
import re
from django.core.management.base import BaseCommand
from django.db import transaction
from store.models import ApprovedLenskartStore, Catchment


class Command(BaseCommand):
    help = 'Fetches approved properties from GeoIQ API and loads them directly into the database.'

    def handle(self, *args, **options):
        url = "https://retailapis-in.geoiq.ai/bdapp/prod/v1/bd/getAllKissflowProperties"
        headers = {
            'x-api-key': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJtYWlsSWRlbnRpdHkiOiJsZW5za2FydC1hZG1pbkBnZW9pcS5pbyJ9.SbaX7dGyaRz_EVwgdE-cQe7_c0pCnM2OPJD2legV0jU',
            'Content-Type': 'application/json'
        }
        payload = json.dumps({})

        self.stdout.write(self.style.NOTICE("Fetching data from API..."))

        try:
            response = requests.post(url, headers=headers, data=payload)
            response.raise_for_status()
            data = response.json().get('data', [])
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"API Request failed: {e}"))
            return

        self.stdout.write(self.style.NOTICE(f"Received {len(data)} records. Processing..."))

        # Prefetch catchments for Phase 2
        catchment_map = {c.market_id: c for c in Catchment.objects.all()}

        records_to_upsert = []

        # PHASE 1: Prepare records
        for item in data:
            prop_id = item.get('property_id')
            if not prop_id:
                continue

            records_to_upsert.append(
                ApprovedLenskartStore(
                    property_id=prop_id,
                    property_name=item.get('property_name'),
                    property_address=item.get('property_address'),
                    latitude=item.get('property_lat'),
                    longitude=item.get('property_lng'),
                    market_ids_raw=item.get('market_id'),
                    kissflow_status=item.get('kissflow_status', 'N/A')
                )
            )

        # PHASE 1: Bulk Upsert
        with transaction.atomic():
            ApprovedLenskartStore.objects.bulk_create(
                records_to_upsert,
                update_conflicts=True,
                unique_fields=['property_id'],
                update_fields=['property_name', 'property_address', 'latitude', 'longitude', 'market_ids_raw',
                               'kissflow_status']
            )

        self.stdout.write(self.style.SUCCESS(f"Successfully saved {len(records_to_upsert)} records."))

        # PHASE 2: Link Catchments (Many-to-Many)
        self.stdout.write(self.style.NOTICE("Linking properties to catchments..."))
        link_count = 0

        # Get all properties we just saved that have market IDs
        properties = ApprovedLenskartStore.objects.exclude(market_ids_raw__isnull=True).exclude(market_ids_raw="")

        with transaction.atomic():
            for prop in properties:
                # Extract IDs from strings like "33215; 33216"
                market_ids = re.findall(r'\d+', str(prop.market_ids_raw))

                valid_catchments = [
                    catchment_map[int(mid)]
                    for mid in market_ids
                    if int(mid) in catchment_map
                ]

                if valid_catchments:
                    prop.catchments.set(valid_catchments)
                    link_count += len(valid_catchments)

        self.stdout.write(self.style.SUCCESS(f"✅ Process complete. Created {link_count} catchment links."))