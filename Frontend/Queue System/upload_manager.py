# utils/upload_manager.py
import os
import io
import fitz
import logging
import tempfile
from ftplib import FTP_TLS
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor
from django.conf import settings
from Frontend.models import UploadQueue
from PIL import Image
from .signals import wake_scheduler
from django.utils.text import slugify
from django.db import transaction, IntegrityError

executor = ThreadPoolExecutor(max_workers=5)  # آپلود موازی

upload_logger = logging.getLogger("upload_manager")
upload_logger.info("Upload log started")

# logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)

# مسیر ثابت برای ذخیره‌سازی موقت
TEMP_DIR = settings.TEMP_UPLOAD_DIR


# ---------------------------
# اتصال FTPS
# ---------------------------
def connect_ftps():
    ftps = FTP_TLS()
    ftps.connect(settings.FTPS_HOST, settings.FTPS_PORT, timeout=15)
    ftps.auth()
    ftps.login(settings.FTPS_USER, settings.FTPS_PASSWORD)
    ftps.prot_p()
    return ftps

# ---------------------------
# اعتبارسنجی فایل‌ها
# ---------------------------
def validate_file(file_obj, ext):
    """اعتبارسنجی PDF یا JPG"""
    content = file_obj.read()
    file_obj.seek(0)
    try:
        if ext == 'pdf':
            fitz.open(stream=content, filetype="pdf").close()
            file_obj.seek(0)
        elif ext in ['jpg', 'jpeg', 'png']:
            img = Image.open(io.BytesIO(content))
            img.verify()
        return True
    except Exception as e:
        upload_logger.error(f"File validation failed:{e}")
        return False

# ---------------------------
# پردازش آپلود
# ---------------------------
def process_upload(local_path, remote_dir, remote_filename, queue_obj=None):
    try:
        if queue_obj:
            if queue_obj.status == 'uploading':
                upload_logger.warning(f"Duplicate task detected for {remote_filename}. Skipping...")
                return
            queue_obj.status = 'uploading'
            queue_obj.save(update_fields=['status'])

        if not os.path.exists(local_path):
            upload_logger.error(f"Local file missing for {remote_filename}. Cannot upload.")
            if queue_obj:
                queue_obj.status = 'failed'
                queue_obj.error_message = 'Local file missing'
                queue_obj.save(update_fields=['status', 'error_message'])
            return
        
        upload_logger.info(f"*****Starting upload {remote_filename}")
        ftps = connect_ftps()
        remote_path = f"{remote_dir}{remote_filename}"

        # ساخت پوشه‌های تو در تو در صورت عدم وجود
        # upload_logger.info(f"Checking and creating directories for:{remote_filename}")
        dirs = remote_dir.strip("/").split("/")
        current_dir = ""
        for d in dirs:
            current_dir += "/" + d
            try:
                ftps.cwd(current_dir)
            except Exception:
                try:
                    ftps.mkd(current_dir)
                    ftps.cwd(current_dir)
                except Exception as err:
                    upload_logger.error(f"Failed to create directory:{current_dir} | Error:{err}")
                    raise

        # حذف فایل قبلی اگر وجود دارد
        # old_removed = False
        try:
            ftps.delete(remote_filename)
            # old_removed = True
            upload_logger.info(f"Old file removed:{remote_filename}")
        except Exception:
            upload_logger.info("No old file found to remove.")

        # آپلود فایل جدید
        upload_logger.info(f"Uploading file:{remote_filename}")
        with open(local_path, "rb") as f:
            ftps.storbinary(f"STOR {remote_filename}", f)

        # upload_logger.info(f"Upload completed:{remote_filename},verifying...")

        # تست فایل دانلودی بعد از آپلود
        downloaded = io.BytesIO()
        ftps.retrbinary(f"RETR {remote_filename}", downloaded.write)
        downloaded.seek(0)

        try:
            if remote_filename.lower().endswith('.pdf'):
                fitz.open(stream=downloaded.read(), filetype="pdf").close()
            else:
                Image.open(io.BytesIO(downloaded.read())).verify()
            upload_logger.info(f"Upload completed,Verification passed:{remote_filename}")
        except Exception:
            ftps.delete(remote_filename)
            upload_logger.error(f"Verification failed, file removed from FTPS:{remote_filename}")
            raise Exception("Uploaded file is corrupted and was deleted from FTPS")

        ftps.quit()

        # موفقیت → حذف فایل موقت
        if os.path.exists(local_path):
            os.remove(local_path)
            # upload_logger.info(f"Local temp file removed:{local_path}")
            upload_logger.info(f"Local removed:{remote_filename}")

        if queue_obj:
            # queue_obj.log_message = "Old file removed → New file uploaded" if old_removed else "Uploaded new file successfully"
            queue_obj.delete()

        upload_logger.info(f">>>>>Upload successful:{remote_filename}")
        # wake_scheduler()
        return remote_path

    except Exception as e:
        upload_logger.error(f"Upload failed for {remote_filename} | Error: {e}")
        if queue_obj:
            queue_obj.status = 'failed'
            queue_obj.retries += 1
            queue_obj.error_message = str(e)
            queue_obj.save(update_fields=['status', 'retries', 'error_message'])
        wake_scheduler()
        raise
        
