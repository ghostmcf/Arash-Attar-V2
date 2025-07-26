
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from random import shuffle
from uuid import UUID
from rest_framework.decorators import api_view,permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from . import models ,serializers
from rest_framework import status
from django.utils.timezone import localtime
 
 
##################OPTIMIZE
@api_view(['GET'])
@permission_classes([IsAuthenticated])        
def index(request):
    try:
        exam_list = request.user.examaverage.examscore_set.order_by('-exam_finished', '-exam__exam_available_time_end')
    except:
        return Response({"message": "No data"}, status=status.HTTP_404_NOT_FOUND)
    else:
        exam_dict = []
        for i in exam_list:
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
        
        
        
@permission_classes([IsAuthenticated])
@api_view(['GET'])
def ExamView(request, examnum):
    selected_exam = get_object_or_404(models.Exam.objects.select_related('exam_group').prefetch_related('questions'), pk=examnum)
    student_in_exam = selected_exam.exam_group.user_set.filter(id=request.user.id).exists()
    student_score = selected_exam.examscore_set.get(exam_average_reffer=request.user.examaverage.id)
    # print(selected_exam.exam_permission+student_in_exam+student_score.exam_finished+request.user.is_staff+request.user.is_superuser+student_score.exam_permission+selected_exam.is_running())
    if (selected_exam.exam_permission and student_in_exam and not student_score.exam_finished) and ((request.user.is_staff or request.user.is_superuser or student_score.exam_permission) or (selected_exam.is_running())):
        if not student_score.exam_peresence:
            if timezone.now() <= selected_exam.exam_maxenterance_time or student_score.exam_permission:
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
                student_score.last_question_time = None
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



