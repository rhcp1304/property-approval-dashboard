import csv
import os
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from catchment.models import Catchment


class Command(BaseCommand):
    """
    A Django management command to load Catchment data from the CSV file.
    Includes fixes for 'latin-1' encoding and robustly handles CSV headers.
    """
    help = 'Loads all catchment data from the specified CSV file.'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='The path to the CSV file.')

    def handle(self, *args, **options):
        file_path = options['csv_file']

        if not os.path.exists(file_path):
            raise CommandError(f"File not found at path: {file_path}")

        self.stdout.write(f"Starting load process for: {file_path}...")

        DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
        records_to_create = []
        skip_count = 0

        with transaction.atomic():
            try:
                with open(file_path, mode='r', encoding='latin-1') as f:

                    # 1. Manually read and clean headers (CRITICAL for non-standard CSVs)
                    headers = [header.strip() for header in f.readline().split(',')]

                    # 2. Reset the file pointer to the beginning
                    f.seek(0)

                    # 3. Initialize DictReader with the clean headers
                    reader = csv.DictReader(f, fieldnames=headers)

                    # 4. Skip the first row (the actual header line)
                    next(reader)

                    for row in reader:
                        try:
                            # Parse Date/Time
                            created_at_str = row['Created_At'].split('.')[0]
                            created_at_dt = datetime.strptime(created_at_str, DATE_FORMAT)

                            # Create Model Instance
                            records_to_create.append(
                                Catchment(
                                    market_id=int(row['Market_ID']),
                                    market_name=row['Market_Name'],
                                    additional_info=row['Additional_Info'],
                                    zone=row['Zone'],
                                    hub_name=row['Hub_Name'],
                                    circle=row['Circle'],
                                    city=row['City'],
                                    created_at=created_at_dt,
                                    wkt_geometry=row['Market_Geometry']
                                    # New fields (centroid, ranks, etc.) will be null initially
                                )
                            )

                        except Exception as e:
                            self.stderr.write(
                                self.style.ERROR(f"Skipping row (ID: {row.get('Market_ID', 'N/A')}). Error: {e}"))
                            skip_count += 1

                    Catchment.objects.bulk_create(records_to_create, ignore_conflicts=True)

                    self.stdout.write(self.style.SUCCESS(f"✅ Finished loading."))
                    self.stdout.write(f"   Successfully imported: {len(records_to_create)} records.")
                    self.stdout.write(f"   Skipped: {skip_count} records.")

            except Exception as e:
                raise CommandError(f"A critical error occurred during file processing: {e}")