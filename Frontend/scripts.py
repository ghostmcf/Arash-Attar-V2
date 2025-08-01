import os
from django.conf import settings
from AssignmentPlatform.models import AssignmentScore,Assignment
from ClassroomsPlatform.models import Classroom
from ExamsPlatform.models import  Exam# فرض میکنیم مدل در فایل assignment/models.py قرار دارد
from django.db import transaction
from django.db.models import Q
from Frontend.upload_manager import connect_ftps,error_perm
import logging
from django.utils.timezone import now, timedelta
from django.contrib.auth.models import Group
import uuid

cleanup_logger = logging.getLogger("orphan_cleanup")

VALID_EXTENSIONS = ('.pdf', '.jpg', '.jpeg', '.png')
    
def reset_assignment_files_to_default():
    """
    برای همه‌ی Assignment: ریست مسیر فایل‌های تکلیف و پاسخ
    و برای AssignmentScore: فقط آن‌هایی که assignment__assignment_permission=True
    مسیر فایل دانش‌آموز و معلم را به useravatar/default-user.jpg ست می‌کند.
    """
    default_path = 'useravatar/default-user.jpg'
    with transaction.atomic():
        # ریست برای همه‌ی Assignment
        Assignment.objects.update(
            assignment_file=default_path,
            assignment_answer_file=default_path
        )
        # ریست فقط آن دسته از AssignmentScore که تکلیف‌شان دسترسی دارد
        AssignmentScore.objects.filter(
            Q(assignment_student_file__isnull=False) & ~Q(assignment_student_file='') |
            Q(assignment_teacher_file__isnull=False) & ~Q(assignment_teacher_file='')
        ).update(
            assignment_student_file=default_path,
            assignment_teacher_file=default_path
        )

from django.contrib.auth.models import User

def temporaryscript():
    User.objects.filter(is_superuser=False).delete()
    Group.objects.all().delete()
    Exam.objects.all().delete()
    Assignment.objects.all().delete()
    Classroom.objects.all().delete()
    

def cfas():
    FAKE_URL = "https://example.com/fakefile.pdf"
    all_groups = Group.objects.all()

    for group in all_groups:
        # ساخت تکلیف
        assignment = Assignment.objects.create(
            assignment_group=group,
            assignment_id=uuid.uuid4(),
            AssignmentName=f"تکلیف گروه {group.name}",
            assignment_headline="موضوع آزمایشی",
            assignment_description="این یک تکلیف تستی برای گروه است.",
            assignment_available_time_start=now(),
            assignment_available_time_end=now() + timedelta(minutes=15),
            assignment_file=FAKE_URL,
            assignment_answer_file=FAKE_URL,
            assignment_extra_score=0
        )

        # ساخت نمره‌های اولیه برای تکلیف
        assignment.create_assignment_score()

        # ویرایش ۱۰ دانش‌آموز اول
        scores = assignment.assignmentscore_set.all()[:10]
        for score in scores:
            score.assignment_student_file = FAKE_URL
            score.assignment_presence = True
            score.assignment_marked = False
            score.assignment_marked_by = ''
            score.assignment_permission=False
            score.save(update_fields=['assignment_student_file', 'assignment_presence', 'assignment_marked', 'assignment_marked_by','assignment_permission'])
    #create fake assignment scores


# def delete_orphaned_files():
#     cleanup_logger.info(">>> Starting orphaned file cleanup for Assignments on FTPS...")
#     ftps = connect_ftps()

#     # 1. استخراج مسیرهای معتبر از دیتابیس و مپ به مسیر FTPS
#     db_files = set()

#     def extract_path(url):
#         if url and 'assignments.arash-attar.com/' in url:
#             return "Assignments/" + url.split('assignments.arash-attar.com/')[-1]
#         return None

#     for url in AssignmentScore.objects.values_list('assignment_student_file', flat=True):
#         path = extract_path(url)
#         if path: db_files.add(path)

#     for url in AssignmentScore.objects.values_list('assignment_teacher_file', flat=True):
#         path = extract_path(url)
#         if path: db_files.add(path)

#     for url in Assignment.objects.values_list('assignment_file', flat=True):
#         path = extract_path(url)
#         if path: db_files.add(path)

#     for url in Assignment.objects.values_list('assignment_answer_file', flat=True):
#         path = extract_path(url)
#         if path: db_files.add(path)

#     cleanup_logger.info(f"Found {len(db_files)} valid file references in DB (Assignments)")

#     # 2. لیست تمام فایل‌های FTPS در مسیر Assignments
#     def list_all_files(path):
#         files = []
#         try:
#             ftps.cwd(path)
#             items = ftps.nlst()
#             for item in items:
#                 if item in ['.', '..', '.ftpquota']:  # نادیده گرفتن فایل‌های سیستمی
#                     continue
#                 full_path = path + item
#                 try:
#                     ftps.cwd(full_path + "/")  # اگر فولدر بود
#                     files += list_all_files(full_path + "/")
#                     ftps.cwd("..")
#                 except Exception:
#                     # فقط فایل‌های با پسوند معتبر
#                     if full_path.lower().endswith(VALID_EXTENSIONS):
#                         files.append(full_path)
#         except Exception:
#             pass
#         return files

#     remote_base_path = "Assignments/"
#     all_files = list_all_files(remote_base_path)
#     cleanup_logger.info(f"Found {len(all_files)} candidate files for deletion check under {remote_base_path}")

