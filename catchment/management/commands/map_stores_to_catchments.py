import time
from django.core.management.base import BaseCommand
from django.db import transaction
from shapely.geometry import Point
from shapely import wkt
from catchment.models import Catchment
from store.models import LenskartStore


class Command(BaseCommand):
    help = 'Maps LenskartStore to Catchment based on physical boundary containment in wkt_geometry.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Starting Point-in-Polygon mapping..."))
        start_time = time.time()

        # 1. Load Catchment Polygons from wkt_geometry
        # We exclude empty or null geometries to avoid errors
        catchments = Catchment.objects.exclude(wkt_geometry__isnull=True).exclude(wkt_geometry__exact='')

        spatial_index = []
        for c in catchments:
            try:
                # Convert the text string into a real Polygon object
                poly = wkt.loads(str(c.wkt_geometry))

                # GIS Best Practice: Fix "Self-intersecting" polygons by adding a 0-width buffer
                if not poly.is_valid:
                    poly = poly.buffer(0)

                spatial_index.append({
                    'id': c.id,
                    'name': c.market_name,
                    'poly': poly
                })
            except Exception as e:
                self.stderr.write(f"Skipping Catchment {c.market_name} (ID: {c.id}): Invalid WKT - {e}")

        if not spatial_index:
            self.stderr.write(self.style.ERROR("No valid wkt_geometry found in Catchment table."))
            return

        self.stdout.write(f"Successfully loaded {len(spatial_index)} market boundaries.")

        # 2. Process Stores
        stores_to_update = []
        stores = LenskartStore.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True)

        total_stores = stores.count()
        self.stdout.write(f"Checking {total_stores} stores against boundaries...")

        for store in stores:
            try:
                # IMPORTANT: Shapely Point takes (Longitude, Latitude)
                store_point = Point(float(store.longitude), float(store.latitude))

                matched_catchment_id = None

                # Check which polygon contains the point
                for item in spatial_index:
                    if item['poly'].contains(store_point):
                        matched_catchment_id = item['id']
                        break  # Stop at the first match

                # Update the store object if the catchment has changed
                if matched_catchment_id and store.catchment_id != matched_catchment_id:
                    store.catchment_id = matched_catchment_id
                    stores_to_update.append(store)

            except Exception as e:
                self.stderr.write(
                    self.style.ERROR(f"Error processing store {getattr(store, 'store_code', store.id)}: {e}"))

        # 3. Bulk Update the Database
        if stores_to_update:
            with transaction.atomic():
                # Note: 'catchment' is the field name in LenskartStore pointing to Catchment model
                LenskartStore.objects.bulk_update(stores_to_update, ['catchment'])
            self.stdout.write(self.style.SUCCESS(f"Updated {len(stores_to_update)} stores."))
        else:
            self.stdout.write(self.style.WARNING("No updates required; all stores are correctly mapped."))

        self.stdout.write(self.style.SUCCESS(
            f"✅ Complete. Total time: {time.time() - start_time:.2f}s"
        ))