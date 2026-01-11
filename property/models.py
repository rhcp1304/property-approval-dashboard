from django.db import models


class PropertyRecord(models.Model):
    presentation_date_context = models.CharField(max_length=255)  # Folder name where PPT was found
    ppt_link = models.URLField(max_length=500, unique=True)

    # Veto Status for the Supreme Leader
    status = models.CharField(
        max_length=10,
        choices=[('PENDING', 'Pending'), ('APPROVE', 'Approve'), ('DROP', 'Drop')],
        default='PENDING'
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.presentation_date_context