#     # 3. مقایسه و حذف فقط فایل‌های معتبر
#     deleted_count = 0
#     for file_path in all_files:
#         if file_path not in db_files:
#             try:
#                 ftps.delete(file_path)
#                 cleanup_logger.info(f"Deleted orphaned file: {file_path}")
#                 deleted_count += 1
#             except error_perm as e:
#                 cleanup_logger.error(f"Permission error deleting {file_path}: {e}")
#             except Exception as e:
#                 cleanup_logger.error(f"Error deleting file {file_path}: {e}")
#         else:
#             # فایل مرتبط است → در لاگ بنویسیم به چه چیزی وصل است
#             cleanup_logger.info(f"File OK: {file_path} -> {file_model_map[file_path]}")        

#     ftps.quit()
#     cleanup_logger.info(f"Cleanup completed. Total orphaned files deleted: {deleted_count}")
    
def delete_orphaned_files():
    cleanup_logger.info(">>> Starting orphaned file cleanup for Assignments on FTPS...")
    ftps = connect_ftps()

    # 1. استخراج مسیرهای معتبر از دیتابیس و مپ به FTPS + مپ مدل‌ها
    db_files = set()
    file_model_map = {}

    def extract_path(url, model_name, field_name, obj_id):
        if url and 'assignments.arash-attar.com/' in url:
            path = "Assignments/" + url.split('assignments.arash-attar.com/')[-1]
            file_model_map[path] = f"{model_name}({obj_id}).{field_name}"
            return path
        return None

    # AssignmentScore Files
    for obj in AssignmentScore.objects.values('id', 'assignment_student_file', 'assignment_teacher_file'):
        if obj['assignment_student_file']:
            path = extract_path(obj['assignment_student_file'], 'AssignmentScore', 'assignment_student_file', obj['id'])
            if path: db_files.add(path)
        if obj['assignment_teacher_file']:
            path = extract_path(obj['assignment_teacher_file'], 'AssignmentScore', 'assignment_teacher_file', obj['id'])
            if path: db_files.add(path)

    # Assignment Files
    for obj in Assignment.objects.values('assignment_id', 'assignment_file', 'assignment_answer_file'):
        if obj['assignment_file']:
            path = extract_path(obj['assignment_file'], 'Assignment', 'assignment_file', obj['assignment_id'])
            if path: db_files.add(path)
        if obj['assignment_answer_file']:
            path = extract_path(obj['assignment_answer_file'], 'Assignment', 'assignment_answer_file', obj['assignment_id'])
            if path: db_files.add(path)

    cleanup_logger.info(f"Found {len(db_files)} valid file references in DB (Assignments)")

    # 2. لیست تمام فایل‌های FTPS در مسیر Assignments
    def list_all_files(path):
        files = []
        try:
            ftps.cwd(path)
            items = ftps.nlst()
            for item in items:
                if item in ['.', '..', '.ftpquota']:
                    continue
                full_path = path + item
                try:
                    ftps.cwd(full_path + "/")  # اگر فولدر بود
                    files += list_all_files(full_path + "/")
                    ftps.cwd("..")
                except Exception:
                    if full_path.lower().endswith(VALID_EXTENSIONS):
                        files.append(full_path)
        except Exception:
            pass
        return files

    remote_base_path = "Assignments/"
    all_files = list_all_files(remote_base_path)
    cleanup_logger.info(f"Found {len(all_files)} candidate files for deletion check under {remote_base_path}")

    # 3. مقایسه و حذف فایل‌های بی‌صاحب
    deleted_count = 0
    for file_path in all_files:
        if file_path not in db_files:
            try:
                ftps.delete(file_path)
                cleanup_logger.info(f"Deleted orphaned file: {file_path} (NO DB Reference)")
                deleted_count += 1
            except error_perm as e:
                cleanup_logger.error(f"Permission error deleting {file_path}: {e}")
            except Exception as e:
                cleanup_logger.error(f"Error deleting file {file_path}: {e}")
        else:
            # فایل مرتبط است → در لاگ بنویسیم به چه چیزی وصل است
            cleanup_logger.info(f"File OK: {file_path} -> {file_model_map[file_path]}")

    ftps.quit()
    cleanup_logger.info(f"Cleanup completed for Assignments. Total orphaned files deleted: {deleted_count}")    
    
def debug_list_assignments():
    cleanup_logger.info(">>> Starting DEBUG scan for Assignments on FTPS...")
    ftps = connect_ftps()

    visited_dirs = []
    all_files = []

    def list_all(current_path):
        try:
            ftps.cwd(current_path)
            cleanup_logger.info(f"[DIR] Entering: {current_path}")
            visited_dirs.append(current_path)

            items = ftps.nlst()
            cleanup_logger.info(f"[DIR] {current_path} contains: {items}")

            for item in items:
                if item in ['.', '..', '.ftpquota']:
                    continue

                try:
                    ftps.cwd(item)  # تست آیا فولدر است
                    # اگر موفق شد → بازگشت به فولدر اصلی بعد از پیمایش
                    list_all(current_path + item + "/")
                    ftps.cwd("..")
                except Exception:
                    # اگر نتوانست وارد شود → فایل است
                    full_path = current_path + item
                    cleanup_logger.info(f"[FILE] {full_path}")
                    all_files.append(full_path)

        except Exception as e:
            cleanup_logger.error(f"Error accessing {current_path}: {e}")

    base_path = "Assignments/"
    list_all(base_path)

    cleanup_logger.info(f"DEBUG Summary: {len(visited_dirs)} folders visited, {len(all_files)} files found.")
    cleanup_logger.info(f"Visited folders: {visited_dirs}")
    cleanup_logger.info(f"All files: {all_files}")

    ftps.quit()
    cleanup_logger.info(">>> DEBUG scan completed.")

    