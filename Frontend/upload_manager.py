# utils/upload_manager.py
import os
import io
import fitz
import logging
from ftplib import FTP_TLS,error_perm,FTP
from uuid import uuid4
from django.conf import settings
from PIL import Image
from django.utils.text import slugify
import asyncio

upload_logger = logging.getLogger("upload_manager")
upload_logger.info("Upload log started")

# مسیر ثابت برای ذخیره‌سازی موقت
TEMP_DIR = settings.TEMP_UPLOAD_DIR


# ---------------------------
# اتصال FTPS
# ---------------------------
# def connect_ftps():
#     try:
#         ftps = FTP_TLS()
#         ftps.connect(settings.FTPS_HOST, settings.FTPS_PORT, timeout=15)
#         ftps.auth()
#         ftps.login(settings.FTPS_USER, settings.FTPS_PASSWORD)
#         ftps.prot_p()
#         return ftps
#     except error_perm as e:
#         upload_logger.error(f"Permission error during FTPS connection: {e}")
#     except TimeoutError as e:
#         upload_logger.error(f"FTPS Connection timed out: {e}")
#     except Exception as e:
#         upload_logger.error(f"Unexpected FTPS error: {e}", exc_info=True)
#     return None

def connect_ftps():
    try:
        ftp = FTP()
        ftp.connect(settings.FTPS_HOST, settings.FTPS_PORT, timeout=15)
        ftp.login(settings.FTPS_USER, settings.FTPS_PASSWORD)
        return ftp
    except error_perm as e:
        upload_logger.error(f"Permission error during FTP connection: {e}")
    except TimeoutError as e:
        upload_logger.error(f"FTP Connection timed out: {e}")
    except Exception as e:
        upload_logger.error(f"Unexpected FTP error: {e}", exc_info=True)
    return None
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
# آپلود مستقیم به FTPS
# ---------------------------
# def upload_to_ftps(file_obj, remote_dir, remote_filename):
#     ext = file_obj.name.split('.')[-1].lower()
#     if not validate_file(file_obj, ext):
#         raise Exception("Invalid or corrupted file uploaded.")

#     # ذخیره موقت
#     os.makedirs(TEMP_DIR, exist_ok=True)
#     temp_file_path = os.path.join(TEMP_DIR, f"{uuid4()}.{ext}")
#     with open(temp_file_path, "wb") as temp_file:
#         for chunk in file_obj.chunks():
#             temp_file.write(chunk)

#     try:
#         ftps = connect_ftps()
#         # ساخت پوشه‌های لازم
#         dirs = remote_dir.strip("/").split("/")
#         current_dir = ""
#         for d in dirs:
#             current_dir += "/" + d
#             try:
#                 ftps.cwd(current_dir)
#             except Exception:
#                 ftps.mkd(current_dir)
#                 ftps.cwd(current_dir)

#         # حذف فایل قبلی اگر وجود داشت
#         try:
#             ftps.delete(remote_filename)
#             upload_logger.info(f">>>> Start Upload - Old file removed: {remote_filename}")
#         except Exception:
#             upload_logger.info(f">>>> Start Upload - No old file found to remove: {remote_filename}")

#         # آپلود
#         upload_logger.info(f"Uploading file: {remote_filename}")
#         with open(temp_file_path, "rb") as f:
#             ftps.storbinary(f"STOR {remote_filename}", f)

#         # اعتبارسنجی فایل روی سرور
#         downloaded = io.BytesIO()
#         ftps.retrbinary(f"RETR {remote_filename}", downloaded.write)
#         downloaded.seek(0)
#         try:
#             if remote_filename.lower().endswith('.pdf'):
#                 fitz.open(stream=downloaded.read(), filetype="pdf").close()
#             else:
#                 Image.open(io.BytesIO(downloaded.read())).verify()
#             upload_logger.info(f"<<<<<<<<Verification passed for {remote_filename}")
#         except Exception:
#             ftps.delete(remote_filename)
#             raise Exception("Uploaded file is corrupted and removed from FTPS")

#         ftps.quit()

#         # حذف فایل موقت
#         if os.path.exists(temp_file_path):
#             os.remove(temp_file_path)

#         # ساخت URL نهایی
#         return f"{settings.FTPS_BASE_URL}/{remote_dir}{remote_filename}"

#     except Exception as e:
#         upload_logger.error(f"Upload failed: {e}")
#         if os.path.exists(temp_file_path):
#             os.remove(temp_file_path)
#         raise