@permission_classes([IsAuthenticated])
@api_view(['GET','POST'])
def InExamChangeView(request,examnum,req_type): 
    # req_type : 1 for conf , 2 for change
    # student_qs_list=list(student_score.questions_list.keys())
    selected_exam       = get_object_or_404(models.Exam,pk=examnum)
    student_score=selected_exam.examscore_set.get(exam_average_reffer = request.user.examaverage.id)
    student_qs_list=student_score.questions_list
    if not selected_exam.is_running() or student_score.exam_finished or not student_score.exam_peresence :
        return Response({"message":"Exam Finished"}, status=status.HTTP_423_LOCKED)
    elif req_type == "conf" and (selected_exam.is_running() or student_score.exam_permission) :           
        student_qs=student_qs_list[student_score.active_question_number-1]
        selected_question=get_object_or_404(models.Question,pk=UUID(student_qs))
        # qt=selected_question.question_time
        qt=datetime. now() + timedelta(seconds=selected_question.question_time)    
        stu_choice=student_score.user_choice[student_score.active_question_number-1]        
        if student_score.last_question_time is None:        
            student_score.last_question_time=timezone.now()
            # if student_score.choices_list[student_score.active_question_number-1] == 0 :
            #     student_score.choices_list[student_score.active_question_number-1] = "1"
            student_score.save()
        else:
            a=timezone.now() - student_score.last_question_time
            a=round(a.total_seconds())
            if (selected_question.question_time-a)<=0 :
                if student_score.active_question_number <10:
                    student_score.active_question_number +=1
                student_score.last_question_time=timezone.now()
                student_score.save()
                student_qs=student_qs_list[student_score.active_question_number-1]
                selected_question=get_object_or_404(models.Question,pk=UUID(student_qs))                    
                # qt=selected_question.question_time
                qt=datetime. now() + timedelta(seconds=selected_question.question_time)
            else:
                # qt=qt-a
                qt=datetime. now() + timedelta(seconds=(selected_question.question_time-a))
        # choices=selected_question.choice_set.all()
        # print(selected_question.question_headline)
        # print(selected_question.question_time)
        return JsonResponse({
            "success":True,
            "active_question_number":student_score.active_question_number,
            "u_choice":student_score.user_choice[student_score.active_question_number-1],
            "q_time":qt,
            "q_id":student_qs,
            "q_img":selected_question.question_img.url,
            "returns":student_score.returns_count,                
            "u_choices_list":student_score.user_choice,
            "u_q_list":student_qs_list,
            "e_time":selected_exam.exam_available_time_end,
            }, status=200)
    elif req_type == "next" and (selected_exam.is_running() or student_score.exam_permission) and 0< student_score.active_question_number <11:
        student_score.last_question_time=timezone.now()           
        if student_score.active_question_number < 10:
            student_score.active_question_number +=1    
        # if student_score.choices_list[student_score.active_question_number-1] == 0 :
        #     student_score.choices_list[student_score.active_question_number-1] = "1"
        student_score.save()
        student_qs=student_qs_list[student_score.active_question_number-1]
        selected_question=get_object_or_404(models.Question,pk=UUID(student_qs))
        # print(selected_question.question_headline)
        # print(selected_question.question_time)
        # choices=selected_question.choice_set.all()                  
        return JsonResponse({
            "success":True,
            "active_question_number":student_score.active_question_number,
            "q_time":datetime. now() + timedelta(seconds=selected_question.question_time),
            "q_id":student_qs,
            "q_img":selected_question.question_img.url,
            # "q_text":selected_question.question_text,
            

            "returns":student_score.returns_count,
            "u_choice":student_score.user_choice[student_score.active_question_number-1],
            "u_choices_list":student_score.user_choice,   
            "u_q_list":student_qs_list,
            }, status=200)
    elif req_type == "finish" and (selected_exam.is_running() or student_score.exam_permission):
        student_score.exam_finished=True
        if student_score.exam_permission and selected_exam.exam_finished:
            student_score.get_score()
        else:    
            student_score.save()
            selected_exam.finish_exam()
        return JsonResponse({
            "success":True,                            
            }, status=200)
    elif req_type == "return" and (selected_exam.is_running() or student_score.exam_permission) and 0< int(request.POST.get("aqn")) <11 and student_score.returns_count>0:
        student_score.last_question_time=timezone.now()  
        student_qs=student_qs_list[int(request.POST.get("aqn"))-1]
        student_score.returns_count -=1
        student_score.save()
        selected_question=get_object_or_404(models.Question,pk=UUID(student_qs))
        
        # print(selected_question.question_headline)
        # print(selected_question.question_time)
        # choices=selected_question.choice_set.all()                  
        return JsonResponse({
            "success":True,
            "active_question_number":int(request.POST.get("aqn")),
            "q_time":datetime. now() + timedelta(seconds=selected_question.question_time),
            "q_id":student_qs,
            "q_img":selected_question.question_img.url,
            # "q_text":selected_question.question_text,
            

            "returns":student_score.returns_count,
            "u_choice":student_score.user_choice[int(request.POST.get("aqn"))-1],
            "u_q_list":student_qs_list,
            }, status=200)
    else:
        return Response({"message":"You are not allowed kooni"}, status=status.HTTP_403_FORBIDDEN)
    pass



@permission_classes([IsAuthenticated])
@api_view(['POST'])
def question_cal(request,examnum,command ):
    selected_exam       = get_object_or_404(models.Exam,pk=examnum)
    student_score=selected_exam.examscore_set.get(exam_average_reffer = request.user.examaverage.id)
    # selected_choice=student_score.choices_list[student_score.active_question_number-1]
    if not selected_exam.is_running() or student_score.exam_finished or not student_score.exam_peresence:
        return Response({"message":"Exam Finished"}, status=status.HTTP_423_LOCKED)
    elif command == "set" :            
        student_score.user_choice[int(request.POST.get("aqn"))-1]=int(request.POST.get("answer_number"))
        # student_score.user_choice[int(student_score.active_question_number)-1]=int(request.POST.get("answer_number"))
        # print(student_score.choices_list)p
        student_score.save()
        # return JsonResponse({"success":True}, status=200)
        return Response(status=status.HTTP_200_OK)
    elif command == "rem" :
        student_score.user_choice[int(request.POST.get("aqn"))-1]=0
        # student_score.user_choice[int(student_score.active_question_number)-1]=0
        student_score.save()
        # return JsonResponse({"success":True}, status=200)
        return Response(status=status.HTTP_200_OK)
    # elif not selected_exam.is_running():
    #     selected_choice=00
    #     return JsonResponse({
    #         "success":False,
    #         "unauthorized":1,
    #         }, status=400)        
    return Response({"message":"You are not allowed"}, status=status.HTTP_400_BAD_REQUEST)

        