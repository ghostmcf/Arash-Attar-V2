
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from random import shuffle
from uuid import UUID
from rest_framework.decorators import api_view,permission_classes
from rest_framework.authentication import SessionAuthentication,TokenAuthentication
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from . import models ,serializers
from rest_framework import status
from django.utils.timezone import localtime
        
# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def index(request):
#     try:
#         exam_list  = request.user.examaverage.examscore_set.order_by('-exam_finished','-exam__exam_available_time_end',)
#         # exam_list     = request.user.groups.all()[0].exam_set.order_by('-exam_permission','-exam_available_time_end',)
#     except:
#         return Response({"message":"No data"},status=status.HTTP_404_NOT_FOUND)
#     else:
#         listed_exam = list(exam_list)
#         exam_dict = []
#         temp_dict ={}
#         for i in listed_exam:
#             if i.exam.exam_finished :
#                 temp_dict={
#                 "score":serializers.ExamScoreSerializer(i).data,
#                 "exam_name":i.exam.ExamName,
#                 "exam_answer_file":i.exam.exam_answer_file.url,
#                 # "exam_file":i.exam.exam_description.url,
#                 # "AssignmentName":i.exam.AssignmentName,
#                 "exam_headline":i.exam.exam_headline,
#                 "exam_available_time_end":i.exam.exam_available_time_end,
#                 "exam_finished":i.exam.exam_finished,
#                 "exam_permission":i.exam.exam_permission,
#                 }
#             else:
#                 temp_dict={
#                 "score":serializers.ExamScoreSerializer(i).data,
#                 "exam_name":i.exam.ExamName,
#                 # "exam_answer_file":i.exam.exam_answer_file.url,
#                 # "exam_file":i.exam.exam_description.url,
#                 # "AssignmentName":i.exam.AssignmentName,
#                 "exam_headline":i.exam.exam_headline,                
#                 "exam_duration":i.exam.exam_duration,
#                 "exam_available_time_start":i.exam.exam_available_time_start,
#                 "exam_available_time_end":i.exam.exam_available_time_end,
#                 "exam_maxenterance_time":i.exam.exam_maxenterance_time,
#                 "exam_finished":i.exam.exam_finished,
#                 "exam_permission":i.exam.exam_permission,
#                 }
#             exam_dict.append(temp_dict)
#         return Response(exam_dict,status=status.HTTP_200_OK)  
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
        
        
        
# @permission_classes([IsAuthenticated])
# @api_view(['GET'])
# def ExamView (request ,examnum):
#     selected_exam       = get_object_or_404(models.Exam,pk=examnum)
#     student_in_exam     = selected_exam.exam_group.user_set.filter(id = request.user.id).exists()
#     student_score       = selected_exam.examscore_set.get(exam_average_reffer = request.user.examaverage.id)  
#     if  ( selected_exam.exam_permission and student_in_exam and not student_score.exam_finished ) and ( (request.user.is_staff or request.user.is_superuser or student_score.exam_permission) or ( selected_exam.is_running() ) ):        
#         if student_score.exam_peresence :
#             pass
#         else:
#             if  timezone.now() <= selected_exam.exam_maxenterance_time or student_score.exam_permission :       
#                 temp_list = []   
#                 temp_user_c=[]
#                 # temp_dict=dict()
#                 q_bank = selected_exam.questions.all()
#                 for questions in q_bank :
#                     temp_list.append(str(questions.question_id))
#                     temp_user_c.append(0)
#                 shuffle(temp_list)
#                 # print(temp_list)
#                 student_score.user_choice=temp_user_c
#                 student_score.questions_list=temp_list
#                 student_score.active_question_number=1
#                 student_score.exam_peresence=True
#                 student_score.last_question_time=None
#             else:
#                 student_score.exam_peresence=False
#         student_score.connect_times +=1
#         student_score.save()                             
                
