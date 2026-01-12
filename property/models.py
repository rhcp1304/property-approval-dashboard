from django.db import models


class PropertyRecord(models.Model):
    presentation_date_context = models.CharField(max_length=255)
    ppt_link = models.URLField(max_length=500, unique=True)
    # New fields
    ai_summary_link = models.URLField(max_length=500, null=True, blank=True)
    recording_link = models.URLField(max_length=500, null=True, blank=True)

    status = models.CharField(
        max_length=10,
        choices=[('PENDING', 'Pending'), ('APPROVE', 'Approve'), ('DROP', 'Drop')],
        default='PENDING'
    )
    updated_at = models.DateTimeField(auto_now=True)