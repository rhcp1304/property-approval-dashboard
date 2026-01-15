from django.db import models


class PropertyRecord(models.Model):
    # Unique Identifiers
    property_id = models.CharField(max_length=50, null=True, blank=True)

    # --- NEW FIELD: Presentation Date ---
    # Captures the date from parent folders (e.g., "25 Jan 2015")
    presentation_date = models.DateField(null=True, blank=True,
                                         help_text="Extracted from Google Drive folder hierarchy")

    # Granular Market Hierarchy (Extracted from PPT)
    circle = models.CharField(max_length=100, null=True, blank=True)
    hub = models.CharField(max_length=100, null=True, blank=True)
    hub_rank = models.CharField(max_length=20, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    city_rank = models.CharField(max_length=20, null=True, blank=True)

    # Increased max_length for complex names like "South 3_Hyderabad (55∕290)..."
    final_market_name = models.CharField(max_length=500, null=True, blank=True)

    # Captured Metadata
    zone_name = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=50, default='pending')

    # Financial Projections (Extracted from PPT)
    projected_revenue_lakhs = models.CharField(max_length=100, null=True, blank=True)
    total_rent_maintenance = models.CharField(max_length=100, null=True, blank=True)

    # Resource Links
    ppt_link = models.URLField(max_length=1000, null=True, blank=True)
    ai_summary_link = models.URLField(max_length=1000, null=True, blank=True)
    recording_link = models.URLField(max_length=1000, null=True, blank=True)
    first_slide_image_url = models.URLField(max_length=2000, null=True, blank=True)

    # Co-Founder Section
    remarks = models.TextField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-presentation_date', '-created_at']  # Sort by meeting date first
        verbose_name = "Property Record"
        verbose_name_plural = "Property Records"

    def __str__(self):
        date_str = self.presentation_date.strftime('%Y-%m-%d') if self.presentation_date else "No Date"
        return f"[{date_str}] {self.final_market_name or 'Unknown Market'} - {self.status}"