#         if student_score.exam_peresence :
#             # return Response({"Exam":serializers.ExamSerializer(selected_exam).data,'exam_time' : selected_exam.exam_available_time_end , 'user_score':serializers.ExamScoreSerializer(student_score).data ,'questions_dict':student_score.questions_list},status=status.HTTP_200_OK) 
#             return Response({"Exam":serializers.ExamSerializer(selected_exam).data,'exam_time' : selected_exam.exam_available_time_end , 'user_score':serializers.ExamScoreSerializer(student_score).data },status=status.HTTP_200_OK) 
#         else :
#             return Response({"message":"You are not allowed"}, status=status.HTTP_403_FORBIDDEN)
#     else:
#         # return Response({"Exam":serializers.ExamSerializer(selected_exam).data,'exam_time' : selected_exam.exam_available_time_end , 'user_score':serializers.ExamScoreSerializer(student_score).data ,'questions_dict':student_score.questions_list},status=status.HTTP_208_ALREADY_REPORTED) 
#         return Response({"Exam":serializers.ExamSerializer(selected_exam).data,'exam_time' : selected_exam.exam_available_time_end , 'user_score':serializers.ExamScoreSerializer(student_score).data },status=status.HTTP_208_ALREADY_REPORTED) 

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


# student_available_extra_time_end

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

        








# @api_view(['GET'])
# @login_required
# def handler404(request,exception):
#     response = render(request,'home/404.html',{})
#     return response

# def question_cal_ghadimi(request,examnum,qnum ):
#     # question = get_object_or_404(models.Question, pk=qnum)
#     # try:
#     #     selected_choice = question.choice_set.get(pk=request.POST['choice'])
#     # except (KeyError, models.Choice.DoesNotExist):
#     #     # Redisplay the question voting form.
#     #     return render(request, 'polls/detail.html', {
#     #         'question': question,
#     #         'error_message': "You didn't select a choice.",
#     #     })
#     # else:
#     #     selected_choice.votes += 1
#     #     selected_choice.save()
#     #     # Always return an HttpResponseRedirect after successfully dealing
#     #     # with POST data. This prevents data from being posted twice if a
#     #     # user hits the Back button.
#     #     return HttpResponseRedirect(reverse('polls:results', args=(question.id,)))
#     if request.method == "POST" and request.is_ajax():
        
#         return JsonResponse({"success":True}, status=200)
#     return JsonResponse({"success":False}, status=400)

 
     
     
####     OLD VIEWS    ########


# # Create your views here.
# @login_required
# def index (request ,):
    # tnow=timezone.now()
    # exams_list = request.user.groups.all()[0].exam_set.order_by('-exam_permission','-exam_available_time_end',)
    # if request.user.groups.all()[0].exam_set.filter(exam_permission=True,exam_finished=False,exam_running=False).exists():
    #     next_exam = request.user.groups.all()[0].exam_set.filter(exam_permission=True,exam_finished=False,exam_running=False).order_by('exam_available_time_start')[0]
    # else:
    #     next_exam=0
    # student_average=request.user.examaverage_set.all()[0]
    # if request.user.groups.all()[0].exam_set.filter(exam_permission=True,exam_finished=False,exam_running=True).exists():
    #     running_exam=request.user.groups.all()[0].exam_set.filter(exam_permission=True,exam_finished=False,exam_running=True)[0]
    # else:
    #     running_exam=0
    # context={'next_exam':next_exam,'student_average':student_average,'running_exam':running_exam,'exams_list':exams_list,'tnow':tnow}
    # return render(request,'ExamsPlatform/index.html',context)


# @login_required
# def ExamsListView (request ,):
#     tnow=timezone.now()
#     exams_list = request.user.groups.all()[0].exam_set.order_by('-exam_permission','-exam_available_time_end',)   
#     # exams_list = request.user.groups.all()[0].exam_set.filter(exam_permission=True,exam_running=False,)
#     context={'exams_list':exams_list,'tnow':tnow}
#     return render(request,'ExamsPlatform/AllExamsList.html',context)


