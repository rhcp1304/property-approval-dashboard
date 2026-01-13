from django.contrib import admin
from .models import PropertyRecord

@admin.register(PropertyRecord)
class PropertyRecordAdmin(admin.ModelAdmin):
    # Replaced 'market_name' with the new granular fields
    list_display = (
        'property_id',
        'circle',
        'hub',
        'hub_rank',
        'city',
        'city_rank',
        'final_market_name',
        'status',
        'updated_at'
    )

    # Added filters for easier navigation
    list_filter = ('circle', 'hub', 'status', 'zone_name')

    # Search by ID or the specific market names
    search_fields = ('property_id', 'final_market_name', 'hub', 'city')

    # Allow status editing directly from the list
    list_editable = ('status',)