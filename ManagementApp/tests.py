"""
تست‌های رگرسیون کنترل دسترسی پنل مدیریت.

اجرا روی سرور/CI:
    python manage.py test ManagementApp

هدف: اطمینان از اینکه اندپوینت‌هایی که قبلاً AllowAny بودند یا permission نداشتند،
دیگر برای کاربر ناشناس/دانش‌آموز باز نیستند و فقط ادمین دسترسی دارد.
"""
import io

import openpyxl
from django.contrib.auth.models import Group, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from ExamsPlatform.models import Exam, ExamAverage, ExamScore, ExamScoreOffline
from AssignmentPlatform.models import Assignment, AssignmentAverage, AssignmentScore
from ClassroomsPlatform.models import ClassroomAverage
from StudentsInfo.models import StudentUser, StudentYearRecord, AttendanceRecord


def _make_xlsx(headers, rows):
    """یک فایل xlsx درون‌حافظه‌ای برای تست آپلود می‌سازد."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(headers)
    for r in rows:
        ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return SimpleUploadedFile(
        "f.xlsx", buf.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


class AccessControlTests(TestCase):
    def setUp(self):
        self.group = Group.objects.create(name="گروه تست")
        self.student = User.objects.create_user(username="student", password="pw")
        self.student.groups.add(self.group)
        self.admin = User.objects.create_user(
            username="admin", password="pw", is_staff=True, is_superuser=True
        )

    # ---- export_exam_scores (قبلاً AllowAny) ----
    def test_export_exam_scores_blocks_anonymous(self):
        resp = self.client.get(f"/management/groups/{self.group.id}/export_exam_scores/")
        self.assertIn(resp.status_code, (401, 403))

    def test_export_exam_scores_blocks_student(self):
        self.client.force_login(self.student)
        resp = self.client.get(f"/management/groups/{self.group.id}/export_exam_scores/")
        self.assertEqual(resp.status_code, 403)

    def test_export_exam_scores_allows_admin(self):
        self.client.force_login(self.admin)
        resp = self.client.get(f"/management/groups/{self.group.id}/export_exam_scores/")
        self.assertEqual(resp.status_code, 200)

    # ---- export_assignment_scores (قبلاً AllowAny) ----
    def test_export_assignment_scores_blocks_student(self):
        self.client.force_login(self.student)
        resp = self.client.get(
            f"/management/groups/{self.group.id}/export_assignment_scores/"
        )
        self.assertEqual(resp.status_code, 403)

    # ---- classroom_presence_summary (قبلاً AllowAny) ----
    def test_classroom_summary_blocks_student(self):
        self.client.force_login(self.student)
        resp = self.client.get(
            f"/management/users/{self.student.id}/classroom_presence_summary/"
        )
        self.assertEqual(resp.status_code, 403)

    # ---- NotificationViewSet (قبلاً بدون permission) ----
    def test_notifications_list_blocks_student(self):
        self.client.force_login(self.student)
        resp = self.client.get("/management/notifications/")
        self.assertEqual(resp.status_code, 403)

    def test_notifications_list_allows_admin(self):
        self.client.force_login(self.admin)
        resp = self.client.get("/management/notifications/")
        self.assertEqual(resp.status_code, 200)

    # ---- IDOR: کاربر نباید نوتیف کاربر دیگری را ببیند ----
    def test_user_notifications_blocks_cross_user(self):
        other = User.objects.create_user(username="other", password="pw")
        self.client.force_login(self.student)
        resp = self.client.get(f"/management/notifications/{other.username}/user/")
        self.assertEqual(resp.status_code, 403)

    def test_user_notifications_allows_self(self):
        self.client.force_login(self.student)
        resp = self.client.get(
            f"/management/notifications/{self.student.username}/user/"
        )
        self.assertEqual(resp.status_code, 200)


class ArchiveYearTests(TestCase):
    """تست بایگانی پایان سال: ساخت رکورد سال + جزئیات، حذف داده‌ی تحصیلی، غیرفعال‌سازی."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin", password="pw", is_staff=True, is_superuser=True
        )
        self.group = Group.objects.create(name="گروه دوازدهم")
        self.group.group_grade = "دوازدهم"
        self.group.save()

        self.student = User.objects.create_user(
            username="0012345678", password="pw", first_name="علی", last_name="رضایی"
        )
        self.student.groups.add(self.group)
        StudentUser.objects.create(student_user=self.student, student_grade="دوازدهم", student_type="ریاضی")

        # میانگین‌ها + نمرات
        self.exam_avg = ExamAverage.objects.create(user=self.student)
        self.assign_avg = AssignmentAverage.objects.create(user=self.student)
        ClassroomAverage.objects.create(user=self.student)

        exam = Exam.objects.create(exam_group=self.group, ExamName="آزمون ۱", exam_headline="فصل ۱")
        ExamScore.objects.create(
            exam=exam, exam_average_reffer=self.exam_avg,
            score=80, exam_peresence=True, exam_finished=True,
        )
        assignment = Assignment.objects.create(
            assignment_group=self.group, AssignmentName="تکلیف ۱", assignment_headline="سری ۱",
        )
        AssignmentScore.objects.create(
            assignment=assignment, assignment_average_reffer=self.assign_avg,
            score=70, assignment_presence=True, assignment_finished=True,
        )

    def test_archive_creates_records_and_wipes_data(self):
        self.client.force_login(self.admin)
        resp = self.client.post(
            "/management/archive-year/", {"study_year": "1403-1404", "confirm": "true"},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)

        # رکورد سال ساخته شد با مقادیر درست
        rec = StudentYearRecord.objects.get(student=self.student, study_year="1403-1404")
        self.assertEqual(rec.grade, "دوازدهم")
        self.assertEqual(rec.group_name, "گروه دوازدهم")
        self.assertEqual(rec.status, "فارغ التحصیل")          # دوازدهمی → فارغ‌التحصیل خودکار
        self.assertEqual(int(rec.exam_average), 80)
        self.assertEqual(int(rec.assignment_average), 70)
        self.assertEqual(rec.exam_records.count(), 1)
        self.assertEqual(rec.assignment_records.count(), 1)

        # داده‌ی تحصیلی سال پاک شد
        self.assertEqual(Exam.objects.count(), 0)
        self.assertEqual(Assignment.objects.count(), 0)
        self.assertEqual(Group.objects.count(), 0)
        self.assertEqual(ExamAverage.objects.count(), 0)

        # دانش‌آموز غیرفعال شد
        self.student.refresh_from_db()
        self.assertFalse(self.student.is_active)

    def test_archive_requires_admin(self):
        student = User.objects.create_user(username="s2", password="pw")
        self.client.force_login(student)
        resp = self.client.post("/management/archive-year/", {}, content_type="application/json")
        self.assertEqual(resp.status_code, 403)


class OfflineExamUploadTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin", password="pw", is_staff=True, is_superuser=True
        )
        self.group = Group.objects.create(name="G")
        self.student = User.objects.create_user(username="0011", password="pw")
        self.student.groups.add(self.group)
        ExamAverage.objects.create(user=self.student)

    def test_offline_exam_updates_average(self):
        self.client.force_login(self.admin)
        f = _make_xlsx(["کد ملی", "درصد"], [["0011", 90]])
        resp = self.client.post("/management/upload-offline-exam/", {
            "file": f, "exam_name": "آزمون حضوری", "group": "G", "date": "1403/07/15",
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            ExamScoreOffline.objects.filter(exam_average_reffer__user=self.student).count(), 1
        )
        avg = ExamAverage.objects.get(user=self.student)
        self.assertEqual(int(avg.average), 90)

    def test_offline_exam_requires_admin(self):
        self.client.force_login(self.student)
        f = _make_xlsx(["کد ملی", "درصد"], [["0011", 90]])
        resp = self.client.post("/management/upload-offline-exam/", {
            "file": f, "exam_name": "x", "group": "G", "date": "1403/07/15",
        })
        self.assertEqual(resp.status_code, 403)


class AttendanceUploadTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin", password="pw", is_staff=True, is_superuser=True
        )
        self.group = Group.objects.create(name="G")
        self.student = User.objects.create_user(username="0011", password="pw")
        self.student.groups.add(self.group)

    def test_attendance_counts_absence(self):
        self.client.force_login(self.admin)
        f = _make_xlsx(["کد ملی", "وضعیت"], [["0011", "غایب"]])
        resp = self.client.post("/management/upload-attendance/", {
            "file": f, "group": "G", "session_title": "جلسه ۱", "date": "1403/07/15",
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            AttendanceRecord.objects.filter(student=self.student, present=False).count(), 1
        )
        self.assertEqual(ClassroomAverage.objects.get(user=self.student).absence_count, 1)

    def test_attendance_idempotent_reupload(self):
        # آپلود مجدد همان جلسه نباید غیبت را دوبرابر کند
        self.client.force_login(self.admin)
        for _ in range(2):
            f = _make_xlsx(["کد ملی", "وضعیت"], [["0011", "غایب"]])
            self.client.post("/management/upload-attendance/", {
                "file": f, "group": "G", "session_title": "جلسه ۱", "date": "1403/07/15",
            })
        self.assertEqual(AttendanceRecord.objects.filter(student=self.student).count(), 1)
        self.assertEqual(ClassroomAverage.objects.get(user=self.student).absence_count, 1)


class SmsPanelTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin", password="pw", is_staff=True, is_superuser=True
        )
        self.group = Group.objects.create(name="G")

    def _student(self, username, mother=None, father=None):
        u = User.objects.create_user(username=username, password="pw")
        u.groups.add(self.group)
        StudentUser.objects.create(student_user=u, mother_number=mother, father_number=father)
        return u

    def test_resolve_numbers_default_and_both(self):
        from Frontend.sms_manager import resolve_numbers
        su = self._student("s1", mother="09120000000", father="09130000000").studentuser
        nums, used = resolve_numbers(su, "mother")
        self.assertEqual((nums, used), (["09120000000"], "mother"))
        nums, used = resolve_numbers(su, "both")
        self.assertEqual(set(nums), {"09120000000", "09130000000"})
        self.assertEqual(used, "both")

    def test_resolve_numbers_fallback_to_existing(self):
        from Frontend.sms_manager import resolve_numbers
        su = self._student("s2", mother=None, father="09130000000").studentuser
        # مادر نیست → fallback به پدر
        nums, used = resolve_numbers(su, "mother")
        self.assertEqual((nums, used), (["09130000000"], "father"))

    def test_exam_send_requires_permission(self):
        exam = Exam.objects.create(exam_group=self.group, ExamName="آزمون")
        self.assertFalse(exam.sms_permission)
        self.client.force_login(self.admin)
        resp = self.client.post(
            f"/management/exams/{exam.exam_id}/send-sms/",
            {"target": "mother", "user_ids": "all"}, content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)   # مجوز صادر نشده → بدون ارسال

    def test_assignment_permission_when_all_marked(self):
        from AssignmentPlatform.models import Assignment, AssignmentAverage, AssignmentScore
        u = self._student("s3")
        avg = AssignmentAverage.objects.create(user=u)
        a = Assignment.objects.create(assignment_group=self.group, AssignmentName="ت۱")
        AssignmentScore.objects.create(assignment=a, assignment_average_reffer=avg, assignment_marked=True)
        a.update_sms_permission()
        a.refresh_from_db()
        self.assertTrue(a.sms_permission)
