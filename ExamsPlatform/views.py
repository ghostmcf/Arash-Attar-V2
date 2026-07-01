
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from random import shuffle
from uuid import UUID
from rest_framework.decorators import api_view,permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from . import models ,serializers
from rest_framework import status
from django.utils.timezone import localtime
from drf_spectacular.utils import extend_schema, inline_serializer
from drf_spectacular.types import OpenApiTypes
from rest_framework import serializers as rfs
 
#  aqn : Active question number
##################OPTIMIZE
@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def index(request):
    try:
        # select_related('exam') جلوی N+1 روی i.exam را می‌گیرد
        exam_list = request.user.examaverage.examscore_set.select_related('exam').order_by('-exam_finished', '-exam__exam_available_time_end')
    except:
        return Response({"message": "No data"}, status=status.HTTP_404_NOT_FOUND)
    else:
        exam_dict = []
        for i in exam_list:
            # امتحان‌های قبلاً تمام‌شده دوباره finish نمی‌شوند (حذف کوئری/سیو اضافی)
            if not i.exam.exam_finished:
                i.exam.finish_exam()
            temp_dict = {
                "score": serializers.ExamScoreSerializer(i).data,
                "exam_name": i.exam.ExamName,
                "exam_headline": i.exam.exam_headline,
                "ExamFinished": i.exam.exam_finished,
                "exam_permission": i.exam.exam_permission,
                "exam_available_time_end": localtime(i.exam.exam_available_time_end),
            }
            if i.exam.exam_finished:
                temp_dict.update({
                    "exam_answer_file": i.exam.exam_answer_file.url,
                    "user_score": i.score,
                })
            else:
                temp_dict.update({
                    "exam_duration": i.exam.exam_duration,
                    "exam_available_time_start": localtime(i.exam.exam_available_time_start),
                    "exam_maxenterance_time": localtime(i.exam.exam_maxenterance_time),
                })
            exam_dict.append(temp_dict)
        return Response(exam_dict, status=status.HTTP_200_OK)     
        
        
        
@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ExamView(request, examnum):
    selected_exam = get_object_or_404(models.Exam.objects.select_related('exam_group').prefetch_related('questions'), pk=examnum)
    student_in_exam = selected_exam.exam_group.user_set.filter(id=request.user.id).exists()
    # اگر کاربر examaverage یا ExamScore برای این آزمون نداشته باشد → ۴۰۳ تمیز (نه ۵۰۰)
    try:
        student_score = selected_exam.examscore_set.get(exam_average_reffer=request.user.examaverage.id)
    except ObjectDoesNotExist:
        return Response({"message": "You are not allowed"}, status=status.HTTP_403_FORBIDDEN)
    # print(selected_exam.exam_permission+student_in_exam+student_score.exam_finished+request.user.is_staff+request.user.is_superuser+student_score.exam_permission+selected_exam.is_running())
    if (selected_exam.exam_permission and student_in_exam and not student_score.exam_finished) and ((request.user.is_staff or request.user.is_superuser or student_score.exam_permission) or (selected_exam.is_running())):
        if not student_score.exam_peresence:
            max_enter = selected_exam.exam_maxenterance_time
            # None یعنی محدودیتِ زمان ورود تعریف نشده → ورود مجاز (زمان کلی آزمون در بیرون چک شده)
            if (max_enter is None or timezone.now() <= max_enter) or student_score.exam_permission:
                temp_list = []
                temp_user_c = []
                q_bank = selected_exam.questions.all()
                for questions in q_bank:
                    temp_list.append(str(questions.question_id))
                    temp_user_c.append(0)
                shuffle(temp_list)
                student_score.user_choice = temp_user_c
                student_score.questions_list = temp_list
                student_score.active_question_number = 1
                student_score.exam_peresence = True
            else:
                student_score.exam_peresence = False
        student_score.connect_times += 1
        student_score.save()

        if student_score.exam_peresence:
            exam_calculated_time=selected_exam.exam_available_time_end
            if student_score.student_available_extra_time_end:
                exam_calculated_time    =    student_score.student_available_extra_time_end
            return Response({"Exam": serializers.ExamSerializer(selected_exam).data, 'exam_time': exam_calculated_time, 'user_score': serializers.ExamScoreSerializer(student_score).data}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "You are not allowed"}, status=status.HTTP_403_FORBIDDEN)
    elif not student_in_exam:
        return Response({"message": "You are not allowed"}, status=status.HTTP_403_FORBIDDEN)
    else:
        return Response({"Exam": serializers.ExamSerializer(selected_exam).data, 'exam_time': selected_exam.exam_available_time_end, 'user_score': serializers.ExamScoreSerializer(student_score).data}, status=status.HTTP_208_ALREADY_REPORTED)





