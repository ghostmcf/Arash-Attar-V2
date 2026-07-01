"""منطق بایگانی پایان سال تحصیلی (مستقل از HTTP؛ از management command صدا زده می‌شود)."""
import logging

import jdatetime
from django.contrib.auth.models import User, Group
from django.db import transaction

from StudentsInfo.models import StudentYearRecord, YearExamRecord, YearAssignmentRecord, StudentUser
from ExamsPlatform.models import Exam, ExamAverage
from AssignmentPlatform.models import Assignment, AssignmentAverage
from ClassroomsPlatform.models import Classroom, ClassroomAverage

logger = logging.getLogger('management_logger')


def current_study_year():
    """سال تحصیلی جلالی جاری به‌صورت 'YYYY-YYYY' (سال تحصیلی از مهر شروع می‌شود)."""
    today = jdatetime.date.today()
    jy = today.year
    return f"{jy}-{jy+1}" if today.month >= 7 else f"{jy-1}-{jy}"


def archive_academic_year(study_year=None, actor='cli'):
    """
    بایگانی پایان سال (اتمیک):
      ۱) برای هر دانش‌آموز StudentYearRecord + جزئیات تک‌تک امتحان/تکلیف.
      ۲) همه‌ی دانش‌آموزها غیرفعال می‌شوند (اکسل سال جدید برگشتی‌ها را فعال می‌کند).
      ۳) Exam/Assignment/Classroom/Group و سه مدل Average پاک می‌شوند (Scoreها با CASCADE).
    خروجی: dict شامل study_year و تعداد رکوردهای بایگانی‌شده.
    """
    study_year = (study_year or '').strip() or current_study_year()
    archived = 0

    with transaction.atomic():
        students = User.objects.filter(is_staff=False)
        for user in students:
            group        = user.groups.first()
            su           = StudentUser.objects.filter(student_user=user).first()
            exam_avg     = ExamAverage.objects.filter(user=user).first()
            assign_avg   = AssignmentAverage.objects.filter(user=user).first()
            class_avg    = ClassroomAverage.objects.filter(user=user).first()

            # تازه‌سازی میانگین‌ها قبل از اسنپ‌شات
            if exam_avg:   exam_avg.get_average()
            if assign_avg: assign_avg.get_average()
            if class_avg:  class_avg.get_absence()

            grade        = (group.group_grade if group else None) or (su.student_grade if su else None)
            group_name   = group.name if group else None
            student_type = su.student_type if su else None
            year_status  = 'فارغ التحصیل' if grade == 'دوازدهم' else 'در حال تحصیل'

            rec, _ = StudentYearRecord.objects.update_or_create(
                student=user, study_year=study_year,
                defaults=dict(
                    student_name=(f"{user.first_name} {user.last_name}".strip() or user.username),
                    grade=grade, group_name=group_name, student_type=student_type,
                    exam_average=(exam_avg.average if exam_avg else 0),
                    exam_final_average=(exam_avg.final_average if exam_avg else 0),
                    exam_count=(exam_avg.exam_count if exam_avg else 0),
                    exam_absent_count=(exam_avg.exam_abscent_count if exam_avg else 0),
                    assignment_average=(assign_avg.average if assign_avg else 0),
                    assignment_count=(assign_avg.assignment_count if assign_avg else 0),
                    assignment_absent_count=(assign_avg.assignment_abscent_count if assign_avg else 0),
                    classroom_absence_count=(class_avg.absence_count if class_avg else 0),
                    status=year_status,
                )
            )

            # جزئیات (idempotent: اجرای مجدد همان سال بازنویسی می‌کند)
            rec.exam_records.all().delete()
            rec.assignment_records.all().delete()

            exam_rows = []
            if exam_avg:
                for es in exam_avg.examscore_set.select_related('exam').all():
                    exam_rows.append(YearExamRecord(
                        year_record=rec, title=es.exam.ExamName, headline=es.exam.exam_headline,
                        date=es.exam.exam_available_time_end, score=es.score,
                        present=es.exam_peresence, is_offline=False))
                for eso in exam_avg.examscoreoffline_set.select_related('exam').all():
                    exam_rows.append(YearExamRecord(
                        year_record=rec, title=eso.exam.ExamName, headline=eso.exam.exam_headline,
                        date=eso.exam.exam_available_time_end, score=eso.score,
                        present=eso.exam_peresence, is_offline=True))
            YearExamRecord.objects.bulk_create(exam_rows)

            assign_rows = []
            if assign_avg:
                for a in assign_avg.assignmentscore_set.select_related('assignment').all():
                    assign_rows.append(YearAssignmentRecord(
                        year_record=rec, title=a.assignment.AssignmentName, headline=a.assignment.assignment_headline,
                        date=a.assignment.assignment_available_time_end, score=a.score,
                        present=a.assignment_presence))
            YearAssignmentRecord.objects.bulk_create(assign_rows)

            if su:
                su.student_status = year_status
                su.save(update_fields=['student_status'])
            archived += 1

        # غیرفعال‌سازی همه‌ی دانش‌آموزها؛ اکسل سال جدید برگشتی‌ها را فعال می‌کند
        students.update(is_active=False)

        # پاک‌سازی داده‌ی تحصیلی سال (CASCADE: ExamScore/AssignmentScore/ClassroomPresence)
        Exam.objects.all().delete()
        Assignment.objects.all().delete()
        Classroom.objects.all().delete()
        # سه مدل Average با اولین اکسل سال جدید دوباره ساخته می‌شوند
        ExamAverage.objects.all().delete()
        AssignmentAverage.objects.all().delete()
        ClassroomAverage.objects.all().delete()
        Group.objects.all().delete()

    logger.info(f"{actor} archived study_year={study_year}: {archived} students")
    return {"study_year": study_year, "students_archived": archived}
