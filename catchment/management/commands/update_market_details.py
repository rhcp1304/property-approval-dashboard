import re
import time
from django.core.management.base import BaseCommand
from django.db import transaction
from catchment_analyzer.models import Catchment

# Regex pattern to find the numbers inside (R/T)
RANK_PATTERN = re.compile(r'\((?P<rank>\d+)\/(?P<total>\d+)\)')


class Command(BaseCommand):
    help = 'Parses the Market_Name field to update all derived fields.'

    def _extract_rank_data(self, part):
        """Helper to extract (R/T) data using regex."""
        match = RANK_PATTERN.search(part)
        if match:
            return int(match.group('rank')), int(match.group('total'))
        return None, None

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Starting comprehensive market detail parsing and update..."))
        start_time = time.time()

        catchments = Catchment.objects.all()

        updates = []
        skip_count = 0

        for catchment in catchments:
            market_name = catchment.market_name
            is_updated = False

            try:
                parts = market_name.split('_')

                # We expect at least four parts: Circle, Hub(R/T), City(R/T), MarketLevel
                if len(parts) >= 4:

                    # --- 1. Extract descriptive fields ---
                    new_circle = parts[0].strip()
                    new_hub_name = parts[1].split('(')[0].strip()
                    new_market_level = parts[-1].strip()

                    # We check if they were pre-loaded correctly, or update them
                    if catchment.circle != new_circle:
                        catchment.circle = new_circle
                        is_updated = True

                    if catchment.hub_name != new_hub_name:
                        catchment.hub_name = new_hub_name
                        is_updated = True

                    if catchment.market_level_name != new_market_level:
                        catchment.market_level_name = new_market_level
                        is_updated = True

                    # --- 2. Extract NEW rank fields ---

                    # From the Hub part (parts[1])
                    hub_rank, hub_total = self._extract_rank_data(parts[1])
                    if hub_rank is not None:
                        if catchment.rank_hub != hub_rank:
                            catchment.rank_hub = hub_rank
                            is_updated = True
                        if catchment.total_hubs != hub_total:
                            catchment.total_hubs = hub_total
                            is_updated = True

                    # From the City part (parts[2])
                    city_rank, city_total = self._extract_rank_data(parts[2])
                    if city_rank is not None:
                        if catchment.rank_city != city_rank:
                            catchment.rank_city = city_rank
                            is_updated = True
                        if catchment.total_city != city_total:
                            catchment.total_city = city_total
                            is_updated = True

                    if is_updated:
                        updates.append(catchment)
                else:
                    self.stderr.write(self.style.WARNING(
                        f"Skipping ID {catchment.market_id}: Market_Name format unrecognizable: {market_name}"
                    ))
                    skip_count += 1

            except Exception as e:
                self.stderr.write(self.style.ERROR(
                    f"Critical error for ID {catchment.market_id} ({market_name}): {e}"
                ))
                skip_count += 1

        # Define all descriptive/rank fields to update
        fields_to_update = [
            'circle', 'hub_name', 'market_level_name',
            'rank_hub', 'total_hubs', 'rank_city', 'total_city'
        ]

        # Save all changes efficiently
        with transaction.atomic():
            Catchment.objects.bulk_update(updates, fields_to_update)

        end_time = time.time()

        self.stdout.write(self.style.SUCCESS(f"✅ Market details update complete."))
        self.stdout.write(f"Updated {len(updates)} records successfully.")
        self.stdout.write(f"Skipped/Errored: {skip_count} records.")
        self.stdout.write(f"Total time taken: {end_time - start_time:.2f} seconds.")