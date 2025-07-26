import os
from django.conf import settings
from AssignmentPlatform.models import AssignmentScore,Assignment  # فرض میکنیم مدل در فایل assignment/models.py قرار دارد
from django.db import transaction
from django.db.models import Q
from Frontend.upload_manager import connect_ftps,upload_logger,error_perm

VALID_EXTENSIONS = ('.pdf', '.jpg', '.jpeg', '.png')

def identify_orphaned_files():
    # دریافت مسیر تمامی فایل‌های موجود در مدل AssignmentScore
    student_files = AssignmentScore.objects.values_list('assignment_student_file', flat=True)

    # ایجاد یک مجموعه از مسیر فایل‌های فعلی برای دسترسی سریع‌تر
    referenced_files = set(os.path.join(settings.MEDIA_ROOT, file) for file in student_files if file)

    # مسیر پایه فولدر فایل‌های تکالیف دانش‌آموزان (به غیر از فولدر answers)
    base_path = os.path.join(settings.MEDIA_ROOT, 'assignment/students/')

    # ایجاد یا باز کردن فایل متنی برای ذخیره مسیر فایل‌های یتیم
    output_file_path = os.path.join(settings.BASE_DIR, 'orphaned_files.txt')
    with open(output_file_path, 'w') as output_file:
        # پیمایش در تمامی فایل‌های موجود در فولدر تکالیف دانش‌آموزان (غیر از answers)
        for root, dirs, files in os.walk(base_path):
            # نادیده گرفتن فولدر 'answers'
            if 'answers' in root:
                continue

            for file in files:
                file_path = os.path.join(root, file)

                # اگر فایل در مجموعه فایل‌های ارجاع‌شده در پایگاه داده وجود نداشت، مسیر آن را در فایل متنی ذخیره کن
                if file_path not in referenced_files:
                    output_file.write(f"{file_path} | {file}\n")
                    print(f"Identified orphaned file: {file_path}")

    print(f"Orphaned file paths written to {output_file_path}")


def delete_orphaned_files():
    # دریافت مسیر تمامی فایل‌های موجود در مدل AssignmentScore
    student_files = AssignmentScore.objects.values_list('assignment_student_file', flat=True)

    # ایجاد یک مجموعه از مسیر فایل‌های فعلی برای دسترسی سریع‌تر
    referenced_files = set(os.path.join(settings.MEDIA_ROOT, file) for file in student_files if file)

    # مسیر پایه فولدر فایل‌های تکالیف دانش‌آموزان (به غیر از فولدر answers)
    base_path = os.path.join(settings.MEDIA_ROOT, 'assignment/students/')

    # ایجاد یا باز کردن فایل متنی برای ذخیره مسیر فایل‌های حذف‌شده
    deleted_files_log_path = os.path.join(settings.BASE_DIR, 'deleted_files.txt')
    with open(deleted_files_log_path, 'w') as log_file:
        # شمارنده برای شمارش تعداد فایل‌های حذف شده
        deleted_count = 0

        # پیمایش در تمامی فایل‌های موجود در فولدر تکالیف دانش‌آموزان (غیر از answers)
        for root, dirs, files in os.walk(base_path):
            # نادیده گرفتن فولدر 'answers'
            if 'answers' in root:
                continue

            for file in files:
                file_path = os.path.join(root, file)

                # اگر فایل در مجموعه فایل‌های ارجاع‌شده در پایگاه داده وجود نداشت، آن را حذف کن
                if file_path not in referenced_files:
                    try:
                        # بررسی مسیر فایل و مجوز دسترسی قبل از حذف
                        if os.path.exists(file_path):
                            if os.access(file_path, os.W_OK):
                                os.remove(file_path)
                                deleted_count += 1

                                # نوشتن نام و مسیر فایل حذف شده در فایل لاگ
                                log_file.write(f"{file_path} | {file}\n")

                                # چاپ پیغام برای هر فایل حذف شده
                                print(f"Deleted orphaned file: {file_path}")
                            else:
                                print(f"Permission denied for deleting file: {file_path}")
                        else:
                            print(f"File does not exist: {file_path}")
                    except Exception as e:
                        print(f"Error deleting file {file_path}: {e}")

    print(f"Total orphaned files deleted: {deleted_count}")
    print(f"Deleted file paths written to {deleted_files_log_path}")
    
    
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

def temporaryscript():
    pass        

# @api_view(['GET'])
# @permission_classes([IsAdminUser])
# def invalidate_authenticated_users(request):
#     """حذف نشست‌های کاربران لاگین‌شده و حفظ نشست کاربران مهمان"""
#     logged_in_users = User.objects.filter(is_active=True)
#     sessions = Session.objects.filter(session_key__in=[
#         s.session_key for s in Session.objects.all() if "_auth_user_id" in s.get_decoded()
#     ])
#     sessions.delete()
#     return Response({"message": "نشست‌های کاربران احراز هویت‌شده حذف شد."}, status=status.HTTP_400_BAD_REQUEST)