# ═══════════════════════════════════════════════════════════════════════════
#  جریان امتحان (exam_flow / exam_choice)
#  مدل state: active_question_number (سوال جاری) | max_question_number (پیشروترین)
#             active_deadline (مهلت مطلق سوال جاری) | frontier_remaining (زمان منجمد فرانت)
# ═══════════════════════════════════════════════════════════════════════════
def _exam_qmap(qlist):
    return {str(q.pk): q for q in models.Question.objects.filter(pk__in=[UUID(x) for x in qlist])}


def _exam_state_response(score, qlist, qmap, exam_deadline):
    cur = score.active_question_number
    q = qmap.get(qlist[cur - 1])
    q_deadline = min(score.active_deadline, exam_deadline) if score.active_deadline else exam_deadline
    return JsonResponse({
        "success": True,
        "active_question_number": cur,
        "max_question_number": score.max_question_number,
        "q_id": qlist[cur - 1],
        "q_img": q.question_img if q else None,   # CharField است؛ مستقیم رشته‌ی URL
        "q_time": q_deadline,                      # مهلت مطلق (aware) برای شمارش معکوس فرانت
        "u_choice": score.user_choice[cur - 1],
        "u_choices_list": score.user_choice,
        "u_q_list": qlist,
        "returns": score.returns_count,
        "e_time": exam_deadline,
    }, status=200)