# ---------------------------
# اضافه کردن به صف
# ---------------------------
def enqueue_upload(file_obj, remote_dir, remote_filename):
    temp_dir = tempfile.gettempdir()
    ext = file_obj.name.split('.')[-1].lower()
    temp_file_path = os.path.join(temp_dir, f"{uuid4()}.{ext}")
    
    # بررسی رکورد قبلی
    is_replacement = False
    existing = UploadQueue.objects.filter(remote_dir=remote_dir, remote_filename=remote_filename, status__in=['pending', 'failed']).first()
    if existing:
        if os.path.exists(existing.local_path):
            os.remove(existing.local_path)
        existing.delete()
        is_replacement = True

    # تست فایل قبل از صف
    if not validate_file(file_obj, ext):
        os.remove(temp_file_path)
        raise Exception("Invalid or corrupted file uploaded.")

    # ذخیره فایل در TEMP_UPLOAD_DIR
    os.makedirs(TEMP_DIR, exist_ok=True)
    temp_file_path = os.path.join(TEMP_DIR, remote_filename)
    try:
        with open(temp_file_path, "wb") as temp_file:
            for chunk in file_obj.chunks():
                temp_file.write(chunk)
    except Exception as e:
        # اگر نوشتن روی دیسک شکست خورد → متوقف شو
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise Exception(f"Failed to write temp file: {e}")

    # ثبت در صف
    created=is_replacement
    try:
        with transaction.atomic():
            obj, created = UploadQueue.objects.update_or_create(
                remote_dir=remote_dir,
                remote_filename=remote_filename,
                defaults={
                    'local_path': temp_file_path,
                    'status': 'pending',
                    'is_replacement': not created,
                    'log_message': "File replaced" if not created else "File queued for upload"
                }
            )
        upload_logger.info(f"File queued: {remote_filename} | Replacement: {not created}")    
        wake_scheduler()
        return {"message": "File received successfully and scheduled for upload", "replacement": not created}
    
    except Exception as db_error:
        
        # اگر ثبت در DB شکست خورد → متوقف شو و فایل موقت پاک شود
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path) 
        raise Exception(f"Database insert failed: {db_error}")

# ---------------------------
# آپلود مستقیم به FTPS
# ---------------------------
def upload_to_ftps(file_obj, remote_dir, remote_filename):
    ext = file_obj.name.split('.')[-1].lower()
    if not validate_file(file_obj, ext):
        raise Exception("Invalid or corrupted file uploaded.")

    # ذخیره موقت
    os.makedirs(TEMP_DIR, exist_ok=True)
    temp_file_path = os.path.join(TEMP_DIR, f"{uuid4()}.{ext}")
    with open(temp_file_path, "wb") as temp_file:
        for chunk in file_obj.chunks():
            temp_file.write(chunk)

    try:
        ftps = connect_ftps()
        # remote_path = f"{remote_dir}{remote_filename}"

        # ساخت پوشه‌های لازم
        dirs = remote_dir.strip("/").split("/")
        current_dir = ""
        for d in dirs:
            current_dir += "/" + d
            try:
                ftps.cwd(current_dir)
            except Exception:
                ftps.mkd(current_dir)
                ftps.cwd(current_dir)

        # حذف فایل قبلی اگر وجود داشت
        try:
            ftps.delete(remote_filename)
            upload_logger.info(f">>>> Start Upload - Old file removed: {remote_filename}")
        except Exception:
            upload_logger.info(f">>>> Start Upload - No old file found to remove: {remote_filename}")

        # آپلود
        upload_logger.info(f"Uploading file: {remote_filename}")
        with open(temp_file_path, "rb") as f:
            ftps.storbinary(f"STOR {remote_filename}", f)

        # اعتبارسنجی فایل روی سرور
        downloaded = io.BytesIO()
        ftps.retrbinary(f"RETR {remote_filename}", downloaded.write)
        downloaded.seek(0)
        try:
            if remote_filename.lower().endswith('.pdf'):
                fitz.open(stream=downloaded.read(), filetype="pdf").close()
            else:
                Image.open(io.BytesIO(downloaded.read())).verify()
            upload_logger.info(f"<<<<<<<<Verification passed for {remote_filename}")
        except Exception:
            ftps.delete(remote_filename)
            raise Exception("Uploaded file is corrupted and removed from FTPS")

        ftps.quit()

        # حذف فایل موقت
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

        # ساخت URL نهایی
        return f"{settings.FTPS_BASE_URL}/{remote_dir}{remote_filename}"

    except Exception as e:
        upload_logger.error(f"Upload failed: {e}")
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise

