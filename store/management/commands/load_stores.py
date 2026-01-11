import csv
import os
from decimal import Decimal
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import DecimalField, FloatField
from store.models import LenskartStore
from catchment.models import Catchment


# --- HELPER FUNCTIONS FOR DATA CLEANING ---
def safe_convert_to_decimal(value, default=None):
    if not value or str(value).strip() in ['-', '', 'None']:
        return default
    try:
        cleaned = str(value).replace(',', '').strip()
        return Decimal(cleaned)
    except:
        return default


def safe_convert_to_float(value, default=None):
    if not value or str(value).strip() in ['-', '', 'None']:
        return default
    try:
        cleaned = str(value).strip().replace('%', '').replace(',', '')
        return float(cleaned)
    except:
        return default


class Command(BaseCommand):
    help = 'Comprehensive loader for Lenskart Store Master CSV with all metadata and metrics.'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the Master CSV file.')

    def handle(self, *args, **options):
        file_path = options['csv_file']
        if not os.path.exists(file_path):
            raise CommandError(f"File not found: {file_path}")

        # Pre-fetch catchments for linking
        catchment_map = {c.city.upper(): c for c in Catchment.objects.all() if c.city}

        self.stdout.write(self.style.NOTICE("Mapping Comprehensive Headers..."))

        try:
            with open(file_path, mode='r', encoding='latin-1') as f:
                reader = csv.reader(f)
                row = next(reader)
                # Handle leading empty rows
                if not any(row): row = next(reader)

                header_groups = row
                header_main = next(reader)
        except Exception as e:
            raise CommandError(f"Failed to read headers: {e}")

        # --- 1. COMPREHENSIVE FIELD MAPPING ---
        # Map indices for ALL metadata fields mentioned
        idx_map = {}
        target_fields = {
            'code': 'Store Code',
            'name': 'Store Name',
            'addr': 'Store Address',
            'lat': 'Latitude',
            'lng': 'Longitude',
            'finance_date': ' Finance Op.Date',  # Note the leading space often found in this CSV
            'open_month': 'OPENING MONTH',
            'status': 'STATUS',
            'close_date': 'Store Close Date',
            'proto': 'Proto',
            'rent': 'Rent',
            'format': 'Format',
            'fy': 'FY',
            'area': 'Area',
            'city': 'City',
            'tier': 'Tier',
            'state': 'State',
            'location': 'Location',
            'region': 'Region'
        }

        for key, csv_col in target_fields.items():
            try:
                # Try exact match, then case-insensitive
                if csv_col in header_main:
                    idx_map[key] = header_main.index(csv_col)
                else:
                    idx_map[key] = [h.strip().lower() for h in header_main].index(csv_col.strip().lower())
            except ValueError:
                idx_map[key] = -1  # Field not found

        # --- 2. DYNAMIC METRIC MAPPING ---
        metric_column_map = {}
        for i, col_name in enumerate(header_main):
            if '-' in col_name and any(char.isdigit() for char in col_name):
                group = header_groups[i].strip() if i < len(header_groups) else ""
                if col_name not in metric_column_map:
                    metric_column_map[col_name] = {}

                if "Sale" in group:
                    metric_column_map[col_name]['sales'] = i
                elif "Footfall" in group:
                    metric_column_map[col_name]['footfall'] = i
                elif "Order" in group:
                    metric_column_map[col_name]['orders'] = i
                elif "Conversion" in group:
                    metric_column_map[col_name]['conversion'] = i

        # --- 3. DATA LOADING ---
        store_records = []
        skip_count = 0

        with open(file_path, mode='r', encoding='latin-1') as f:
            reader = csv.reader(f)
            # Skip the specific header rows found during mapping
            for _ in range(3): next(reader, None)

            for row in reader:
                if not row or idx_map['code'] >= len(row) or not row[idx_map['code']].strip():
                    continue

                try:
                    # Dynamic Metrics Parsing
                    metrics_json = {}
                    for month, cols in metric_column_map.items():
                        m_data = {
                            "sales": str(safe_convert_to_decimal(row[cols['sales']])) if 'sales' in cols else None,
                            "footfall": str(
                                safe_convert_to_decimal(row[cols['footfall']])) if 'footfall' in cols else None,
                            "orders": str(safe_convert_to_decimal(row[cols['orders']])) if 'orders' in cols else None,
                            "conversion": safe_convert_to_float(
                                row[cols['conversion']]) if 'conversion' in cols else None,
                        }
                        if any(v is not None for v in m_data.values()):
                            metrics_json[month] = m_data

                    # Build the model using all mapped indices
                    def get_val(key):
                        return row[idx_map[key]].strip() if idx_map[key] != -1 and idx_map[key] < len(row) else None

                    city_val = get_val('city')

                    store_obj = LenskartStore(
                        store_code=get_val('code'),
                        store_name=get_val('name'),
                        store_address=get_val('addr'),
                        latitude=safe_convert_to_decimal(get_val('lat')),
                        longitude=safe_convert_to_decimal(get_val('lng')),
                        finance_op_date=get_val('finance_date'),
                        opening_month=get_val('open_month'),
                        status=get_val('status'),
                        store_close_date=get_val('close_date'),
                        proto=get_val('proto'),
                        rent=safe_convert_to_decimal(get_val('rent')),
                        format=get_val('format'),
                        fy=get_val('fy'),
                        area=get_val('area'),
                        city=city_val,
                        tier=get_val('tier'),
                        state=get_val('state'),
                        location=get_val('location'),
                        region=get_val('region'),
                        metrics_data=metrics_json,
                        catchment=catchment_map.get(city_val.upper()) if city_val else None
                    )
                    store_records.append(store_obj)

                except Exception as e:
                    self.stderr.write(f"Error processing store {row[0] if row else 'UNK'}: {e}")
                    skip_count += 1

        # --- 4. BULK SAVE ---
        if store_records:
            fields_to_update = [
                'store_name', 'store_address', 'latitude', 'longitude',
                'finance_op_date', 'opening_month', 'status', 'store_close_date',
                'proto', 'rent', 'format', 'fy', 'area', 'city', 'tier',
                'state', 'location', 'region', 'metrics_data', 'catchment'
            ]
            with transaction.atomic():
                LenskartStore.objects.bulk_create(
                    store_records,
                    update_conflicts=True,
                    unique_fields=['store_code'],
                    update_fields=fields_to_update
                )

        self.stdout.write(self.style.SUCCESS(f"✅ Loaded {len(store_records)} stores. Skipped {skip_count}."))