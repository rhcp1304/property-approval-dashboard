from django.db import models
from django.db.models import JSONField
from catchment.models import Catchment

class LenskartStore(models.Model):
    """Stores CORE data and ALL metrics in a single JSON field."""

    # --- CORE STORE DATA FIELDS ---
    store_code = models.CharField(max_length=50, unique=True, verbose_name="Store Code")
    store_name = models.CharField(max_length=255, verbose_name="Store Name")

    # Static fields
    store_address = models.TextField(verbose_name="Store Address", null=True, blank=True)
    finance_op_date = models.CharField(max_length=50, verbose_name="Finance Op.Date", null=True, blank=True)
    opening_month = models.CharField(max_length=50, verbose_name="OPENING MONTH", null=True, blank=True)
    status = models.CharField(max_length=50, verbose_name="STATUS", null=True, blank=True)
    store_close_date = models.CharField(max_length=50, verbose_name="Store Close Date", null=True, blank=True)
    proto = models.CharField(max_length=50, verbose_name="Proto", null=True, blank=True)
    rent = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    format = models.CharField(max_length=50, verbose_name="Format", null=True, blank=True)
    fy = models.CharField(max_length=50, verbose_name="FY", null=True, blank=True)
    area = models.CharField(max_length=50, verbose_name="Area", null=True, blank=True)
    city = models.CharField(max_length=100, verbose_name="City", null=True, blank=True)
    tier = models.CharField(max_length=50, verbose_name="Tier", null=True, blank=True)
    state = models.CharField(max_length=100, verbose_name="State", null=True, blank=True)
    location = models.CharField(max_length=100, verbose_name="Location", null=True, blank=True)
    region = models.CharField(max_length=100, verbose_name="Region", null=True, blank=True)

    # Coordinates
    latitude = models.DecimalField(max_digits=12, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=12, decimal_places=8, null=True, blank=True)
    google_maps_link = models.TextField(verbose_name="Google Maps Link", null=True, blank=True)

    # --- DYNAMIC METRIC FIELD (The change) ---
    metrics_data = JSONField(default=dict, verbose_name="Monthly Performance Metrics")

    # --- RELATIONSHIP ---
    catchment = models.ForeignKey(
        'catchment.Catchment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Mapped Catchment",
        related_name="mapped_stores"  # <--- CRITICAL CHANGE HERE
    )

    def __str__(self):
        return self.store_name

    class Meta:
        db_table = 'lenskart_store'
        verbose_name_plural = "Lenskart Stores"


class ApprovedLenskartStore(models.Model):
    """
    Stores data for potential store locations approved by Kissflow/Survey.
    Complete mapping of all GeoIQ API response fields.
    """
    # --- Identification ---
    property_id = models.IntegerField(unique=True, verbose_name="Property ID")
    property_name = models.CharField(max_length=255, null=True, blank=True)
    property_address = models.TextField(null=True, blank=True)

    # --- Geo Data ---
    latitude = models.DecimalField(max_digits=12, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=12, decimal_places=8, null=True, blank=True)

    # --- Market / Catchment Info ---
    market_id = models.CharField(max_length=255, null=True, blank=True, help_text="Raw Market IDs (e.g. 33441; 33442)")
    market_name = models.TextField(null=True, blank=True, help_text="Full path of the market/catchment")

    # --- Status & Timing ---
    kissflow_status = models.CharField(max_length=100, null=True, blank=True)
    latest_approval_date = models.DateTimeField(null=True, blank=True)

    # --- People Info ---
    property_created_by_info = models.CharField(max_length=255, null=True, blank=True)
    survey_filled_by_info = models.CharField(max_length=255, null=True, blank=True)

    # --- File Handling ---
    ppt_url_raw = models.URLField(max_length=2000, null=True, blank=True)
    ppt_file = models.FileField(upload_to='approved_stores/ppts/%Y/%m/', null=True, blank=True)

    # --- NEW FIELDS (Extracted from PPT) ---
    store_size = models.CharField(max_length=255, null=True, blank=True)
    frontage = models.CharField(max_length=255, null=True, blank=True)
    signage_width = models.CharField(max_length=255, null=True, blank=True)
    signage_height = models.CharField(max_length=255, null=True, blank=True)
    ceiling_height = models.CharField(max_length=255, null=True, blank=True)
    height_from_beam_bottom = models.CharField(max_length=255, null=True, blank=True)
    trade_area = models.CharField(max_length=255, null=True, blank=True)
    proposed_rent = models.CharField(max_length=255, null=True, blank=True)
    geoiq_projected_revenue = models.CharField(max_length=255, null=True, blank=True)

    # --- Internal Timestamps ---
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'approved_lenskart_store'
        verbose_name = "Approved Lenskart Store"
        verbose_name_plural = "Approved Lenskart Stores"
        ordering = ['-property_id']

    def __str__(self):
        return f"[{self.property_id}] {self.property_name or 'Unnamed Property'}"