# # @login_required
# # def ExamView (request ,examnum):  
#     selected_exam       = get_object_or_404(models.Exam,pk=examnum)
#     student_in_exam     = selected_exam.exam_group.user_set.filter(id = request.user.id).exists()
#     student_score       =selected_exam.examscore_set.get(exam_average_reffer = request.user.id)  
#     if  ( selected_exam.exam_permission and student_in_exam and not student_score.exam_finished ) and ( (request.user.is_staff or request.user.is_superuser or student_score.exam_permission) or ( selected_exam.is_running() ) ):        
#         if student_score.exam_peresence :
#             pass
#         else:
#             if  timezone.now() <= selected_exam.exam_maxenterance_time :       
#                 temp_list = []   
#                 temp_list_c=[]
#                 temp_user_c=[]
#                 # temp_dict=dict()
#                 for questions in selected_exam.question_set.all() :
#                     temp_list.append(str(questions.question_id))
#                     temp_list_c.append(0)
#                     temp_user_c.append(0)
#                 shuffle(temp_list)
#                 # print(temp_list)
#                 student_score.user_choice=temp_user_c
#                 student_score.questions_list=temp_list
#                 student_score.choices_list=temp_list_c
#                 student_score.active_question_number=1
#                 student_score.exam_peresence=True
#                 student_score.last_question_time=None
#             else:
#                 student_score.exam_peresence=False
#         student_score.connect_times +=1
#         student_score.save()                             
                
#         if student_score.exam_peresence :
#             context={'selected_exam':selected_exam , 'exam_time' : selected_exam.exam_available_time_end , 'user_score':student_score ,'questions_dict':student_score.questions_list}  
#             return render(request,'ExamsPlatform/Exam/Exam.html',context)
#         else :
#             context={'selected_exam':selected_exam , 'presence' : student_score.exam_peresence , 'user_score':student_score }
#             return render(request,'ExamsPlatform/Exam/failed.html',context)
#     else:
#         # return redirect('examresultpage')
#         return HttpResponseRedirect('/exam-platform/exam/'+str(selected_exam.exam_id)+'/result')


# @login_required
# def ExamResultView (request ,examnum):
#     selected_exam       = get_object_or_404(models.Exam,pk=examnum)
#     student_in_exam = selected_exam.exam_group.user_set.filter(id = request.user.id).exists()
#     student_score=selected_exam.examscore_set.get(exam_average_reffer = request.user.id) 
#     if ( student_in_exam and selected_exam.exam_available_time_end < timezone.now() ) or (request.user.is_staff or request.user.is_superuser) :        
#         if selected_exam.exam_finished==False:
#             selected_exam.finish_exam()
#         if student_score.exam_peresence:
#             context={'selected_exam':selected_exam ,'result_permission':1 , 'student_score':student_score }
#         else:
#             context={'selected_exam':selected_exam ,'result_permission':2 , 'student_score':student_score }  
#         student_score.get_score()
#         return render(request,'ExamsPlatform/Exam/result.html',context)
#     elif (student_in_exam and selected_exam.is_running() ) :#selected_exam.exam_available_time_end >= timezone.now()
#         if student_score.exam_finished:            
#             context={'selected_exam':selected_exam ,'result_permission':0 }
#             return render(request,'ExamsPlatform/Exam/result.html',context)        
#         elif not selected_exam.exam_finished:
#             return redirect(reverse('ExamsPlatform:exampage',kwargs = {'examnum': examnum }))        
#     else:
#         return HttpResponseNotFound("hey")



# def is_ajax(request):
#     return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'

