# admin.py
import os
from django.contrib import admin
from .models import UploadQueue
from .upload_manager import process_upload
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=5)

@admin.register(UploadQueue)
class UploadQueueAdmin(admin.ModelAdmin):
    list_display = ('remote_filename', 'status', 'is_replacement', 'retries', 'created_at', 'updated_at')
    list_filter = ('status', 'is_replacement')
    search_fields = ('remote_filename', 'remote_dir')
    readonly_fields = ('local_path', 'remote_dir', 'remote_filename', 'log_message', 'error_message')

    actions = ['retry_upload']

    def retry_upload(self, request, queryset):
        count = 0
        for obj in queryset:
            if obj.status in ['failed', 'pending'] and os.path.exists(obj.local_path):
                obj.status = 'pending'
                obj.log_message = "Retry triggered from Admin Panel"
                obj.save(update_fields=['status', 'log_message'])
                executor.submit(process_upload, obj.local_path, obj.remote_dir, obj.remote_filename, obj)
                count += 1
            else:
                self.message_user(request, f"Cannot retry {obj.remote_filename} (file missing or status not allowed)")
        self.message_user(request, f"Retry started for {count} files")
    retry_upload.short_description = "Retry selected uploads"
