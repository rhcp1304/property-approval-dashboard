import os
import django

# 1. SETUP DJANGO ENVIRONMENT
# Replace 'your_project_name' with the name of the folder containing settings.py
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'property_approval_dashboard.settings')
django.setup()

from store.models import ApprovedLenskartStore
from property.models import PropertyRecord


def sync_mapping():
    print("--- Starting Sync Process ---")

    # 2. CLEAR OLD LINKS (Optional: ensures a fresh start)
    # We reset everything to rejected/unlinked first
    PropertyRecord.objects.all().update(status='rejected', approved_store=None)
    print("Reset all Property Records to 'rejected' and unlinked.")

    # 3. FETCH ALL APPROVED STORES
    approved_stores = ApprovedLenskartStore.objects.all()
    total_approved = approved_stores.count()
    mapped_count = 0

    print(f"Found {total_approved} Approved Stores in database.")

    # 4. PERFORM MAPPING
    for approved in approved_stores:
        # Match the Integer property_id to the CharField property_id
        # We use str() to ensure the types match for the query
        target_id = str(approved.property_id)

        matches = PropertyRecord.objects.filter(property_id=target_id)

        if matches.exists():
            matches.update(
                approved_store=approved,
                status='approved'
            )
            mapped_count += matches.count()
            print(f"  [MATCH] Linked Property ID {target_id}")

    print("--- Sync Complete ---")
    print(f"Total Property Records Linked: {mapped_count}")


if __name__ == "__main__":
    sync_mapping()