def auto_upload(file_type, instance, file_obj=None, extra_data=None):
    ext = file_obj.name.split('.')[-1] if file_obj else 'file'

    if file_type == "assignment_student":
        group_slug = slugify(instance.assignment.assignment_group.name, allow_unicode=True)
        assignment_slug = slugify(instance.assignment.AssignmentName, allow_unicode=True)
        username = instance.assignment_average_reffer.user.username
        remote_dir = f"Assignments/{group_slug}/{assignment_slug}/students/{username}/"
        remote_filename = f"{username}.{ext}"
        remote_created = f"{group_slug}/{assignment_slug}/students/{username}/"
        baseurl = 'https://assignments.arash-attar.com' 

    elif file_type == "assignment_teacher":
        group_slug = slugify(instance.assignment.assignment_group.name, allow_unicode=True)
        assignment_slug = slugify(instance.assignment.AssignmentName, allow_unicode=True)
        username = instance.assignment_average_reffer.user.username
        remote_dir = f"Assignments/{group_slug}/{assignment_slug}/students/{username}/"
        remote_filename = f"{username}-marked.{ext}"
        remote_created = f"{group_slug}/{assignment_slug}/students/{username}/"
        baseurl = 'https://assignments.arash-attar.com' 
    
    elif file_type == "assignment":
        group_slug = slugify(instance.assignment_group.name, allow_unicode=True)
        assignment_slug = slugify(instance.AssignmentName, allow_unicode=True)
        assignment_id_slug = slugify(instance.assignment_id, allow_unicode=True)
        remote_dir = f"Assignments/{group_slug}/{assignment_slug}/"
        remote_filename = f"{assignment_id_slug}.{ext}"
        remote_created = f"{group_slug}/{assignment_slug}/"
        baseurl = 'https://assignments.arash-attar.com' 
        
    elif file_type == "assignment_answer":
        group_slug = slugify(instance.assignment_group.name, allow_unicode=True)
        assignment_slug = slugify(instance.AssignmentName, allow_unicode=True)
        assignment_id_slug = slugify(instance.assignment_id, allow_unicode=True)
        remote_dir = f"Assignments/{group_slug}/{assignment_slug}/"
        remote_filename = f"{assignment_id_slug}-Ans.{ext}"      
        remote_created = f"{group_slug}/{assignment_slug}/"
        baseurl = 'https://assignments.arash-attar.com'  

    elif file_type == "exam_description":
        group_slug = slugify(instance.assignment.assignment_group.name, allow_unicode=True)
        exam_slug = slugify(instance.ExamName, allow_unicode=True)
        remote_dir = f"Exams/{group_slug}/{exam_slug}/"
        remote_filename = f"{exam_slug}-file.{ext}"
        remote_created = f"{group_slug}/{exam_slug}/"
        baseurl = 'https://exams.arash-attar.com'

    elif file_type == "exam_answer":
        group_slug = slugify(instance.assignment.assignment_group.name, allow_unicode=True)
        exam_slug = slugify(instance.ExamName, allow_unicode=True)
        remote_dir = f"Exams/Groups/{group_slug}/{exam_slug}/"
        remote_filename = f"{exam_slug}-Ans.{ext}"
        remote_created = f"Groups/{group_slug}/{exam_slug}/"
        baseurl = 'https://exams.arash-attar.com'

    elif file_type == "exam_question":
        category_slug = slugify(instance.question_category, allow_unicode=True)
        question_id = extra_data.get("question_id")
        remote_dir = f"Exams/Questions/{category_slug}/"
        remote_filename = f"{question_id}.{ext}"
        remote_created = f"Questions/{category_slug}/"
        baseurl = 'https://exams.arash-attar.com'

    elif file_type == "exam_question_answer":
        category_slug = slugify(instance.question_category, allow_unicode=True)
        question_id = extra_data.get("question_id")
        remote_dir = f"Exams/Questions/{category_slug}/"
        remote_filename = f"{question_id}-Ans.{ext}"
        remote_created = f"Questions/{category_slug}/"
        baseurl = 'https://exams.arash-attar.com'
    else:
        raise ValueError("Invalid file_type")

    # enqueue_upload(file_obj,remote_dir,remote_filename)
    upload_to_ftps(file_obj,remote_dir,remote_filename)
    
    # return f"{settings.FTPS_BASE_URL}/{remote_dir}{remote_filename}"
    return f"{baseurl}/{remote_created}{remote_filename}"