# ---------------------------
# آپلود Async با Retry + Timeout
# ---------------------------
async def upload_to_ftps(file_obj, remote_dir, remote_filename, retries=3, timeout=30):
    upload_logger.info(f">>> Upload Started [{remote_filename}]")
    ext = file_obj.name.split('.')[-1].lower()
    if not validate_file(file_obj, ext):
        raise Exception("Invalid or corrupted file uploaded.")

    # ذخیره فایل موقت
    os.makedirs(TEMP_DIR, exist_ok=True)
    temp_file_path = os.path.join(TEMP_DIR, f"{uuid4()}.{ext}")
    with open(temp_file_path, "wb") as temp_file:
        for chunk in file_obj.chunks():
            temp_file.write(chunk)

    for attempt in range(1, retries + 1):
        try:
            await asyncio.wait_for(asyncio.to_thread(_upload_file_sync, temp_file_path, remote_dir, remote_filename), timeout)
            upload_logger.info(f"<<< Upload successful [{remote_filename}] on attempt {attempt}")
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            return f"{settings.FTPS_BASE_URL}/{remote_dir}{remote_filename}"

        except (asyncio.TimeoutError, Exception) as e:
            upload_logger.error(f"Attempt {attempt} failed for {remote_filename}: {e}")
            if attempt == retries:
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                raise Exception(f"Upload failed after {retries} retries.")

# ---------------------------
# منطق Sync آپلود (برای اجرا در Thread)
# ---------------------------
def _upload_file_sync(local_path, remote_dir, remote_filename):
    ftps = connect_ftps()
    if ftps:
        pass
    else:
        upload_logger.warning(f"FTPS connection could not be established for {remote_filename}")
    # ساخت پوشه‌ها
    dirs = remote_dir.strip("/").split("/")
    current_dir = ""
    for d in dirs:
        current_dir += "/" + d
        try:
            ftps.cwd(current_dir)
        except error_perm:
            ftps.mkd(current_dir)
            ftps.cwd(current_dir)

    # حذف فایل قدیمی
    try:
        ftps.delete(remote_filename)
        upload_logger.info(f">-- Old file removed: {remote_filename}")
    except error_perm:
        pass

    # آپلود
    # with open(local_path, "rb") as f:
    #     ftps.storbinary(f"STOR {remote_filename}", f)
    try:
        with open(local_path, "rb") as f:
            ftps.storbinary(f"STOR {remote_filename}", f)
        # upload_logger.info(f"File uploaded successfully: {remote_filename}")
    except FileNotFoundError:
        upload_logger.error(f"Local file not found: {local_path}")
    except Exception as e:
        upload_logger.error(f"Error during file upload: {e}", exc_info=True)
        
    # اعتبارسنجی فایل روی سرور
    downloaded = io.BytesIO()
    ftps.retrbinary(f"RETR {remote_filename}", downloaded.write)
    downloaded.seek(0)
    try:
        downloaded = io.BytesIO()
        ftps.retrbinary(f"RETR {remote_filename}", downloaded.write)
        downloaded.seek(0)
        # upload_logger.info(f"Remote file retrieved successfully: {remote_filename}")
    except Exception as e:
        upload_logger.error(f"Error during remote file verification {remote_filename}: {e}", exc_info=True)
        
    try:
        if remote_filename.lower().endswith('.pdf'):
            fitz.open(stream=downloaded.read(), filetype="pdf").close()
        else:
            Image.open(io.BytesIO(downloaded.read())).verify()
    except Exception:
        ftps.delete(remote_filename)
        upload_logger.error(f"Verification failed for {remote_filename}")
        raise Exception("Uploaded file is corrupted and removed from FTPS")

    ftps.quit()


