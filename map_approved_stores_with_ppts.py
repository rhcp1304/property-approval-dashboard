import os, django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'property_approval_dashboard.settings')
django.setup()

from store.models import ApprovedLenskartStore
from property.models import PropertyRecord


def matching_v3_prefix_subset():
    print("🚀 Running Prefix-Subset Match (High Efficiency)...")

    all_stores = ApprovedLenskartStore.objects.all()
    all_ppts = list(PropertyRecord.objects.all())

    updated_count = 0
    already_correct = 0
    no_match_found = 0

    for store in all_stores:
        if not store.latitude or not store.longitude:
            no_match_found += 1
            continue

        # Convert to string and take first 5 chars (e.g., "28.61")
        # This covers the major location and ~1km accuracy
        s_lat_pre = str(store.latitude)[:5]
        s_lng_pre = str(store.longitude)[:5]

        found_ppt = None
        for ppt in all_ppts:
            if not ppt.latitude or not ppt.longitude:
                continue

            p_lat_str = str(ppt.latitude)
            p_lng_str = str(ppt.longitude)

            # Logic: Does the PPT start with the same 5 characters as the store?
            if p_lat_str.startswith(s_lat_pre) and p_lng_str.startswith(s_lng_pre):
                found_ppt = ppt
                break

        if found_ppt:
            if store.source_ppt_id == found_ppt.id:
                already_correct += 1
            else:
                store.source_ppt = found_ppt
                store.save()
                updated_count += 1
                print(f"✅ LINKED: Store {store.property_id} -> PPT {found_ppt.id} (Match: {s_lat_pre})")
        else:
            no_match_found += 1

    print(f"\n" + "=" * 50)
    print(f"TOTAL STORES: {all_stores.count()}")
    print(f"MATCHES FOUND: {updated_count + already_correct}")
    print(f"NO MATCH: {no_match_found}")
    print("=" * 50)


if __name__ == "__main__":
    matching_v3_prefix_subset()