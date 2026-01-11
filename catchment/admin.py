from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from .models import Catchment

@admin.register(Catchment)
class CatchmentAdmin(admin.ModelAdmin):
    # --- HELPER METHODS ---

    def display_mapped_stores_count(self, obj):
        """Displays count of existing stores in the list view."""
        return obj.mapped_stores.count()
    display_mapped_stores_count.short_description = 'Stores Count'

    def mapped_stores_list(self, obj):
        """
        Generates a combined HTML list of Existing Stores and
        Approved Properties for the detail view.
        """
        existing_stores = obj.mapped_stores.all()
        approved_properties = obj.approved_lenskart_stores.all()

        if not existing_stores.exists() and not approved_properties.exists():
            return "No Stores or Approved Properties mapped."

        html_output = []

        # 1. Existing Stores Section
        if existing_stores.exists():
            html_output.append("<strong>Existing Stores (Active):</strong><ul style='margin-top:5px;'>")
            for store in existing_stores:
                url = reverse("admin:store_lenskartstore_change", args=[store.pk])
                html_output.append(
                    format_html('<li><a href="{}">{} - {}</a></li>', url, store.store_code, store.store_name)
                )
            html_output.append("</ul>")

        # 2. Approved Properties Section (From API)
        if approved_properties.exists():
            html_output.append("<strong style='color: #264b5d;'>Approved Properties (Kissflow):</strong><ul style='margin-top:5px;'>")
            for prop in approved_properties:
                url = reverse("admin:store_approvedlenskartstore_change", args=[prop.pk])
                html_output.append(
                    format_html('<li><a href="{}">ID: {} - {}</a></li>', url, prop.property_id, prop.property_name or "Unnamed")
                )
            html_output.append("</ul>")

        # JOIN & MARK SAFE: This prevents the 'args or kwargs' TypeError
        return mark_safe("".join(html_output))

    mapped_stores_list.short_description = 'Associated Stores & Properties'

    # --- ADMIN CONFIGURATION ---

    list_display = (
        'market_id',
        'market_name',
        'market_level_name',
        'has_store',
        'display_mapped_stores_count',
        'city',
        'hub_name',
    )

    search_fields = ('market_name', 'market_id', 'city')
    list_filter = ('city', 'circle', 'has_store')

    fieldsets = (
        ('Market Identification', {
            'fields': ('market_id', 'market_name', 'market_level_name')
        }),
        ('Location Details', {
            'fields': ('city', 'circle', 'zone', 'hub_name', 'centroid')
        }),
        ('Status & Mapped Data', {
            'fields': ('has_store', 'mapped_stores_list'),
        }),
        ('Geometry & Info', {
            'fields': ('wkt_geometry', 'additional_info', 'created_at'),
            'classes': ('collapse',),
        }),
    )

    readonly_fields = (
        'wkt_geometry',
        'created_at',
        'centroid',
        'mapped_stores_list'
    )