from django.contrib import admin
from django.utils.html import format_html
from .models import LenskartStore, ApprovedLenskartStore


class LenskartStoreAdmin(admin.ModelAdmin):
    list_display = (
        'store_code',
        'store_name',
        'catchment',
        'latitude',
        'longitude'
    )
    list_filter = (
        'catchment',
    )
    search_fields = (
        'store_code',
        'store_name',
        'catchment__market_name'
    )

    # ADDED: Fieldsets to organize store details and include the new JSONField
    fieldsets = (
        ('Core Identification & Location', {
            'fields': ('store_code', 'store_name', 'catchment', 'city', 'state', 'location', 'region')
        }),
        ('Geospatial Data', {
            'fields': ('latitude', 'longitude', 'google_maps_link')
        }),
        ('Financial & Operational Details', {
            'fields': ('finance_op_date', 'opening_month', 'status', 'store_close_date', 'rent', 'fy', 'proto', 'format', 'area', 'tier')
        }),
        ('Monthly Performance Metrics', {
            # ADDED: The new JSONField. Collapsed for cleanliness.
            'fields': ('metrics_data',),
            'classes': ('collapse',),
        }),
    )


# ----------------------------------------------------------------------

# --- ApprovedLenskartStore Model Admin ---

class ApprovedLenskartStoreAdmin(admin.ModelAdmin):
    list_display = (
        'property_id',
        'property_name',
        'latitude',
        'longitude',
        'kissflow_status',
        'display_catchments_count',
    )
    list_filter = (
        'kissflow_status',
        'catchments',
    )
    search_fields = (
        'property_name',
        'property_address',
        'property_id',
        'catchments__market_name',
    )

    # Helper function to display the count of mapped catchments
    def display_catchments_count(self, obj):
        # We use obj.catchments.count() for ManyToMany relationship
        return obj.catchments.count()

    display_catchments_count.short_description = 'Mapped Catchments'


# --- Registration ---

admin.site.register(LenskartStore, LenskartStoreAdmin)
admin.site.register(ApprovedLenskartStore, ApprovedLenskartStoreAdmin)