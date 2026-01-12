from django.contrib import admin
from .models import LenskartStore, ApprovedLenskartStore


# --- LenskartStore Admin ---
@admin.register(LenskartStore)
class LenskartStoreAdmin(admin.ModelAdmin):
    list_display = ('store_code', 'store_name', 'latitude', 'longitude')
    search_fields = ('store_code', 'store_name')


# --- ApprovedLenskartStore Admin ---
@admin.register(ApprovedLenskartStore)
class ApprovedLenskartStoreAdmin(admin.ModelAdmin):
    # What shows up in the main table list
    list_display = (
        'property_id',
        'property_name',
        'kissflow_status',
        'store_size',
        'proposed_rent',
        'geoiq_projected_revenue'
    )

    list_filter = ('kissflow_status', 'latest_approval_date')
    search_fields = ('property_name', 'property_id', 'property_address')
    readonly_fields = ('created_at', 'updated_at')

    # Organizing the detail page into logical sections
    fieldsets = (
        ('Core Identification', {
            'fields': ('property_id', 'property_name', 'property_address', 'kissflow_status', 'latest_approval_date')
        }),
        ('Location Details', {
            'fields': ('latitude', 'longitude', 'market_id', 'market_name')
        }),
        ('Physical Specs (Extracted)', {
            'fields': (
                'store_size',
                'frontage',
                'signage_width',
                'signage_height',
                'ceiling_height',
                'height_from_beam_bottom',
                'trade_area'
            )
        }),
        ('Financials', {
            'fields': ('proposed_rent', 'geoiq_projected_revenue')
        }),
        ('Files & Metadata', {
            'fields': ('ppt_file', 'ppt_url_raw', 'property_created_by_info', 'survey_filled_by_info', 'created_at',
                       'updated_at')
        }),
    )