# @login_required
# def InExamChangeView(request,examnum): 
#     # req_type : 1 for conf , 2 for change
#     # student_qs_list=list(student_score.questions_list.keys())
#     if request.method == "POST" and is_ajax(request):
#         selected_exam       = get_object_or_404(models.Exam,pk=examnum)
#         student_score=selected_exam.examscore_set.get(exam_average_reffer = request.user.id)
#         student_qs_list=student_score.questions_list
#         if request.POST.get("req_type") == "conf" and selected_exam.is_running() :            
#             student_qs=student_qs_list[student_score.active_question_number-1]
#             selected_question=get_object_or_404(models.Question,pk=UUID(student_qs))
#             # qt=selected_question.question_time
#             qt=datetime. now() + timedelta(seconds=selected_question.question_time)    
#             stu_choice=student_score.choices_list[student_score.active_question_number-1]        
#             if student_score.last_question_time is None:        
#                 student_score.last_question_time=timezone.now()
#                 if student_score.choices_list[student_score.active_question_number-1] == 0 :
#                     student_score.choices_list[student_score.active_question_number-1] = "1"
#                 student_score.save()
#             else:
#                 a=timezone.now() - student_score.last_question_time
#                 a=round(a.total_seconds())
#                 if (selected_question.question_time-a)<=0 :
#                     if student_score.active_question_number <10:
#                         student_score.active_question_number +=1
#                     student_score.last_question_time=timezone.now()
#                     student_score.save()
#                     student_qs=student_qs_list[student_score.active_question_number-1]
#                     selected_question=get_object_or_404(models.Question,pk=UUID(student_qs))                    
#                     # qt=selected_question.question_time
#                     qt=datetime. now() + timedelta(seconds=selected_question.question_time)
#                 else:
#                     # qt=qt-a
#                     qt=datetime. now() + timedelta(seconds=(selected_question.question_time-a))
#             choices=selected_question.choice_set.all()
#             # print(selected_question.question_headline)
#             # print(selected_question.question_time)
#             return JsonResponse({
#                 "success":True,
#                 "active_question_number":student_score.active_question_number,
#                 "u_choice":student_score.user_choice[student_score.active_question_number-1],
#                 "q_time":qt,
#                 "q_id":student_qs,
#                 "q_img":selected_question.question_img.url,
#                 "q_text":selected_question.question_text,

#                 # Choice 1 
#                 "c1_id":str(choices[0].choice_id),
#                 "c1_txt":choices[0].choice_text,
#                 "c1_img":choices[0].choice_img.url,                

#                 # Choice 2 
#                 "c2_id":str(choices[1].choice_id),
#                 "c2_txt":choices[1].choice_text,
#                 "c2_img":choices[1].choice_img.url,

#                 # Choice 3 
#                 "c3_id":str(choices[2].choice_id),
#                 "c3_txt":choices[2].choice_text,
#                 "c3_img":choices[2].choice_img.url,

#                 # Choice 4
#                 "c4_id":str(choices[3].choice_id),
#                 "c4_txt":choices[3].choice_text,
#                 "c4_img":choices[3].choice_img.url,               

#                 "returns":student_score.returns_count,                
#                 "u_choices_list":student_score.user_choice,
#                 "u_q_list":student_qs_list,
#                 }, status=200)
#         elif request.POST.get("req_type") == "next" and selected_exam.is_running() and 0< student_score.active_question_number <11:
#             student_score.last_question_time=timezone.now()           
#             if student_score.active_question_number < 10:
#                 student_score.active_question_number +=1    
#             if student_score.choices_list[student_score.active_question_number-1] == 0 :
#                 student_score.choices_list[student_score.active_question_number-1] = "1"
#             student_score.save()
#             student_qs=student_qs_list[student_score.active_question_number-1]
#             selected_question=get_object_or_404(models.Question,pk=UUID(student_qs))
#             # print(selected_question.question_headline)
#             # print(selected_question.question_time)
#             choices=selected_question.choice_set.all()                  
#             return JsonResponse({
#                 "success":True,
#                 "active_question_number":student_score.active_question_number,
#                 "q_time":datetime. now() + timedelta(seconds=selected_question.question_time),
#                 "q_id":student_qs,
#                 "q_img":selected_question.question_img.url,
#                 "q_text":selected_question.question_text,

#                 # Choice 1 
#                 "c1_id":str(choices[0].choice_id),
#                 "c1_txt":choices[0].choice_text,
#                 "c1_img":choices[0].choice_img.url,                

#                 # Choice 2 
#                 "c2_id":str(choices[1].choice_id),
#                 "c2_txt":choices[1].choice_text,
#                 "c2_img":choices[1].choice_img.url,

#                 # Choice 3 
#                 "c3_id":str(choices[2].choice_id),
#                 "c3_txt":choices[2].choice_text,
#                 "c3_img":choices[2].choice_img.url,

#                 # Choice 4
#                 "c4_id":str(choices[3].choice_id),
#                 "c4_txt":choices[3].choice_text,
#                 "c4_img":choices[3].choice_img.url,            

