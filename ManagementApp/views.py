from ClassroomsPlatform.models import Classroom,ClassroomPresence
from AssignmentPlatform.models import Assignment,AssignmentScore,AssignmentAverage
from Frontend import scripts
from Frontend.upload_manager import auto_upload,process_content_urls
from ExamsPlatform.models import Question,Exam,ExamScore
from StudentsInfo.models import DirectMoney,SignedCheck,StudentUser,Books,Notification, UserNotification
from StudentsInfo.serializers import NotificationSerializer, UserNotificationSerializer
from django.contrib.auth.models import Group,User
from rest_framework.decorators import api_view,action
from rest_framework.response import Response
from rest_framework import status,viewsets,views
# from rest_framework.parsers import MultiPartParser
from rest_framework.decorators import api_view,permission_classes
from rest_framework.permissions import IsAuthenticated,IsAdminUser,BasePermission,AllowAny
from .serializers import GroupsSerializer,GroupSerializer,ClassroomSerializer,ClassroomsSerializer,AssignmentSerializer,ExamSerializer,QuestionSerializer,SmallUserSerializer,UserSerializer,AssignmentScoreSerializer,AssignmentScoresSerializer,SignedCheckSerializer,DirectMoneySerializer,ExamScoresSerializer,ExamSerializerWithQuestion,CreateStudentUserSerializer,UpdateStudentUserSerializer,ExamSerializerWithGroup,AssignmentSerializerWithGroup,BooksSerializer,BooksUserSerializer,ExamScoresSerializerWithExamName,ExamAverageNCSerializer
import pandas as pd
import io
import xlsxwriter
from django.http import HttpResponse
import openpyxl
import jdatetime
from datetime import date,datetime
from django.shortcuts import get_object_or_404
import logging
## SMS
# import requests
# import json
from sms_ir import SmsIr

API_KEY = "YOURAPIKEY"
LINE_NUMBER = "300000000000"
sms_ir = SmsIr(API_KEY, LINE_NUMBER)

logger = logging.getLogger('sms_manager')

send_sms=''

class IsStaffUser(BasePermission):
    def has_permission(self,request,view):
        return request.user and request.user.is_staff

