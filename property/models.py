from django.db import models


class PropertyRecord(models.Model):
    # Allowed to be null if the link is missing
    property_id = models.CharField(max_length=50, null=True, blank=True)

    presentation_date_context = models.CharField(max_length=255)
    ppt_link = models.URLField(max_length=500, null=True, blank=True)
    ai_summary_link = models.URLField(max_length=500, null=True, blank=True)
    recording_link = models.URLField(max_length=500, null=True, blank=True)

    # NEW: Stores the Google-hosted thumbnail URL
    first_slide_image_url = models.URLField(max_length=1000, null=True, blank=True)

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Dropped/Rejected', 'Dropped/Rejected'),
        ('Conditionally Approved', 'Conditionally Approved'),
        ('Hold', 'Hold'),
    ]
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.property_id or 'No ID'} - {self.presentation_date_context}"