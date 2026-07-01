"""
تست‌های منطق نمره‌دهی آزمون.

اجرا روی سرور/CI:
    python manage.py test ExamsPlatform

این تست‌ها به دیتابیس تست نیاز دارند (Django خودش یک DB موقت می‌سازد).
"""
from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.utils import timezone

from .models import Exam, ExamAverage, ExamScore, Question


class GetScoreTests(TestCase):
    """آزمون فرمول get_score در ExamScore."""

    def setUp(self):
        self.group = Group.objects.create(name="گروه تست")
        self.user = User.objects.create_user(username="0012345678", password="x")
        self.user.groups.add(self.group)
        self.exam_average = ExamAverage.objects.create(user=self.user)

        self.exam = Exam.objects.create(
            exam_group=self.group,
            ExamName="آزمون تست",
            exam_available_time_start=timezone.now(),
            exam_available_time_end=timezone.now(),
        )

        # سه سوال با پاسخ‌های مشخص: 1, 2, 3
        self.questions = []
        for idx, answer in enumerate((1, 2, 3), start=1):
            q = Question.objects.create(
                question_headline=f"q{idx}",
                question_category="cat",
                question_answer=answer,
                question_time=60,
            )
            self.exam.questions.add(q)
            self.questions.append(q)

    def _make_score(self, user_choice):
        qlist = [str(q.pk) for q in self.questions]
        return ExamScore.objects.create(
            exam=self.exam,
            exam_average_reffer=self.exam_average,
            exam_finished=True,
            exam_peresence=True,
            questions_list=qlist,
            user_choice=user_choice,
        )

    def test_two_correct_one_blank(self):
        # انتخاب کاربر: [درست، درست، بی‌پاسخ] => 2 درست، 0 غلط، 1 بی‌پاسخ
        score = self._make_score([1, 2, 0])
        score.get_score()
        # ((2*3 - 0) / (3*3)) * 100 = 66.67  (float برای سازگاری با SQLite/MySQL)
        self.assertAlmostEqual(float(score.score), 66.67, places=2)
        self.assertEqual(score.wrong_counts, 0)
        self.assertEqual(score.none_counts, 1)

    def test_two_correct_one_wrong(self):
        # [درست، غلط، درست] => 2 درست، 1 غلط
        score = self._make_score([1, 4, 3])
        score.get_score()
        # ((2*3 - 1) / 9) * 100 = 55.56  (float برای سازگاری با SQLite/MySQL)
        self.assertAlmostEqual(float(score.score), 55.56, places=2)
        self.assertEqual(score.wrong_counts, 1)
        self.assertEqual(score.none_counts, 0)

    def test_score_capped_at_100(self):
        # همه درست + نمره‌ی اضافه => نباید از 100 بیشتر شود
        self.exam.exam_extra_score = 50
        self.exam.save(update_fields=["exam_extra_score"])
        score = self._make_score([1, 2, 3])
        score.get_score()
        self.assertEqual(score.score, Decimal("100"))

    def test_absent_scores_zero(self):
        # غایب (peresence=False) => نمره صفر
        score = ExamScore.objects.create(
            exam=self.exam,
            exam_average_reffer=self.exam_average,
            exam_finished=True,
            exam_peresence=False,
            questions_list=[str(q.pk) for q in self.questions],
            user_choice=[0, 0, 0],
        )
        score.get_score()
        self.assertEqual(score.score, Decimal("0"))
