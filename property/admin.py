from django.contrib import admin
from .models import PropertyRecord


@admin.register(PropertyRecord)
class PropertyRecordAdmin(admin.ModelAdmin):
    # Columns to show in the list view
    list_display = ('presentation_date_context', 'status', 'updated_at')

    # Filter sidebar for the Supreme Leader
    list_filter = ('status', 'updated_at')

    # Search bar to find specific folders
    search_fields = ('presentation_date_context',)

    # Allow changing status directly from the list view
    list_editable = ('status',)