@extend_schema(
    request=inline_serializer(name='ExamFlowRequest', fields={
        'aqn': rfs.IntegerField(required=False, help_text="فقط برای req_type=return: شماره‌ی سوالِ مقصدِ بازگشت"),
    }),
    responses=OpenApiTypes.OBJECT)
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def exam_flow(request, examnum, req_type):
    """جریان امتحان (نسخه‌ی اصلاح‌شده). req_type: conf | next | return | finish"""
    try:
        exam_avg_id = request.user.examaverage.id
    except Exception:
        return Response({"message": "You are not allowed"}, status=status.HTTP_403_FORBIDDEN)

    with transaction.atomic():
        selected_exam = get_object_or_404(models.Exam, pk=examnum)
        try:
            score = (models.ExamScore.objects.select_for_update()
                     .get(exam=selected_exam, exam_average_reffer=exam_avg_id))
        except models.ExamScore.DoesNotExist:
            return Response({"message": "You are not allowed"}, status=status.HTTP_403_FORBIDDEN)

        if score.exam_finished or not score.exam_peresence:
            return Response({"message": "Exam Finished"}, status=status.HTTP_423_LOCKED)

        qlist = score.questions_list
        total = len(qlist)
        if total == 0:
            return Response({"message": "No questions"}, status=status.HTTP_400_BAD_REQUEST)

        now = timezone.now()
        exam_deadline = score.student_available_extra_time_end or selected_exam.exam_available_time_end

        # اتمام آزمون: همیشه مجاز
        if req_type == "finish":
            score.exam_finished = True
            score.save(update_fields=['exam_finished'])
            selected_exam.finish_exam()
            if selected_exam.exam_finished:
                score.get_score()
            return JsonResponse({"success": True}, status=200)

        if now >= exam_deadline:
            return Response({"message": "Exam time over"}, status=status.HTTP_423_LOCKED)

        qmap = _exam_qmap(qlist)

        def qtime(idx):
            q = qmap.get(qlist[idx - 1])
            return q.question_time if q else 0

        def set_fresh_deadline(idx):
            # شروع تازه‌ی یک سوال (سوال آخر محدود به تایم امتحان است)
            score.active_deadline = exam_deadline if idx >= total else now + timedelta(seconds=qtime(idx))

        # ── lazy init ──
        if score.active_deadline is None:
            score.active_question_number = 1
            score.max_question_number = max(score.max_question_number, 1)
            set_fresh_deadline(1)
            score.frontier_remaining = None

        # ── همگام‌سازی با زمانِ سپری‌شده (re-entry/غیبت) ──
        if score.active_question_number >= score.max_question_number:
            # روی فرانت: تا جایی که زمان سوال‌ها گذشته پیش برو
            while score.active_deadline <= now and score.max_question_number < total:
                score.max_question_number += 1
                score.active_question_number = score.max_question_number
                if score.max_question_number >= total:
                    score.active_deadline = exam_deadline
                else:
                    score.active_deadline = score.active_deadline + timedelta(seconds=qtime(score.max_question_number))
            score.frontier_remaining = None
        else:
            # روی سوال بازگشتی: اگر زمانش تمام شده، برگرد به فرانت با زمان باقی‌مانده
            if score.active_deadline <= now:
                score.active_question_number = score.max_question_number
                score.active_deadline = (exam_deadline if score.max_question_number >= total
                                         else now + timedelta(seconds=(score.frontier_remaining or 0)))
                score.frontier_remaining = None

        if req_type == "conf":
            pass
        elif req_type == "next":
            if score.active_question_number < score.max_question_number:
                # از حالت بازگشت → پرش مستقیم به پیشروترین سوال با زمان باقی‌مانده (req 8)
                score.active_question_number = score.max_question_number
                score.active_deadline = (exam_deadline if score.max_question_number >= total
                                         else now + timedelta(seconds=(score.frontier_remaining or 0)))
                score.frontier_remaining = None
            elif score.max_question_number < total:
                # روی فرانت → یک سوال جلو
                score.max_question_number += 1
                score.active_question_number = score.max_question_number
                set_fresh_deadline(score.max_question_number)
            # اگر روی سوال آخر باشد، کاری نمی‌کند (محدود به تایم امتحان)
        elif req_type == "return":
            if score.returns_count <= 0:
                return Response({"message": "No returns left"}, status=status.HTTP_403_FORBIDDEN)
            try:
                aqn = int(request.data.get("aqn"))
            except (TypeError, ValueError):
                return Response({"message": "Invalid question number"}, status=status.HTTP_400_BAD_REQUEST)
            # فقط بازگشت به سوالِ قبلی (نه جلو، نه ندیده) — req 6
            if not (1 <= aqn < score.active_question_number):
                return Response({"message": "Can only return to an earlier question"}, status=status.HTTP_400_BAD_REQUEST)
            # اگر روی فرانت بودیم، زمان باقی‌مانده‌اش را منجمد کن
            if score.active_question_number == score.max_question_number:
                score.frontier_remaining = max(0.0, (min(score.active_deadline, exam_deadline) - now).total_seconds())
            score.active_question_number = aqn
            set_fresh_deadline(aqn)
            score.returns_count -= 1
        else:
            return Response({"message": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)

        score.save(update_fields=['active_question_number', 'max_question_number',
                                  'active_deadline', 'frontier_remaining', 'returns_count'])
        return _exam_state_response(score, qlist, qmap, exam_deadline)


@extend_schema(
    request=inline_serializer(name='ExamChoiceRequest', fields={
        'aqn': rfs.IntegerField(help_text="شماره‌ی سوال"),
        'answer_number': rfs.IntegerField(required=False, help_text="گزینه‌ی انتخابی (برای command=set)"),
    }),
    responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def exam_choice(request, examnum, command):
    """ثبت/حذف گزینه (نسخه‌ی جدید با قفل ردیف برای جلوگیری از lost-update). command: set | rem"""
    try:
        exam_avg_id = request.user.examaverage.id
    except Exception:
        return Response({"message": "You are not allowed"}, status=status.HTTP_403_FORBIDDEN)

    with transaction.atomic():
        selected_exam = get_object_or_404(models.Exam, pk=examnum)
        try:
            score = (models.ExamScore.objects.select_for_update()
                     .get(exam=selected_exam, exam_average_reffer=exam_avg_id))
        except models.ExamScore.DoesNotExist:
            return Response({"message": "You are not allowed"}, status=status.HTTP_403_FORBIDDEN)

        if score.exam_finished or not score.exam_peresence:
            return Response({"message": "Exam Finished"}, status=status.HTTP_423_LOCKED)
        now = timezone.now()
        exam_deadline = score.student_available_extra_time_end or selected_exam.exam_available_time_end
        if now >= exam_deadline:
            return Response({"message": "Exam time over"}, status=status.HTTP_423_LOCKED)

        try:
            aqn = int(request.data.get("aqn"))
        except (TypeError, ValueError):
            return Response({"message": "Invalid parameters"}, status=status.HTTP_400_BAD_REQUEST)
        if not (1 <= aqn <= len(score.user_choice)):
            return Response({"message": "Invalid question number"}, status=status.HTTP_400_BAD_REQUEST)
        # ضدِ تقلب: فقط گزینه‌ی «سوال جاری» قابل ثبت است (نه ثبت دسته‌جمعی/سوال‌های دیگر)
        if aqn != score.active_question_number:
            return Response({"message": "Can only answer the active question"}, status=status.HTTP_403_FORBIDDEN)

        if command == "set":
            try:
                answer_number = int(request.data.get("answer_number"))
            except (TypeError, ValueError):
                return Response({"message": "Invalid parameters"}, status=status.HTTP_400_BAD_REQUEST)
            score.user_choice[aqn - 1] = answer_number
        elif command == "rem":
            score.user_choice[aqn - 1] = 0
        else:
            return Response({"message": "Invalid command"}, status=status.HTTP_400_BAD_REQUEST)

        score.save(update_fields=['user_choice'])
        return Response(status=status.HTTP_200_OK)

        