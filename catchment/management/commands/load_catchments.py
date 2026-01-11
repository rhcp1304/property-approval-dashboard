import csv
import os
import re
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.contrib.gis.geos import GEOSGeometry  # Required for centroid calculation
from catchment.models import Catchment

# Regex pattern to find the numbers inside (R/T)
RANK_PATTERN = re.compile(r'\((?P<rank>\d+)\/(?P<total>\d+)\)')


class Command(BaseCommand):
    """
    Unified Command:
    1. Loads Catchment data from CSV.
    2. Parses Market_Name for rank and level fields.
    3. Calculates Centroid from the WKT geometry.
    """
    help = 'Loads, parses, and calculates centroids for catchment data from a CSV file.'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='The path to the CSV file.')

    def _extract_rank_data(self, part):
        """Helper to extract (R/T) data using regex."""
        match = RANK_PATTERN.search(part)
        if match:
            return int(match.group('rank')), int(match.group('total'))
        return None, None

    def handle(self, *args, **options):
        file_path = options['csv_file']

        if not os.path.exists(file_path):
            raise CommandError(f"File not found at path: {file_path}")

        self.stdout.write(f"Starting combined load, parse, and centroid process for: {file_path}...")

        DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
        records_to_create = []
        skip_count = 0

        with transaction.atomic():
            try:
                with open(file_path, mode='r', encoding='latin-1') as f:
                    # Clean headers to handle potential whitespace
                    headers = [header.strip() for header in f.readline().split(',')]
                    f.seek(0)

                    reader = csv.DictReader(f, fieldnames=headers)
                    next(reader)  # Skip the header row

                    for row in reader:
                        try:
                            # 1. Basic Field Parsing
                            created_at_str = row['Created_At'].split('.')[0]
                            created_at_dt = datetime.strptime(created_at_str, DATE_FORMAT)
                            market_name = row['Market_Name']
                            wkt_geometry = row['Market_Geometry']

                            # 2. Centroid Calculation
                            # Converts WKT string to a GEOS object and finds its center point
                            centroid_point = None
                            if wkt_geometry:
                                centroid_point = GEOSGeometry(wkt_geometry).centroid

                            # 3. Extract logic from Market_Name (Circle_Hub(R/T)_City(R/T)_Level)
                            parts = market_name.split('_')

                            # Default values for parsed fields
                            circle = row['Circle']
                            hub_name = row['Hub_Name']
                            market_level = ""
                            h_rank, h_total = None, None
                            c_rank, c_total = None, None

                            if len(parts) >= 4:
                                circle = parts[0].strip()
                                hub_name = parts[1].split('(')[0].strip()
                                market_level = parts[-1].strip()

                                # Extract Hub Ranks
                                h_rank, h_total = self._extract_rank_data(parts[1])
                                # Extract City Ranks
                                c_rank, c_total = self._extract_rank_data(parts[2])
                            else:
                                self.stderr.write(self.style.WARNING(
                                    f"Row {row.get('Market_ID')}: Market_Name format non-standard."))

                            # 4. Create Model Instance
                            records_to_create.append(
                                Catchment(
                                    market_id=int(row['Market_ID']),
                                    market_name=market_name,
                                    additional_info=row['Additional_Info'],
                                    zone=row['Zone'],
                                    hub_name=hub_name,
                                    circle=circle,
                                    city=row['City'],
                                    created_at=created_at_dt,
                                    wkt_geometry=wkt_geometry,
                                    # Geolocation field
                                    centroid=centroid_point,
                                    # Derived fields
                                    market_level_name=market_level,
                                    rank_hub=h_rank,
                                    total_hubs=h_total,
                                    rank_city=c_rank,
                                    total_city=c_total
                                )
                            )

                        except Exception as e:
                            self.stderr.write(
                                self.style.ERROR(f"Skipping row (ID: {row.get('Market_ID', 'N/A')}). Error: {e}"))
                            skip_count += 1

                    # 5. Efficient Bulk Create
                    Catchment.objects.bulk_create(records_to_create, ignore_conflicts=True)

                    self.stdout.write(self.style.SUCCESS(f"✅ Finished loading, parsing, and centroid population."))
                    self.stdout.write(f"   Successfully imported: {len(records_to_create)} records.")
                    self.stdout.write(f"   Skipped: {skip_count} records.")

            except Exception as e:
                raise CommandError(f"A critical error occurred: {e}")