#                 "returns":student_score.returns_count,
#                 "u_choice":student_score.user_choice[student_score.active_question_number-1],
#                 "u_choices_list":student_score.user_choice,   
#                 }, status=200)
#         elif request.POST.get("req_type") == "3" and selected_exam.is_running():            
#             student_qs=student_qs_list[student_score.active_question_number-1]
#             selected_question=get_object_or_404(models.Question,pk=UUID(student_qs))
#             qt=selected_question.question_time            
#             a=timezone.now() - student_score.last_question_time
#             a=round(a.total_seconds())
#             if (qt-a)>0 :
#                 qt=qt-a
#                 return JsonResponse({
#                 "success":True,
#                 "q_time":qt,                              
#                 }, status=200)
#             else:
#                 return JsonResponse({
#                 "success":True,                                              
#                 }, status=200)
#         elif request.POST.get("req_type") == "finish" and selected_exam.is_running():
#             student_score.exam_finished=True
#             student_score.save()
#             return JsonResponse({
#                 "success":True,                            
#                 }, status=200)
#         elif request.POST.get("req_type") == "return" and selected_exam.is_running() and 0< int(request.POST.get("aqn")) <11 and student_score.returns_count>0:
#             student_score.last_question_time=timezone.now()  
#             student_qs=student_qs_list[int(request.POST.get("aqn"))-1]
#             student_score.returns_count -=1
#             student_score.save()
#             selected_question=get_object_or_404(models.Question,pk=UUID(student_qs))
            
#             # print(selected_question.question_headline)
#             # print(selected_question.question_time)
#             choices=selected_question.choice_set.all()                  
#             return JsonResponse({
#                 "success":True,
#                 "active_question_number":int(request.POST.get("aqn")),
#                 "q_time":datetime. now() + timedelta(seconds=selected_question.question_time),
#                 "q_id":student_qs,
#                 "q_img":selected_question.question_img.url,
#                 "q_text":selected_question.question_text,

#                 # Choice 1 
#                 "c1_id":str(choices[0].choice_id),
#                 "c1_txt":choices[0].choice_text,
#                 "c1_img":choices[0].choice_img.url,                

#                 # Choice 2 
#                 "c2_id":str(choices[1].choice_id),
#                 "c2_txt":choices[1].choice_text,
#                 "c2_img":choices[1].choice_img.url,

#                 # Choice 3 
#                 "c3_id":str(choices[2].choice_id),
#                 "c3_txt":choices[2].choice_text,
#                 "c3_img":choices[2].choice_img.url,

#                 # Choice 4
#                 "c4_id":str(choices[3].choice_id),
#                 "c4_txt":choices[3].choice_text,
#                 "c4_img":choices[3].choice_img.url,            

#                 "returns":student_score.returns_count,
#                 "u_choice":student_score.user_choice[int(request.POST.get("aqn"))-1],
#                 }, status=200)
#         elif not selected_exam.is_running():
#             HttpResponseRedirect("/result")
#         else:
#             HttpResponse("rid")
#     else:
#         return HttpResponse("Error occured")
#     pass

# @login_required
# def question_cal(request,examnum ):
    # if request.method == "POST" and is_ajax(request):
    #     selected_exam       = get_object_or_404(models.Exam,pk=examnum)
    #     student_score=selected_exam.examscore_set.get(exam_average_reffer = request.user.id)
    #     selected_choice=student_score.choices_list[student_score.active_question_number-1]
    #     if request.POST.get("act") == "set"  and selected_exam.is_running():            
    #         student_score.choices_list[int(request.POST.get("aqn"))-1]=request.POST.get("c_id")
    #         student_score.user_choice[int(request.POST.get("aqn"))-1]=int(request.POST.get("answer_number"))
    #         # print(student_score.choices_list)
    #         student_score.save()
    #         return JsonResponse({"success":True}, status=200)
    #     elif request.POST.get("act") == "rem" and selected_exam.is_running():
    #         student_score.choices_list[int(request.POST.get("aqn"))-1]=1
    #         student_score.user_choice[int(request.POST.get("aqn"))-1]=0
    #         student_score.save()
    #         return JsonResponse({"success":True}, status=200)
    #     elif not selected_exam.is_running():
    #         selected_choice=00
    #         return JsonResponse({
    #             "success":False,
    #             "unauthorized":1,
    #             }, status=400)        
    #     return JsonResponse({"success":False}, status=400)
    # return JsonResponse({"success":False}, status=400)
     
    