from django.db import models


class Catchment(models.Model):
    """Model storing all CSV data and calculated/derived fields."""

    # Core CSV Fields
    market_id = models.IntegerField(unique=True, verbose_name="Market ID")
    market_name = models.CharField(max_length=255, verbose_name="Market Name")
    additional_info = models.TextField(verbose_name="Additional Info")
    zone = models.CharField(max_length=100)
    wkt_geometry = models.TextField(verbose_name="WKT Geometry")
    created_at = models.DateTimeField(verbose_name="Created At")

    # Fields pre-loaded from CSV but used for parsing
    hub_name = models.CharField(max_length=100, verbose_name="Hub Name")
    circle = models.CharField(max_length=100)
    city = models.CharField(max_length=100)

    # Derived Geospatial Field
    centroid = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="Calculated Centroid (Lat, Lon)"
    )

    # Derived Descriptive Fields (from market_name parsing)
    market_level_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Market Level Name"
    )
    rank_hub = models.IntegerField(null=True, blank=True, verbose_name="Hub Rank")
    total_hubs = models.IntegerField(null=True, blank=True, verbose_name="Total Hubs in Circle")
    rank_city = models.IntegerField(null=True, blank=True, verbose_name="City Rank")
    total_city = models.IntegerField(null=True, blank=True, verbose_name="Total Cities in Hub")

    # Derived Flag Field
    has_store = models.BooleanField(
        default=False,
        verbose_name="Has Associated Lenskart Store"
    )

    def __str__(self):
        return self.market_name

    class Meta:
        db_table = 'catchments'
        verbose_name_plural = "Catchments"
