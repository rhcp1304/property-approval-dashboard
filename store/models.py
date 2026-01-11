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
    """Stores data for potential store locations approved by Kissflow/Survey."""

    property_id = models.IntegerField(unique=True, verbose_name="Property ID")
    property_name = models.CharField(max_length=255, verbose_name="Property Name", null=True, blank=True)
    property_address = models.TextField(verbose_name="Address", null=True, blank=True)

    # Coordinates for spatial analysis
    latitude = models.DecimalField(max_digits=12, decimal_places=8, null=True, blank=True, verbose_name="Latitude")
    longitude = models.DecimalField(max_digits=12, decimal_places=8, null=True, blank=True, verbose_name="Longitude")

    # Raw string field to store the original semicolon-separated Market IDs from the CSV
    market_ids_raw = models.TextField(verbose_name="Raw Market IDs (CSV)", null=True, blank=True)

    kissflow_status = models.CharField(max_length=50, verbose_name="Kissflow Status")

    # Many-to-Many relationship with Catchment
    catchments = models.ManyToManyField(
        'catchment.Catchment',
        related_name='approved_lenskart_stores',
        verbose_name="Mapped Catchments"
    )

    def __str__(self):
        return f"Approved Store {self.property_id}: {self.property_name or self.property_address}"

    class Meta:
        db_table = 'approved_lenskart_store'
        verbose_name_plural = "Approved Lenskart Stores"