import csv
import os
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import DecimalField, FloatField
from store.models import LenskartStore
from catchment.models import Catchment


# --- HELPER FUNCTIONS ---
def safe_convert_to_decimal(value, default=None):
    if not value or str(value).strip() in ['-', '', 'None']:
        return default
    try:
        clean_val = str(value).strip().replace(',', '')
        return DecimalField.to_python(DecimalField(), clean_val)
    except Exception:
        return default


def safe_convert_to_float(value, default=None):
    if not value or str(value).strip() in ['-', '', 'None']:
        return default
    try:
        cleaned_value = str(value).strip().replace('%', '').replace(',', '')
        return FloatField.to_python(FloatField(), cleaned_value)
    except Exception:
        return default


class Command(BaseCommand):
    help = 'Loads store data from CSV, skipping the first two filler rows.'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the Store Master CSV.')

    def handle(self, *args, **options):
        file_path = options['csv_file']
        if not os.path.exists(file_path):
            raise CommandError(f"File not found: {file_path}")

        self.stdout.write(self.style.NOTICE(f"Starting import from: {file_path}"))

        # Pre-fetch catchments to avoid N+1 queries
        catchment_map = {c.city.upper(): c for c in Catchment.objects.all() if c.city}

        try:
            with open(file_path, mode='r', encoding='latin-1') as f:
                # SKIP THE FIRST TWO ROWS (Filler and Group Headers)
                next(f)  # Row 1: empty commas
                next(f)  # Row 2: "Sale FY-20", etc.

                # ROW 3 IS THE ACTUAL HEADER
                reader = csv.DictReader(f)

                # Identify the dynamic months from the headers
                # Looking for patterns like "Apr-24" in the actual column names
                all_headers = reader.fieldnames

                # Strategy: Find "SALES - Apr-24" etc by scanning headers
                # Or use your index logic if the file is strictly formatted
                dynamic_months = []
                for header in all_headers:
                    if "SALES - " in header:
                        month_name = header.replace("SALES - ", "").strip()
                        dynamic_months.append(month_name)

                store_records = []
                skip_count = 0

                with transaction.atomic():
                    for row in reader:
                        store_code = row.get('Store Code', '').strip()
                        if not store_code or store_code == '-':
                            continue

                        try:
                            # 1. Map Metrics to JSON
                            metrics_data = {}
                            for month in dynamic_months:
                                m_data = {}
                                # Sales, Footfall, Orders
                                for m_type in ['SALES', 'FOOTFALL', 'ORDERS']:
                                    key = f"{m_type} - {month}"
                                    val = safe_convert_to_decimal(row.get(key))
                                    m_data[m_type.lower()] = str(val) if val is not None else None

                                # Conversion
                                conv_key = f"CONVERSION - {month}"
                                conv = safe_convert_to_float(row.get(conv_key))
                                m_data['conversion'] = float(conv) if conv is not None else None

                                metrics_data[month] = m_data

                            # 2. Assign Core Fields
                            city_val = row.get('City', '').strip()

                            store_obj = LenskartStore(
                                store_code=store_code,
                                store_name=row.get('Store Name'),
                                store_address=row.get('Store Address'),
                                finance_op_date=row.get('Finance Op.Date'),
                                opening_month=row.get('OPENING MONTH'),
                                status=row.get('STATUS'),
                                store_close_date=row.get('Store Close Date'),
                                proto=row.get('Proto'),
                                format=row.get('Format'),
                                fy=row.get('FY'),
                                area=row.get('Area'),
                                city=city_val,
                                tier=row.get('Tier'),
                                state=row.get('State'),
                                location=row.get('Location'),
                                region=row.get('Region'),
                                google_maps_link=row.get('Google Maps Link'),
                                rent=safe_convert_to_decimal(row.get('Rent')),
                                latitude=safe_convert_to_decimal(row.get('Latitude')),
                                longitude=safe_convert_to_decimal(row.get('Longitude')),
                                metrics_data=metrics_data,
                                catchment=catchment_map.get(city_val.upper())
                            )
                            store_records.append(store_obj)

                        except Exception as e:
                            self.stderr.write(f"Error processing row {store_code}: {e}")
                            skip_count += 1

                # 3. Bulk Upsert
                if store_records:
                    # Automatically get fields to update (exclude PK and unique store_code)
                    update_fields = [
                        f.name for f in LenskartStore._meta.get_fields()
                        if f.concrete and not f.primary_key and f.name != 'store_code'
                    ]

                    LenskartStore.objects.bulk_create(
                        store_records,
                        update_conflicts=True,
                        unique_fields=['store_code'],
                        update_fields=update_fields
                    )

                self.stdout.write(self.style.SUCCESS(
                    f"✅ Successfully processed {len(store_records)} stores. Skipped: {skip_count}"
                ))

        except Exception as e:
            raise CommandError(f"Fatal error during CSV read: {e}")