# ---------------------------
# مدیریت آدرس آپلود
# ---------------------------
def auto_upload(file_type, instance, file_obj=None, extra_data=None):
    ext = file_obj.name.split('.')[-1] if file_obj else 'file'

    if file_type == "assignment_student":
        group_slug = slugify(instance.assignment.assignment_group.name, allow_unicode=True)
        assignment_slug = slugify(instance.assignment.AssignmentName, allow_unicode=True)
        username = instance.assignment_average_reffer.user.username
        remote_dir = f"Arash-Attar/Assignments/{group_slug}/{assignment_slug}/students/{username}/"
        remote_filename = f"{username}.{ext}"
        remote_created = f"{group_slug}/{assignment_slug}/students/{username}/"
        baseurl = 'https://assignments.arash-attar.com' 

    elif file_type == "assignment_teacher":
        group_slug = slugify(instance.assignment.assignment_group.name, allow_unicode=True)
        assignment_slug = slugify(instance.assignment.AssignmentName, allow_unicode=True)
        username = instance.assignment_average_reffer.user.username
        remote_dir = f"Arash-Attar/Assignments/{group_slug}/{assignment_slug}/students/{username}/"
        remote_filename = f"{username}-marked.{ext}"
        remote_created = f"{group_slug}/{assignment_slug}/students/{username}/"
        baseurl = 'https://assignments.arash-attar.com' 
    
    elif file_type == "assignment":
        group_slug = slugify(instance.assignment_group.name, allow_unicode=True)
        assignment_slug = slugify(instance.AssignmentName, allow_unicode=True)
        assignment_id_slug = slugify(instance.assignment_id, allow_unicode=True)
        remote_dir = f"Arash-Attar/Assignments/{group_slug}/{assignment_slug}/"
        remote_filename = f"{assignment_id_slug}.{ext}"
        remote_created = f"{group_slug}/{assignment_slug}/"
        baseurl = 'https://assignments.arash-attar.com' 
        
    elif file_type == "assignment_answer":
        group_slug = slugify(instance.assignment_group.name, allow_unicode=True)
        assignment_slug = slugify(instance.AssignmentName, allow_unicode=True)
        assignment_id_slug = slugify(instance.assignment_id, allow_unicode=True)
        remote_dir = f"Arash-Attar/Assignments/{group_slug}/{assignment_slug}/"
        remote_filename = f"{assignment_id_slug}-Ans.{ext}"      
        remote_created = f"{group_slug}/{assignment_slug}/"
        baseurl = 'https://assignments.arash-attar.com'  

    elif file_type == "exam_description":
        group_slug = slugify(instance.exam_group.name, allow_unicode=True)
        exam_slug = slugify(instance.ExamName, allow_unicode=True)
        remote_dir = f"Arash-Attar/Exams/{group_slug}/{exam_slug}/"
        remote_filename = f"{exam_slug}-file.{ext}"
        remote_created = f"{group_slug}/{exam_slug}/"
        baseurl = 'https://exams.arash-attar.com'

    elif file_type == "exam_answer":
        group_slug = slugify(instance.exam_group.name, allow_unicode=True)
        exam_slug = slugify(instance.ExamName, allow_unicode=True)
        remote_dir = f"Arash-Attar/Exams/Groups/{group_slug}/{exam_slug}/"
        remote_filename = f"{exam_slug}-Ans.{ext}"
        remote_created = f"Groups/{group_slug}/{exam_slug}/"
        baseurl = 'https://exams.arash-attar.com'

    elif file_type == "question":
        category_slug = slugify(instance.question_category, allow_unicode=True)
        question_id = slugify(instance.question_id)
        remote_dir = f"Arash-Attar/Exams/Questions/{category_slug}/"
        remote_filename = f"{question_id}.{ext}"
        remote_created = f"Questions/{category_slug}/"
        baseurl = 'https://exams.arash-attar.com'

    elif file_type == "question_answer":
        category_slug = slugify(instance.question_category, allow_unicode=True)
        question_id = slugify(instance.question_id)
        remote_dir = f"Arash-Attar/Exams/Questions/{category_slug}/"
        remote_filename = f"{question_id}-Ans.{ext}"
        remote_created = f"Questions/{category_slug}/"
        baseurl = 'https://exams.arash-attar.com'
    else:
        raise ValueError("Invalid file_type")

    # enqueue_upload(file_obj,remote_dir,remote_filename)
    asyncio.run(upload_to_ftps(file_obj, remote_dir, remote_filename))
    
    # return f"{settings.FTPS_BASE_URL}/{remote_dir}{remote_filename}"
    return f"{baseurl}/{remote_created}{remote_filename}"




FTPS_BASE_URL = 'https://center.arash-attar.com'


def move_file_in_ftp(ftps, old_path, new_dir, filename):
    """
    old_path: مسیر فایل فعلی (مثلا 'Classrooms/jalase1.mp4')
    new_dir: پوشه جدید (مثلا 'Classrooms/math-session/jalase1/')
    filename: نام فایل (مثلا 'jalase1.mp4')
    """
    try:
        # ایجاد پوشه‌های مورد نیاز
        for folder in new_dir.split('/'):
            if folder and folder not in ftps.nlst():
                try:
                    ftps.mkd(folder)
                except error_perm:
                    pass
            ftps.cwd(folder)

        # برگرد به ریشه برای rename
        ftps.cwd('/')
        new_path = f"{new_dir}{filename}"

        ftps.rename(old_path, new_path)
        return new_path
    except Exception as e:
        print(f"Error moving file in FTP: {e}")
        return None


def process_content_urls(instance):
    ftps = connect_ftps()
    CLASSROOM_BASE_URL = 'https://classroom.arash-attar.com'
    classroom_headling_slug = slugify(instance.classroom_headline or 'untitled', allow_unicode=True)
    classroom_name_slug = slugify(instance.ClassroomName or 'class', allow_unicode=True)
    remote_created = f"{classroom_headling_slug}/{classroom_name_slug}/"
    new_dir = f"Classrooms/{remote_created}"

    updated_fields = []
    for field in ['content1_url1','content1_url2','content2_url1','content2_url2','content3_url1','content3_url2','content4_url1','content4_url2','content5_url1','content5_url2']:
        filename = getattr(instance, field)
        if filename and not filename.startswith('http'):
            # slugify filename و حفظ پسوند
            ext = os.path.splitext(filename)[-1]
            clean_name = slugify(os.path.splitext(filename)[0], allow_unicode=True) + ext
            old_path = f"Classrooms/{filename}"
            new_path = move_file_in_ftp(ftps, old_path, new_dir, clean_name)

            if new_path:
                full_url = f"{CLASSROOM_BASE_URL}/{remote_created}{clean_name}"
                setattr(instance, field, full_url)
                updated_fields.append(field)

    ftps.quit()
    if updated_fields:
        instance.save(update_fields=updated_fields)