@api_view(['POST'])
@permission_classes([IsAdminUser])
def change_user_password(request):
    username = request.data.get('username')
    new_password = request.data.get('new_password')

    if not username or not new_password:
        return Response({'error': 'Please provide both username and new_password'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    user.set_password(new_password)
    user.save()

    return Response({'success': 'Password updated successfully'}, status=status.HTTP_200_OK)    

@api_view(['POST'])
@permission_classes([IsAdminUser])
def zappier(self, request):
    scripts.temporaryscript()
    return Response({"message": "Run Successfully"}, status=status.HTTP_200_OK)    
#########################   Users - Groups - Attendance - SMS
class GroupsIndex (viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    http_method_names = ['get','post','delete','patch']
    permission_classes = [IsAdminUser,IsAuthenticated]
    search_fields=('name','group_time','group_day','group_grade','group_gender')
    def get_serializer_class(self):
        if self.action == 'list':
            return GroupsSerializer
        return GroupSerializer

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def attendance(self, request, pk=None):
        try:
            # دریافت تکلیف
            # assignment = get_object_or_404(Assignment, assignment_id=pk)
            pass
        except Exception as e:
            return Response(
                {"message": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    @action(detail=True, methods=['get'] , permission_classes=[AllowAny])
    def export_exam_scores(self, request, pk):
        group_id = pk
        group = Group.objects.get(id=group_id)
        response = HttpResponse(content_type='application/ms-excel')
        response['Content-Disposition'] = 'attachment; filename=exam_scores.xlsx'

        wb = openpyxl.Workbook()
        exams = Exam.objects.filter(exam_group_id=group_id, exam_finished=True)
        for exam in exams:
            ws = wb.create_sheet(exam.ExamName)
            ws.append(['Student', 'Score', 'Exam Presence', 'Questions Answer List', 'User Choice', 'Wrong Counts', 'None Counts'])
            exam_scores = ExamScore.objects.filter(exam=exam)
            for exam_score in exam_scores:
                student = exam_score.exam_average_reffer.user
                student_name = f'{student.first_name} {student.last_name}'  # or student.username
                if exam_score.exam_peresence:
                    score = exam_score.score
                    presence = exam_score.exam_peresence
                    questions_answer_list = exam_score.questions_answer_list
                    user_choice = exam_score.user_choice
                    wrong_counts = exam_score.wrong_counts
                    none_counts = exam_score.none_counts
                else:
                    score = '0'#absent
                    presence = 'غایب'
                    questions_answer_list = ''
                    user_choice = ''
                    wrong_counts = ''
                    none_counts = ''
                ws.append([student_name, score, presence, questions_answer_list, user_choice, wrong_counts, none_counts])
        wb.save(response)
        return response    
        
    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def export_assignment_scores(self, request, pk):
        group_id = pk
        # group = Group.objects.get(id=group_id)
        # # 
        # filename = f'{group.name}_Assignment_summary.xlsx'
        # response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        # # response = HttpResponse(output.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        # response['Content-Disposition'] = f'attachment; filename={filename}'
        # # 
        response = HttpResponse(content_type='application/ms-excel')
        response['Content-Disposition'] ='attachment; filename=assignment_scores.xlsx'
        # group_id = pk
        # group = Group.objects.get(id=group_id)
        # filename = re.sub(r'[<>:"/\\|?*]', '', f'{group.name}_Assignment_summary.xlsx')  # remove invalid characters
        # response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        # response['Content-Disposition'] = f'attachment; filename={filename}'
        wb = openpyxl.Workbook()
        assignments = Assignment.objects.filter(assignment_group_id=group_id, assignment_finished=True)
        for assignment in assignments:
            ws = wb.create_sheet(assignment.AssignmentName)
            ws.append(['Student', 'Score', 'Assignment Presence', 'Assignment Marked'])
            assignment_scores = AssignmentScore.objects.filter(assignment=assignment)
            for assignment_score in assignment_scores:
                student = assignment_score.assignment_average_reffer.user
                student_name = f'{student.first_name} {student.last_name}'  # or student.username
                if assignment_score.assignment_presence:
                    score = assignment_score.score
                    presence = assignment_score.assignment_presence
                    marked = assignment_score.assignment_marked
                else:
                    score = '0'
                    presence = 'غایب'
                    marked = ''
                ws.append([student_name, score, presence, marked])
        wb.save(response)
        return response
    
class UsersIndex (viewsets.ModelViewSet):
    queryset = User.objects.filter(is_staff=False).order_by('-date_joined')
    serializer_class = UserSerializer
    http_method_names = ['get','post','delete','patch']
    permission_classes = [IsAdminUser,IsAuthenticated]
    search_fields=('first_name','last_name','username','groups__name','studentuser__student_type','groups__group_grade','groups__group_gender','studentuser__student_school','studentuser__mother_number','studentuser__registration_date')
    # def list(self, request):
    #     ordering = request.query_params.get('ordering', '-date_joined')
    #     queryset = User.objects.filter(is_staff=False).order_by(ordering)
    #     serializer = SmallUserSerializer(queryset, many=True)
    #     return Response(serializer.data)
    
    def get_serializer_class(self):
        if self.action == 'list':
            return SmallUserSerializer
        return UserSerializer

    def create(self, request, *args, **kwargs):
        user_data = request.data.copy()
        password = user_data.pop('password', None)
        user_serializer = self.get_serializer(data=user_data)
        user_serializer.is_valid(raise_exception=True)
        user_instance = user_serializer.save()
        if password:
            user_instance.set_password(password)
            user_instance.save()
    
        student_user_data = request.data.get('studentuser')
        if student_user_data:
            student_user_data['student_user'] = user_instance.id
            student_user_serializer = CreateStudentUserSerializer(data=student_user_data)
            student_user_serializer.is_valid(raise_exception=True)
            student_user_serializer.save()
    
        headers = self.get_success_headers(user_serializer.data)
        return Response(user_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def perform_create(self, serializer):
        instance = serializer.save()
        student_user = instance.studentuser
        student_user.student_group_info()
        student_user.create_averages()

    def partial_update(self, request, *args, **kwargs):
        # Update User instance
        user_instance = self.get_object()
        user_serializer = self.get_serializer(user_instance, data=request.data, partial=True)
        user_serializer.is_valid(raise_exception=True)
        user_serializer.save()
    
        # Update StudentUser instance
        student_user_data = request.data.get('studentuser')
        if student_user_data:
            student_user_instance = user_instance.studentuser
            student_user_serializer = UpdateStudentUserSerializer(student_user_instance, data=student_user_data, partial=True)
            student_user_serializer.is_valid(raise_exception=True)
            student_user_serializer.save()
            student_user_instance.student_group_info()
            student_user_instance.create_averages()
        return Response(user_serializer.data)
        
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def toggle_activation(self, request, pk=None):
        user = self.get_object()
        user.is_active = not user.is_active
        user.save()
        return Response({'status': 'success', 'is_active': user.is_active},status=status.HTTP_200_OK)
        
    @action(detail=True, methods=['get'], permission_classes=[IsAdminUser])
    def is_active(self, request, pk=None):
        user = self.get_object()
        return Response({'is_active': user.is_active},status=status.HTTP_200_OK)  
    
    @action(detail=True, methods=['get', 'patch'], permission_classes=[IsAdminUser])
    def user_books(self, request, pk=None):
        user = self.get_object()
        if request.method == 'GET':
            books = user.books_set.all()
            serializer = BooksUserSerializer(books, many=True)
            return Response(serializer.data,status=status.HTTP_200_OK)
        elif request.method == 'PATCH':
            book_ids = request.data.get('book_ids', [])
            books = Books.objects.filter(id__in=book_ids)
            user.books_set.set(books)
            return Response(status=status.HTTP_202_ACCEPTED)
        
    @action(detail=True, methods=['get', 'patch'], permission_classes=[IsAdminUser])
    def change_exam_noncountable(self, request, pk=None):
        user = self.get_object()

        # اگر ExamAverage وجود نداشت، None برگردانیم یا ایجاد کنیم؟
        exam_avg = getattr(user, 'examaverage', None)
        if exam_avg is None:
            return Response({"detail": "ExamAverage برای این کاربر تعریف نشده است."}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'GET':
            serializer = ExamAverageNCSerializer(exam_avg)
            return Response(serializer.data)

        elif request.method == 'PATCH':
            new_value = request.data.get('exams_noncountable')
            if new_value is not None:
                exam_avg.non_countable_count = new_value
                exam_avg.save(update_fields=['non_countable_count',])
                # اگر متدی برای آپدیت میانگین داری
                if hasattr(exam_avg, 'get_average'):
                    exam_avg.get_average()
            return Response(status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def classroom_presence_summary(self, request, pk=None):
        user = self.get_object()
    
        # Create an in-memory output file for the new workbook.
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
    
        # Create a worksheet and set the column headers.
        worksheet = workbook.add_worksheet()
        worksheet.write(0, 0, 'User')
        worksheet.write(0, 1, 'Classroom Name')
        worksheet.write(0, 2, 'Presence Percentage')
        worksheet.write(0, 3, 'Presence')
    
        # Get the data and write it to the worksheet.
        row = 1
        presences = ClassroomPresence.objects.select_related('classroom', 'classroom_average_reffer__user').filter(classroom_average_reffer__user=user)
        for presence in presences:
            worksheet.write(row, 0, presence.classroom_average_reffer.user.username)
            worksheet.write(row, 1, presence.classroom.ClassroomName)
            worksheet.write(row, 2, presence.classroom_presence_percentage)
            worksheet.write(row, 3, str(presence.classroom_presence))
            row += 1
    
        # Close the workbook and construct the response.
        workbook.close()
        output.seek(0)
        filename = f'{user.username}_classroom_presence_summary.xlsx'
        response = HttpResponse(output.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response

class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    http_method_names = ['get','post','delete','patch']
    def perform_create(self, serializer):
        notif = serializer.save()
        if not notif.is_persistent:
            # تمام کاربران همه گروه‌های انتخاب شده
            users = User.objects.filter(groups__in=notif.groups.all()).distinct().values_list('id', flat=True)
            UserNotification.objects.bulk_create(
                [UserNotification(user_id=u, notification=notif) for u in users]
            )

    @action(detail=True, methods=["get"], url_path="user")
    def user_notifications(self, request,pk=None):
        username = pk
        if not username:
            return Response({"error": "username required"}, status=status.HTTP_400_BAD_REQUEST)

        # نوتیف دائم گروه‌های کاربر
        persistent = Notification.objects.filter(
            groups__user__username=username, is_persistent=True, is_finished=False
        ).values("id", "title", "message","is_persistent")

        # نوتیف یکبارمصرف از UserNotification
        one_time = UserNotification.objects.filter(user__username=username).select_related("notification")
        return Response(list(persistent) + UserNotificationSerializer(one_time, many=True).data , status=status.HTTP_200_OK)

    @action(detail=True, methods=["delete"], url_path="read")
    def mark_as_read(self, request, pk=None):
        user_notif = get_object_or_404(UserNotification.objects.select_related("notification"), pk=pk)
        notif = user_notif.notification
        user_notif.delete()
        if not notif.user_notifications.exists():
            notif.is_finished = True
            notif.save(update_fields=["is_finished"])
        return Response({"status": "Read And Removed"},status=status.HTTP_200_OK)

class SMSManagerIndex(viewsets.ViewSet):
    permission_classes = [IsAdminUser, IsAuthenticated]
    # ✅ ارسال پیامک به یک فرد (پدر یا مادر)
    
    @action(detail=True, methods=['post'], url_path='individual')
    def send_individual(self, request, pk=None):
        recipient_type = request.data.get('recipient')  # 'father' یا 'mother'
        message_text = request.data.get('message')

        if recipient_type not in ['father', 'mother']:
            return Response({"error": "recipient must be 'father' or 'mother'"}, status=status.HTTP_400_BAD_REQUEST)
        if not message_text:
            return Response({"error": "message is required"}, status=status.HTTP_400_BAD_REQUEST)

        student = get_object_or_404(StudentUser, pk=pk)
        mobile = student.father_number if recipient_type == 'father' else student.mother_number

        if not mobile:
            return Response({"error": f"{recipient_type} number not available"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = sms_ir.send_sms(mobile, message_text, LINE_NUMBER)

            # ✅ ثبت در لاگ
            logger.info(f"Individual SMS sent | StudentID={pk} | Recipient={recipient_type} | Mobile={mobile} | Message='{message_text}' | Status={result}")

            return Response({"status": "sent", "response": result})
        except Exception as e:
            logger.error(f"Individual SMS error | StudentID={pk} | Error={str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ✅ ارسال گروهی (پیش‌فرض مادر، اگر نبود پدر)
    @action(detail=False, methods=['post'], url_path='group')
    def send_group(self, request):
        group_ids = request.data.get('group_ids')
        message_text = request.data.get('message')

        if not group_ids or not isinstance(group_ids, list):
            return Response({"error": "group_ids (list) is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not message_text:
            return Response({"error": "message is required"}, status=status.HTTP_400_BAD_REQUEST)

        mobiles = set()
        group_names = []

        for group_id in group_ids:
            group = Group.objects.filter(pk=group_id).first()
            if group:
                group_names.append(group.name)
                students = StudentUser.objects.filter(student_user__groups=group)
                for student in students:
                    if student.mother_number:
                        mobiles.add(student.mother_number)
                    elif student.father_number:
                        mobiles.add(student.father_number)

        if not mobiles:
            return Response({"error": "No valid numbers found"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = sms_ir.send_bulk_sms(list(mobiles), message_text, LINE_NUMBER)

            # ✅ ثبت در لاگ
            logger.info(f"Group SMS sent | Groups={group_names} | TotalNumbers={len(mobiles)} | Message='{message_text}' | Status={result}")

            return Response({"status": "sent", "total": len(mobiles), "response": result})
        except Exception as e:
            logger.error(f"Group SMS error | Groups={group_names} | Error={str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
#########################   CLASSROOM All Upload Set
class ClassroomsIndex (viewsets.ModelViewSet):
    queryset = Classroom.objects.all().order_by('-classroom_creation_time')
    serializer_class = ClassroomSerializer
    http_method_names = ['get','post','delete','patch']
    permission_classes = [IsAdminUser,IsAuthenticated]
    search_fields=('ClassroomName','classroom_headline','classroom_groups__name')    
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ClassroomsSerializer
        return ClassroomSerializer
        
    def perform_create(self, serializer):
        instance = serializer.save()
        instance.create_classroom_presence()
        process_content_urls(instance)

    def partial_update(self, request, *args, **kwargs):
        response = super().partial_update(request, *args, **kwargs)
        instance = self.get_object()
        instance.update_classroom_presence()
        process_content_urls(instance)
        return response
#########################    ASSIGNMENT   All Upload Set         
class AssignmentsIndex (viewsets.ModelViewSet):
    queryset = Assignment.objects.all().order_by('-assignment_creation_time')
    serializer_class = AssignmentSerializer
    http_method_names = ['get','post','delete','patch']
    permission_classes = [IsAdminUser,IsAuthenticated,IsStaffUser]
    search_fields=('AssignmentName','assignment_headline','assignment_group__name','assignment_permission','assignment_available_time_start','assignment_available_time_end')
    # def get_queryset(self):
    #     queryset = Assignment.objects.all()
    #     ordering = self.request.query_params.get('ordering', '-assignment_creation_time')
    #     if ordering is not None:
    #         queryset = queryset.order_by(ordering)
    #     return queryset
        
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return AssignmentSerializerWithGroup
        return super().get_serializer_class()
        
    def perform_create(self, serializer):
        instance = serializer.save()
        # هندل فایل‌های ارسالی
        file_obj = self.request.FILES.get('assignment_file')
        if file_obj:
            # print(instance.AssignmentName)
            # print(instance.assignment_group.name)
            download_url = auto_upload("assignment", instance, file_obj)
            instance.assignment_file = download_url

        file_obj_answer = self.request.FILES.get('assignment_answer_file')
        if file_obj_answer:
            download_url = auto_upload("assignment_answer", instance, file_obj_answer)
            instance.assignment_answer_file = download_url

        instance.save(update_fields=['assignment_file', 'assignment_answer_file'])
        instance.create_assignment_score()

    def partial_update(self, request, *args, **kwargs):
        response = super().partial_update(request, *args, **kwargs)
        instance = self.get_object()

        # هندل assignment_file
        file_assignment = self.request.FILES.get('assignment_file')
        if file_assignment:
            instance.assignment_file = auto_upload('assignment', instance, file_assignment)

        # هندل assignment_answer_file
        file_assignment_answer = self.request.FILES.get('assignment_answer_file')
        if file_assignment_answer:
            instance.assignment_answer_file = auto_upload('assignment_answer', instance, file_assignment_answer)

        if file_assignment or file_assignment_answer:
            instance.save(update_fields=['assignment_file', 'assignment_answer_file'])

        instance.create_assignment_score()
        instance.update_assignment_score()
        return response 
    
    @action(detail=True, methods=['get'], permission_classes=[IsAdminUser])
    def send_all_results_sms(self, request, pk=None):
        try:
            # دریافت تکلیف
            assignment = get_object_or_404(Assignment, assignment_id=pk)

            # ارسال پیامک نتایج
            send_sms(assignment)

            return Response(
                {"message": "SMS sent successfully."},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"message": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def reset_assignment_finished_for_assignment(self, request, pk=None):
        """
        بازنشانی وضعیت تکلیف:
        - assignment_permission=True
        - assignment_finished=False
        - تغییر زمان شروع و پایان تکلیف (در صورت ارسال)
        - تغییر وضعیت در AssignmentScore ها
        """
        try:
            # دریافت تکلیف
            assignment = get_object_or_404(Assignment, assignment_id=pk)

            # دریافت داده‌ها از کاربر
            start_time = request.data.get("assignment_available_time_start")
            end_time = request.data.get("assignment_available_time_end")

            # اعتبارسنجی و تبدیل به datetime در صورت ارسال
            if start_time:
                try:
                    assignment.assignment_available_time_start = datetime.fromisoformat(start_time)
                except ValueError:
                    return Response({"message": "Invalid start_time format. Use ISO format (e.g., 2025-07-24T14:30:00)."},
                                    status=status.HTTP_400_BAD_REQUEST)

            if end_time:
                try:
                    assignment.assignment_available_time_end = datetime.fromisoformat(end_time)
                except ValueError:
                    return Response({"message": "Invalid end_time format. Use ISO format (e.g., 2025-07-24T16:30:00)."},
                                    status=status.HTTP_400_BAD_REQUEST)

            # تغییر وضعیت‌های تکلیف
            assignment.assignment_permission = True
            assignment.assignment_finished = False
            assignment.save(update_fields=["assignment_permission", "assignment_finished", 
                                           "assignment_available_time_start", "assignment_available_time_end"])

            # بروزرسانی AssignmentScore ها
            updated_count = AssignmentScore.objects.filter(assignment=assignment).update(
                assignment_finished=False
            )

            return Response(
                {
                    "message": f"Assignment {assignment.assignment_id} has been reset successfully.",
                    "updated_assignment_scores": updated_count,
                    "assignment_start_time": assignment.assignment_available_time_start,
                    "assignment_end_time": assignment.assignment_available_time_end
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"message": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
class AssignmentScoresIndex (viewsets.ModelViewSet):
    queryset = AssignmentScore.objects.filter(assignment_presence=True).order_by('-updated_file_at')
    serializer_class = AssignmentScoreSerializer
    http_method_names = ['get','delete','patch']   
    permission_classes = [IsAdminUser,IsAuthenticated,IsStaffUser]
    search_fields=('assignment_average_reffer__user__first_name','assignment_average_reffer__user__last_name','assignment__AssignmentName','assignment_presence','assignment_finished','assignment_marked','assignment_marked_by')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return AssignmentScoresSerializer
        return AssignmentScoreSerializer   
    
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.assignment_marked = True
        instance.assignment_permission = False
        instance.assignment_marked_by = f"{request.user.first_name} {request.user.last_name}"
 
        # هندل فایل تصحیح‌شده
        teacher_file = request.FILES.get('assignment_teacher_file')
        if teacher_file:
            instance.assignment_teacher_file = auto_upload("assignment_teacher", instance, teacher_file)
            # ذخیره در مدل
            instance.save(update_fields=['assignment_teacher_file', 'assignment_marked', 'assignment_permission', 'assignment_marked_by'])
        else:
            # اگر فایل آپلود نشده بود، فقط فلگ‌ها رو آپدیت کن
            instance.save(update_fields=['assignment_marked', 'assignment_permission', 'assignment_marked_by'])

        # ادامه پروسه اصلی
        response = super().partial_update(request, *args, **kwargs)
        instance.refresh_from_db()
        instance.get_score()

        return response
    
    @action(detail=True, methods=['get'], permission_classes=[IsAdminUser])
    def send_result_sms(self, request, pk=None):
        try:
            # دریافت تکلیف
            assignment = get_object_or_404(Assignment, assignment_id=pk)

            # ارسال پیامک نتایج
            send_sms(assignment)

            return Response(
                {"message": "SMS sent successfully."},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"message": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )  
    # @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    # def identify_orphaned_assignments(self, request):
    #     scripts.identify_orphaned_files()
    #     return Response({"message": "Orphaned assignments identified and logged to 'orphaned_files.txt'."}, status=status.HTTP_200_OK)

    # @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    # def delete_orphaned_assignments(self, request):
    #     scripts.delete_orphaned_files()
    #     return Response({"message": "Orphaned assignments deleted and logged."}, status=status.HTTP_200_OK)
    # @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    # def debug_orphaned_assignments(self, request):
    #     scripts.debug_list_assignments()
    #     return Response({"message": "Debug scan completed and logged."}, status=status.HTTP_200_OK)

#########################   EXAMS Upload Done
class ExamsIndex (viewsets.ModelViewSet):
    queryset = Exam.objects.all().order_by('-exam_available_time_start')
    serializer_class = ExamSerializer
    http_method_names = ['get','post','delete','patch']
    permission_classes = [IsAdminUser,IsAuthenticated]
    search_fields=('ExamName','exam_available_time_start','exam_group__name')
    # def list(self, request, pk=None):
    #     ordering = request.query_params.get('ordering', '-exam_available_time_start',)
    #     queryset = Exam.objects.all().order_by(ordering)
    #     serializer = ExamSerializerWithGroup(queryset, many=True)
    #     return Response(serializer.data)
    
    # def retrieve(self, request, pk=None):
    #     # ordering = request.query_params.get('ordering', '-exam_available_time_start', '-exam_available_time_start','exam_creation_time')
    #     queryset = Exam.objects.all()#.order_by(ordering)
    #     exam = get_object_or_404(queryset, pk=pk)
    #     serializer = ExamSerializerWithQuestion(exam)
    #     return Response(serializer.data) 
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ExamSerializerWithGroup
        if self.action == 'retrieve':
            return ExamSerializerWithQuestion    
        return ExamSerializer
            
    def perform_create(self, serializer):
        instance = serializer.save()
        # هندل آپلود فایل آزمون
        exam_description_file = self.request.FILES.get('exam_description')
        exam_answer_file = self.request.FILES.get('exam_answer_file')

        if exam_description_file:
            uploaded_path = auto_upload("exam_description",instance,exam_description_file)
            instance.exam_description = uploaded_path

        if exam_answer_file:
            uploaded_path = auto_upload("exam_answer",instance,exam_answer_file)
            instance.exam_answer_file = uploaded_path
        instance.save()
        # سایر عملیات
        instance.merge_question_answer_images()
        instance.set_exam_time()
        instance.create_exam_score()
        # eta = instance.exam_available_time_end + timedelta(seconds=1)
        # finish_exam.apply_async((instance.exam_id,), eta=eta)

    def partial_update(self, request, *args, **kwargs):
        response = super().partial_update(request, *args, **kwargs)
        instance = self.get_object()

        # آپلود در صورت وجود فایل جدید
        exam_description_file = request.FILES.get('exam_description')
        exam_answer_file = request.FILES.get('exam_answer_file')

        if exam_description_file:
            uploaded_path = auto_upload("exam_description", instance, exam_description_file)
            instance.exam_description = uploaded_path

        if exam_answer_file:
            uploaded_path = auto_upload("exam_answer", instance, exam_answer_file)
            instance.exam_answer_file = uploaded_path
            
        instance.save()
        instance.merge_question_answer_images()
        instance.set_exam_time()
        instance.create_exam_score()
        instance.update_exam_score()
        # instance.finish_exam()
        return response
    
    @action(detail=True, methods=['get'], permission_classes=[IsAdminUser])
    def send_all_results_sms(self, request, pk=None):
        try:
            # دریافت تکلیف
            exam = get_object_or_404(Exam, exam_id=pk)

            # ارسال پیامک نتایج
            send_sms(exam)

            return Response(
                {"message": "SMS sent successfully."},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"message": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class ExamScoresIndex (viewsets.ModelViewSet):
    # queryset = ExamScore.objects.all()
    serializer_class = ExamScoresSerializer
    http_method_names = ['get','post','delete','patch']
    permission_classes = [IsAdminUser,IsAuthenticated]
    
    def get_queryset(self):
        queryset = ExamScore.objects.all()
        ordering = self.request.query_params.get('ordering', '-updated_at')
        if ordering is not None:
            queryset = queryset.order_by(ordering)
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ExamScoresSerializerWithExamName
        return ExamScoresSerializer
        
    @action(detail=True, methods=['get',], permission_classes=[IsAdminUser])
    def user_scores_list(self, request, pk=None):
        exam_scores = ExamScore.objects.filter(exam_average_reffer__user__pk=pk)
        # serializer = self.get_serializer(exam_scores, many=True)
        serializer = ExamScoresSerializerWithExamName(exam_scores, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], permission_classes=[IsAdminUser])
    def send_result_sms(self, request, pk=None):
        try:
            # دریافت تکلیف
            exam = get_object_or_404(Exam, exam_id=pk)

            # ارسال پیامک نتایج
            send_sms(exam)

            return Response(
                {"message": "SMS sent successfully."},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"message": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class QuestionsIndex(viewsets.ModelViewSet):
    serializer_class = QuestionSerializer
    http_method_names = ['get', 'post', 'delete', 'patch']
    permission_classes = [IsAdminUser, IsAuthenticated]
    search_fields = ('question_headline', 'question_category', 'question_grade', 'question_book')

    def get_queryset(self):
        queryset = Question.objects.all()
        ordering = self.request.query_params.get('ordering', '-question_creation_time')
        if ordering is not None:
            queryset = queryset.order_by(ordering)
        return queryset
    
    def perform_create(self, serializer):
        instance = serializer.save()

        # بررسی فایل‌های ارسالی برای سوال
        question_img_file = self.request.FILES.get('question_img')
        question_answer_img_file = self.request.FILES.get('question_answer_img')

        if question_img_file:
            uploaded_path = auto_upload("question", instance, question_img_file)
            instance.question_img = uploaded_path

        if question_answer_img_file:
            uploaded_path = auto_upload("question_answer", instance, question_answer_img_file)
            instance.question_answer_img = uploaded_path
            
        instance.save()
        
    def partial_update(self, request, *args, **kwargs):
        response = super().partial_update(request, *args, **kwargs)
        instance = self.get_object()

        # آپلود در صورت وجود فایل جدید
        question_img_file = request.FILES.get('question_img')
        question_answer_img_file = request.FILES.get('question_answer_img')

        if question_img_file:
            uploaded_path = auto_upload("question", instance, question_img_file)
            instance.question_img = uploaded_path

        if question_answer_img_file:
            uploaded_path = auto_upload("question_answer", instance, question_answer_img_file)
            instance.question_answer_img = uploaded_path

        instance.save()
        return response    

##################  MONEY  
class SignedCheckIndex (viewsets.ModelViewSet):
    queryset = SignedCheck.objects.all()
    serializer_class = SignedCheckSerializer
    http_method_names = ['get','post','delete','patch']
    permission_classes = [IsAdminUser,IsAuthenticated]

class BooksIndex (viewsets.ModelViewSet):
    queryset = Books.objects.all()
    serializer_class = BooksSerializer
    http_method_names = ['get','post','delete','patch']
    permission_classes = [IsAdminUser,IsAuthenticated]

class DirectMoneyIndex (viewsets.ModelViewSet):
    queryset = DirectMoney.objects.all()
    serializer_class = DirectMoneySerializer
    http_method_names = ['get','post','delete','patch']
    permission_classes = [IsAdminUser,IsAuthenticated]

############################# Uploads
  
###########Upload working stable version
class UploadExcelView(views.APIView):
    http_method_names = ['post']
    permission_classes = [IsAdminUser,IsAuthenticated]
    def post(self, request):
        file = request.FILES['file']
        # data = pd.read_excel(file)
        data = pd.read_excel(file, dtype={'کد ملی': str, 'شماره دانش آموز': str, 'شماره پدر': str, 'شماره مادر': str, 'شماره منزل': str})
        
        field_mapping = {
            'father_name': 'نام پدر',
            'phone_number': 'شماره دانش آموز',
            'father_number': 'شماره پدر',
            'mother_number': 'شماره مادر',
            'home_number': 'شماره منزل',
            'address': 'آدرس',
            'student_school': 'مدرسه',
            'student_type': 'رشته',
            'student_gender': 'جنسیت',
            'student_grade': 'مقطع'
        }
        for _, row in data.iterrows():
            # if pd.isna(row['کد ملی']) or row['کد']=='انصراف':
            #     continue
            if pd.isna(row['کد ملی']):
                continue
            # Get or create User object
            username = str(row['کد ملی'])
            password = username[-4:]
            user, created = User.objects.get_or_create(username=username)
            if created:
                user.set_password(password)
            user.first_name = row['نام']
            user.last_name = row['نام خانوادگی']
            user.save()

            group_name = row['گروه']
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                group.group_time=row['ساعت کلاس']
                group.group_day=row['روز کلاس']
                group.group_grade=row['مقطع']
                group.group_gender=row['جنسیت']
                group.save()
            user.groups.clear()
            user.groups.add(group)

            if not pd.isna(row['تاریخ پرداخت']):
                try:
                    year, month, day = map(int, row['تاریخ پرداخت'].split('/'))
                    payment_date = jdatetime.date(year, month, day).togregorian()
                except ValueError as e:
                    print(f"Invalid payment date: {e}")
                    payment_date = None
            else:
                payment_date = None
            
            if not pd.isna(row['تاریخ چک']):
                try:
                    year, month, day = map(int, row['تاریخ چک'].split('/'))
                    check_date = jdatetime.date(year, month, day).togregorian()
                except ValueError as e:
                    print(f"Invalid check date: {e}")
                    check_date = None
            else:
                check_date = None
            
            # if not pd.isna(row['تاریخ ثبت نام']):
            #     try:
            #         year, month, day = map(int, row['تاریخ ثبت نام'].split('/'))
            #         registration_date = jdatetime.date(year, month, day).togregorian()
            #     except ValueError as e:
            #         print(f"Invalid registration date: {e}")
            #         registration_date = None
            # else:
            #     registration_date = None
            
            # Create StudentUser object
            student_user, created = StudentUser.objects.get_or_create(student_user=user)
            for field, column in field_mapping.items():
                if not pd.isna(row[column]):
                    setattr(student_user, field, row[column])
                    
            student_user.student_status='در حال تحصیل'
            # student_user.student_description=row['توضیحات دانش آموز']
            student_user.registration_date = date.today()
            student_user.save()
            student_user.create_averages()
            
            if not pd.isna(row['مبلغ چک']):
                signed_check_kwargs = {
                    "student": user,
                    "amout": row.get('مبلغ چک', 0),
                    "check_date": str(row.get('تاریخ چک',  "-")),
                    "check_number": str(row.get('شماره چک',  "-")),
                    "bank": row.get('نام بانک',  "-"),
                    "description": row.get('توضیحات چک', "-")
                } 
                signed_check = SignedCheck.objects.create(**signed_check_kwargs)
                
            # Create DirectMoney object
            if not pd.isna(row['مبلغ نقدی']):
                card_number = row.get('4 رقم کارت', 0)
                if pd.isna(card_number):
                    card_number = 0
                direct_money_kwargs = {
                    "student": user,
                    "amout": row.get('مبلغ نقدی', 0),
                    "payment_date": str(row.get('تاریخ پرداخت',  "-")),
                    "refrence_number": row.get('شماره مرجع', "-"),
                    "following_number": row.get('شماره پیگیری',"-"),
                    "card_number":str(row.get('چهار رقم کارت',  "-")),
                    "payment_method": row.get('انتقال / POS', "-"),
                    "bank": row.get('بانک عامل', "-"),
                    "description": row.get('توضیحات نقدی', "-")
                }
                
                direct_money = DirectMoney.objects.create(**direct_money_kwargs)
                

        return Response(status=status.HTTP_201_CREATED)

 ####last working 100%       
