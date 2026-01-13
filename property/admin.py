from django.contrib import admin
from .models import PropertyRecord

@admin.register(PropertyRecord)
class PropertyRecordAdmin(admin.ModelAdmin):
    # Columns to show in the list view
    # Added property_id as the first column
    list_display = ('property_id', 'status', 'updated_at', 'presentation_date_context')

    # Filter sidebar
    list_filter = ('status', 'updated_at')

    # Search bar (searching by property ID or folder name)
    search_fields = ('property_id', 'presentation_date_context')

    # Allow changing status directly from the list view
    list_editable = ('status',)