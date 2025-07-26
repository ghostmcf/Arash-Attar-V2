from django.db import models

# models.py
class UploadQueue(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('uploading', 'Uploading'),
        ('failed', 'Failed')
    )

    local_path = models.CharField(max_length=500)  # مسیر فایل موقت
    remote_dir = models.CharField(max_length=191)
    remote_filename = models.CharField(max_length=191)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    retries = models.IntegerField(default=0)
    error_message = models.TextField(blank=True, null=True)
    is_replacement = models.BooleanField(default=False)
    log_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['remote_dir', 'remote_filename'], name='unique_upload_target')
        ]

    def __str__(self):
        return f"{self.remote_dir}{self.remote_filename} - {self.status}"
    
    