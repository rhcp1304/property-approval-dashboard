import time
import re
from django.core.management.base import BaseCommand
from django.db import transaction
from geopy.distance import geodesic
from catchment.models import Catchment
from store.models import LenskartStore


class Command(BaseCommand):
    help = 'Maps LenskartStore records to their closest Catchment centroid handling WKT POINT format.'

    def _parse_wkt_point(self, wkt_string):
        """
        Extracts coordinates from 'POINT (Longitude Latitude)' format.
        Returns (Latitude, Longitude) for geopy.
        """
        try:
            # Regex to extract numbers from POINT (85.8204 20.3208)
            match = re.search(r'POINT\s*\((?P<lon>[\d\.-]+)\s+(?P<lat>[\d\.-]+)\)', wkt_string)
            if match:
                # IMPORTANT: Geopy expects (Lat, Lon), WKT is (Lon, Lat)
                return float(match.group('lat')), float(match.group('lon'))
        except Exception:
            return None
        return None

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Starting spatial join with WKT support..."))
        start_time = time.time()

        # 1. Pre-process Catchments
        catchments_with_coords = {}
        valid_catchments = Catchment.objects.exclude(centroid__isnull=True).exclude(centroid__exact='')

        for catchment in valid_catchments:
            centroid_str = str(catchment.centroid)

            # Check if it's WKT format 'POINT (Lon Lat)' or old 'Lat, Lon' format
            if 'POINT' in centroid_str:
                coords = self._parse_wkt_point(centroid_str)
            else:
                try:
                    lat, lon = centroid_str.split(',')
                    coords = (float(lat.strip()), float(lon.strip()))
                except ValueError:
                    coords = None

            if coords:
                catchments_with_coords[catchment.id] = coords
            else:
                self.stderr.write(
                    self.style.WARNING(f"Skipping ID {catchment.market_id}: Invalid format '{centroid_str}'"))

        if not catchments_with_coords:
            self.stderr.write(self.style.ERROR("No valid centroids found."))
            return

        self.stdout.write(f"Loaded {len(catchments_with_coords)} market centroids.")

        # 2. Iterate through stores
        stores_to_update = []
        stores = LenskartStore.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True)

        self.stdout.write(f"Processing {stores.count()} stores...")

        for store in stores:
            closest_catchment_id = None
            min_distance = float('inf')

            try:
                store_coords = (float(store.latitude), float(store.longitude))

                for catchment_id, catchment_coords in catchments_with_coords.items():
                    # geodesic expects (Lat, Lon)
                    distance = geodesic(store_coords, catchment_coords).km

                    if distance < min_distance:
                        min_distance = distance
                        closest_catchment_id = catchment_id

                if closest_catchment_id and store.catchment_id != closest_catchment_id:
                    store.catchment_id = closest_catchment_id
                    stores_to_update.append(store)

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Error store {store.store_code}: {e}"))

        # 3. Bulk Update
        if stores_to_update:
            with transaction.atomic():
                # Note: 'catchment' is usually the field name if it's a ForeignKey
                LenskartStore.objects.bulk_update(stores_to_update, ['catchment'])

        self.stdout.write(self.style.SUCCESS(
            f"✅ Mapping complete. Updated {len(stores_to_update)} stores in {time.time() - start_time:.2f}s"))