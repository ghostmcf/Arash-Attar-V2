from ClassroomsPlatform.models import Classroom,ClassroomPresence
from AssignmentPlatform.models import Assignment,AssignmentScore,AssignmentAverage
from AssignmentPlatform import scripts
from ExamsPlatform.models import Question,Exam,ExamScore
from StudentsInfo.models import DirectMoney,SignedCheck,StudentUser,Books
from django.contrib.auth.models import Group,User
from rest_framework.decorators import api_view,action
from rest_framework.response import Response
from rest_framework import status,viewsets,views
# from rest_framework.parsers import MultiPartParser
from rest_framework.decorators import api_view,permission_classes
from rest_framework.permissions import IsAuthenticated,IsAdminUser,BasePermission,AllowAny
from .serializers import GroupsSerializer,GroupSerializer,ClassroomSerializer,ClassroomsSerializer,AssignmentSerializer,ExamSerializer,QuestionSerializer,SmallUserSerializer,UserSerializer,AssignmentScoreSerializer,AssignmentScoresSerializer,SignedCheckSerializer,DirectMoneySerializer,ExamScoresSerializer,ExamSerializerWithQuestion,CreateStudentUserSerializer,UpdateStudentUserSerializer,ExamSerializerWithGroup,AssignmentSerializerWithGroup,BooksSerializer,BooksUserSerializer,ExamScoresSerializerWithExamName
import pandas as pd
import io
import xlsxwriter
from django.http import HttpResponse
import openpyxl
import jdatetime
from django.shortcuts import get_object_or_404
# from django.core.cache import cache
# from django.contrib.sessions.models import Session

class IsStaffUser(BasePermission):
    def has_permission(self,request,view):
        return request.user and request.user.is_staff


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
    
#########################   Users and Groups
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
    # def list(self, request):
    #     queryset = Group.objects.all()
    #     serializer = GroupsSerializer(queryset, many=True)
    #     return Response(serializer.data)
        
    @action(detail=True, methods=['get'] , permission_classes=[AllowAny])
    def export_exam_scores(self, request, pk):
        group_id = pk
        group = Group.objects.get(id=group_id)
        response = HttpResponse(content_type='application/ms-excel')
        response['Content-Disposition'] = 'attachment; filename=exam_scores.xlsx'
        # filename = re.sub(r'[<>:"/\\|?*]', '', group.name)
        # response['Content-Disposition'] = 'attachment; filename={}Exams.xlsx'.format(group.name)
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
    # parser_classes = [MultiPartParser]
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
    #######################  
    # def retrive(self, request, pk=None):
    #     response = {'message': 'Update function is not offered in this path.'}
    #     return Response(response, status=status.HTTP_403_FORBIDDEN)
        
        
        
    # def create(self, request, *args, **kwargs):
    #     user_serializer = self.get_serializer(data=request.data)
    #     user_serializer.is_valid(raise_exception=True)
    #     user_instance = user_serializer.save()

    #     student_user_data = request.data.get('studentuser')
    #     if student_user_data:
    #         student_user_data['student_user'] = user_instance.id
    #         student_user_serializer = CreateStudentUserSerializer(data=student_user_data)
    #         student_user_serializer.is_valid(raise_exception=True)
    #         student_user_serializer.save()

    #     headers = self.get_success_headers(user_serializer.data)
    #     return Response(user_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
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
        return Response({'status': 'success', 'is_active': user.is_active})
        
    @action(detail=True, methods=['get'], permission_classes=[IsAdminUser])
    def is_active(self, request, pk=None):
        user = self.get_object()
        return Response({'is_active': user.is_active})  
    
    @action(detail=True, methods=['get', 'patch'], permission_classes=[IsAdminUser])
    def user_books(self, request, pk=None):
        user = self.get_object()
        if request.method == 'GET':
            books = user.books_set.all()
            serializer = BooksUserSerializer(books, many=True)
            return Response(serializer.data)
        elif request.method == 'PATCH':
            book_ids = request.data.get('book_ids', [])
            books = Books.objects.filter(id__in=book_ids)
            user.books_set.set(books)
            return Response(status=status.HTTP_202_ACCEPTED)
        # if request.method == 'GET':
        #     # books = Books.objects.filter(student=user)
        #     books = user.Books.all(student=user)
        #     serializer = BooksUserSerializer(books, many=True)
        #     return Response(serializer.data)
        # elif request.method == 'PATCH':
        #     serializer = BooksSerializer(data=request.data, many=True)
        #     if serializer.is_valid():
        #         serializer.save()
        #         return Response(serializer.data)
        #     else:
        #         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        # elif request.method == 'PATCH':
        #     # Clear the existing books
        #     user.books_set.clear()
    
        #     # Validate and save the new books
        #     serializer = BooksSerializer(data=request.data, many=True)
        #     if serializer.is_valid():
        #         serializer.save()
        #         # Add the new books to the user
        #         for book in serializer.instance:
        #             book.student.add(user)
        #         return Response(serializer.data)
        #     else:
        #         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)        
            # book_ids = request.data.get('book_ids', [])
            # # Replace the user's books with the new list
            # new_books = Books.objects.filter(id__in=book_ids)
            # user.books_set.set(new_books)
            # # Return the updated list of user's books
            # updated_books = Books.objects.filter(student=user)
            # serializer = BooksUserSerializer(updated_books, many=True)
            # return Response(serializer.data)
    
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

#########################   CLASSROOM
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

    def partial_update(self, request, *args, **kwargs):
        response = super().partial_update(request, *args, **kwargs)
        instance = self.get_object()
        instance.update_classroom_presence()
        # for _ in Classroom.objects.all():
        #     _.update_classroom_presence()
        # cache.clear()
        return response

#########################    ASSIGNMENT            
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
        instance.create_assignment_score()
        # eta = instance.assignment_available_time_end + timedelta(seconds=1)
        # finish_assignment_cron.apply_async((instance.assignment_id,), eta=eta)

    def partial_update(self, request, *args, **kwargs):
        response = super().partial_update(request, *args, **kwargs)
        instance = self.get_object()
        instance.create_assignment_score()
        instance.update_assignment_score()
        return response    
    
class AssignmentScoresIndex (viewsets.ModelViewSet):
    queryset = AssignmentScore.objects.filter(assignment_presence=True).order_by('-updated_file_at')
    serializer_class = AssignmentScoreSerializer
    http_method_names = ['get','delete','patch']   
    permission_classes = [IsAdminUser,IsAuthenticated,IsStaffUser]
    search_fields=('assignment_average_reffer__user__first_name','assignment_average_reffer__user__last_name','assignment__AssignmentName','assignment_presence','assignment_finished','assignment_marked','assignment_marked_by')
    # def list(self, request):
    #     ordering = request.query_params.get('ordering', '-updated_file_at')
    #     queryset = AssignmentScore.objects.all().filter(assignment_presence=True).order_by(ordering)
    #     serializer = AssignmentScoresSerializer(queryset, many=True)
    #     return Response(serializer.data) 
    
    def get_serializer_class(self):
        if self.action == 'list':
            return AssignmentScoresSerializer
        return AssignmentScoreSerializer
        
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.assignment_marked = True
        instance.assignment_permission = False
        instance.assignment_marked_by = f"{request.user.first_name} {request.user.last_name}"
        instance.save(update_fields=['assignment_marked', 'assignment_permission', 'assignment_marked_by'])
        response = super().partial_update(request, *args, **kwargs)
        instance.refresh_from_db()
        instance.get_score()
        return response    
    
    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def identify_orphaned_assignments(self, request):
        scripts.identify_orphaned_files()
        return Response({"message": "Orphaned assignments identified and logged to 'orphaned_files.txt'."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def delete_orphaned_assignments(self, request):
        scripts.delete_orphaned_files()
        return Response({"message": "Orphaned assignments deleted and logged to 'deleted_files.txt'."}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def reset_files(self, request):
        """
        اکشن ادمین برای ریست مسیر تمام فایل‌های مرتبط
        """
        scripts.reset_assignment_files_to_default()
        return Response(
            {"message": "تمام فایل‌های تکالیف به مسیر پیش‌فرض ریست شدند."},
            status=status.HTTP_200_OK
        )
        
    # @action(detail=True, methods=['get'], permission_classes=[IsAdminUser])
    # def reset_assignment_finished_for_assignment(self, request, pk=None):
    #     try:
    #         # یافتن تکلیف بر اساس assignment_id (که همان pk است)
    #         assignment = Assignment.objects.get(assignment_id=pk)
    #     except Assignment.DoesNotExist:
    #         return Response({"message": "Assignment not found."}, status=status.HTTP_404_NOT_FOUND)

    #     try:
    #         # تغییر وضعیت assignment_finished به False برای تمامی رکوردهای مرتبط در AssignmentScore
    #         assignment_scores = AssignmentScore.objects.filter(assignment=assignment)
    #         updated_count = assignment_scores.update(assignment_finished=False)

    #         return Response({"message": f"Successfully updated {updated_count} assignment scores for assignment {assignment.assignment_id}."}, status=status.HTTP_200_OK)

    #     except Exception as e:
    #         return Response({"message": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    @action(detail=True, methods=['get'], permission_classes=[IsAdminUser])
    def reset_assignment_finished_for_assignment(self, request, pk=None):
        """
        بازنشانی وضعیت تکلیف: 
        - `assignment_permission=True`
        - `assignment_finished=False`
        - تنظیم مجدد مقادیر `assignment_finished=False` و `assignment_marked=False` در `AssignmentScore`
        """
        try:
            # دریافت تکلیف موردنظر
            assignment = get_object_or_404(Assignment, assignment_id=pk)

            # تغییر وضعیت‌های تکلیف
            assignment.assignment_permission = True
            assignment.assignment_finished = False
            assignment.save()

            # تغییر وضعیت در `AssignmentScore` های مربوطه
            assignment_scores = AssignmentScore.objects.filter(assignment=assignment)
            updated_count = assignment_scores.update(assignment_finished=False, assignment_marked=False)

            return Response(
                {
                    "message": f"Assignment {assignment.assignment_id} has been reset.",
                    "updated_assignment_scores": updated_count
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"message": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )        
            
#########################   EXAMS
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
        instance.merge_question_answer_images()
        instance.set_exam_time()
        instance.create_exam_score()
        # eta = instance.exam_available_time_end + timedelta(seconds=1)
        # finish_exam.apply_async((instance.exam_id,), eta=eta)

    def partial_update(self, request, *args, **kwargs):
        response = super().partial_update(request, *args, **kwargs)
        instance = self.get_object()
        instance.merge_question_answer_images()
        instance.set_exam_time()
        instance.create_exam_score()
        instance.update_exam_score()
        # instance.finish_exam()
        return response
        
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
        
class QuestionsIndex (viewsets.ModelViewSet):
    serializer_class = QuestionSerializer
    http_method_names = ['get','post','delete','patch']
    permission_classes = [IsAdminUser,IsAuthenticated]
    search_fields=('question_headline','question_category','question_grade','question_book')
    def get_queryset(self):
        queryset = Question.objects.all()
        ordering = self.request.query_params.get('ordering', '-question_creation_time')
        if ordering is not None:
            queryset = queryset.order_by(ordering)
        return queryset

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
    # def retrieve(self, request, pk=None):
    #         queryset = DirectMoney.objects.all().filter(student=pk)
    #         # group = get_object_or_404(queryset, pk=pk)
    #         serializer = DirectMoneySerializer(group)
    #         return Response(serializer.data)           
    
    
    # def create(self, request): 
    #     post_data = request.data
    #     a=self.serializer = ClassroomSerializer(classroom)
    #     return Response(data="return data")

############################# Upload




###########Upload working stable version
class UploadExcelView(views.APIView):
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
            
            if not pd.isna(row['تاریخ ثبت نام']):
                try:
                    year, month, day = map(int, row['تاریخ ثبت نام'].split('/'))
                    registration_date = jdatetime.date(year, month, day).togregorian()
                except ValueError as e:
                    print(f"Invalid registration date: {e}")
                    registration_date = None
            else:
                registration_date = None
            
            # Create StudentUser object
            student_user, created = StudentUser.objects.get_or_create(student_user=user)
            for field, column in field_mapping.items():
                if not pd.isna(row[column]):
                    setattr(student_user, field, row[column])
                    
            student_user.student_status='در حال تحصیل'
            # student_user.student_description=row['توضیحات دانش آموز']
            student_user.registration_date = registration_date
            student_user.save()
            student_user.create_averages()
            
            if not pd.isna(row['مبلغ چک']):
                signed_check_kwargs = {
                    "student": user,
                    "amout": row.get('مبلغ چک', 0),
                    "check_date": check_date,
                    "check_number": str(row.get('شماره چک',  "-")),
                    "bank": row.get('ثبت صیادی',  "-"),
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
                    "payment_date": payment_date,
                    "refrence_number": row.get('شماره مرجع', "-"),
                    "following_number": row.get('شماره پیگیری',"-"),
                    "card_number":card_number,
                    "payment_method": row.get('انتقال / POS', "-"),
                    "bank": row.get('بانک عامل', "-"),
                    "description": row.get('توضیحات نقدی', "-")
                }
                
                direct_money = DirectMoney.objects.create(**direct_money_kwargs)
                

        return Response(status=status.HTTP_201_CREATED)


# class UploadExcelView(views.APIView):
#     def post(self, request):
#         file = request.FILES['file']
#         data = pd.read_excel(file)

#         # for _, row in data.iterrows():
#         #     # Create User object
#         #     username = str(row['username'])
#         #     password = username[-4:]
#         #     user = User.objects.create_user(
#         #         username=username,
#         #         first_name=row['first_name'],
#         #         last_name=row['last_name'],
#         #     )
#         #     user.set_password(password)
#         #     user.save()

#         #     # Add user to group
#         #     group_name = row['usrgroup']
#         #     group, created = Group.objects.get_or_create(name=group_name)
#         #     user.groups.add(group)
            
#         #     # Create StudentUser object
#         #     student_user = StudentUser.objects.create(
#         #         student_user=user,
#         #         father_name=row['father_name'],
#         #         phone_number=row['phone_number'],
#         #         father_number=row['father_number'],
#         #         mother_number=row['mother_number'],
#         #         home_number=row['home_number'],
#         #         address=row['address'],
#         #         registration_date=row['registration_date'],
#         #         # avatar=row['avatar'],
#         #         student_school=row['student_school'],
#         #         # average_exam=row['average_exam'],
#         #         # average_assignment=row['average_assignment'],
#         #         student_type=row['student_type'],
#         #         student_gender=row['student_gender'],
#         #         student_grade=row['student_grade']
#         #     )
#         for _, row in data.iterrows():
#             # Get or create User object
#             username = str(row['username'])
#             password = username[-4:]
#             user, created = User.objects.get_or_create(username=username)
#             if created:
#                 user.set_password(password)
#             user.first_name = row['first_name']
#             user.last_name = row['last_name']
#             user.save()

#             # Add user to group
#             group_name = row['usrgroup']
#             group, created = Group.objects.get_or_create(name=group_name)
#             user.groups.clear()
#             user.groups.add(group)

#             # Get or create StudentUser object
#             student_user, created = StudentUser.objects.get_or_create(student_user=user)
#             student_user.father_name = row['father_name']
#             student_user.phone_number = row['phone_number']
#             student_user.father_number = row['father_number']
#             student_user.mother_number = row['mother_number']
#             student_user.home_number = row['home_number']
#             student_user.address = row['address']
#             student_user.registration_date = row['registration_date']
#             student_user.student_school = row['student_school']
#             student_user.student_type = row['student_type']
#             student_user.student_gender = row['student_gender']
#             student_user.student_grade = row['student_grade']
#             student_user.save()
#             student_user.create_averages()
#             # Create SignedCheck object
#             signed_check = SignedCheck.objects.create(
#                 student=user,
#                 amout=row['cheque_amout'],
#                 check_date=row['cheque_date'],
#                 check_number=row['cheque_number'],
#                 bank=row['bank'],
#                 description=row['c_description']
#             )

#             # Create DirectMoney object
#             direct_money = DirectMoney.objects.create(
#                 student=user,
#                 amout=row['money_amout'],
#                 payment_date=row['payment_date'],
#                 refrence_number=row['refrence_number'],
#                 following_number=row['following_number'],
#                 card_number=row['card_number'],
#                 payment_method=row['payment_method'],
#                 bank=row['bank'],
#                 description=row['d_description']
#             )

#         return Response(status=status.HTTP_201_CREATED)






# class UploadExcelView(views.APIView):
#     def post(self, request):
#         file = request.FILES['file']
#         data = pd.read_excel(file)
#         field_mapping = {
#             'father_name': 'father_name',
#             'phone_number': 'phone_number',
#             'father_number': 'father_number',
#             'mother_number': 'mother_number',
#             'home_number': 'home_number',
#             'address': 'address',
#             'registration_date': 'registration_date',
#             'student_school': 'student_school',
#             'student_type': 'student_type',
#             'student_gender': 'student_gender',
#             'student_grade': 'student_grade'
#         }
#         for _, row in data.iterrows():
#             # Get or create User object
#             username = str(row['username'])
#             password = username[-4:]
#             user, created = User.objects.get_or_create(username=username)
#             if created:
#                 user.set_password(password)
#             user.first_name = row['first_name']
#             user.last_name = row['last_name']
#             user.save()

#             # Add user to group
#             group_name = row['usrgroup']
#             group, created = Group.objects.get_or_create(name=group_name)
#             user.groups.clear()
#             user.groups.add(group)

#             if not pd.isna(row['payment_date']):
#                 year, month, day = map(int, row['payment_date'].split('/'))
#                 payment_date = jdatetime.date(year, month, day).togregorian()
#             else:
#                 payment_date = None
            
#             if not pd.isna(row['cheque_date']):
#                 year, month, day = map(int, row['cheque_date'].split('/'))
#                 check_date = jdatetime.date(year, month, day).togregorian()
#             else:
#                 check_date = None
            
#             if not pd.isna(row['registration_date']):
#                 year, month, day = map(int, row['registration_date'].split('/'))
#                 registration_date = jdatetime.date(year, month, day).togregorian()
#             else:
#                 registration_date = None
            
#             # Create StudentUser object
#             student_user, created = StudentUser.objects.get_or_create(student_user=user)
#             student_user.father_name = row['father_name']
#             student_user.phone_number = row['phone_number']
#             student_user.father_number = row['father_number']
#             student_user.mother_number = row['mother_number']
#             student_user.home_number = row['home_number']
#             student_user.address = row['address']
#             student_user.registration_date = registration_date
#             student_user.student_school = row['student_school']
#             student_user.student_type = row['student_type']
#             student_user.student_gender = row['student_gender']
#             student_user.student_grade = row['student_grade']
#             student_user.save()
            
#             # Create SignedCheck object
#             if not pd.isna(row['cheque_amout']):
#                 signed_check = SignedCheck.objects.create(
#                     student=user,
#                     amout=row['cheque_amout'],
#                     check_date=check_date,
#                     check_number=str(row['cheque_number']),
#                     bank=row['c_bank'],
#                     description=row['c_description']
#                 )
                
#             # Create DirectMoney object
#             if not pd.isna(row['money_amout']):
#                 direct_money = DirectMoney.objects.create(
#                     student=user,
#                     amout=row['money_amout'],
#                     payment_date=payment_date,
#                     refrence_number=row['refrence_number'],
#                     following_number=row['following_number'],
#                     card_number=row['card_number'],
#                     payment_method=row['payment_method'],
#                     bank=row['d_bank'],
#                     description=row['d_description']
#                 )

#         return Response(status=status.HTTP_201_CREATED)



# class UploadExcelView(views.APIView):
#     def post(self, request):
#         file = request.FILES['file']
#         data = pd.read_excel(file)
#         field_mapping = {
#             'father_name': 'نام پدر',
#             'phone_number': 'شماره دانش آموز',
#             'father_number': 'شماره پدر',
#             'mother_number': 'شماره مادر',
#             'home_number': 'شماره منزل',
#             'address': 'آدرس',
#             'registration_date': 'تاریخ ثبت نام',
#             'student_school': 'مدرسه',
#             'student_type': 'رشته',
#             'student_gender': 'جنسیت',
#             'student_grade': 'مقطع'
#         }
#         for _, row in data.iterrows():
#             if pd.isna(row['کدملی']) or row['کد']='انصراف' :
#                 continue
#             # Get or create User object
#             username = str(row['کدملی'])
#             password = username[-4:]
#             user, created = User.objects.get_or_create(username=username)
#             if created:
#                 user.set_password(password)
#             user.first_name = row['نام']
#             user.last_name = row['نام خانوادگی']
#             user.save()

#             # Add user to group
#             group_name = row['گروه']
#             group, created = Group.objects.get_or_create(name=group_name)
#             if created:
#                 group.group_time=row['ساعت کلاس']
#                 group.group_day=row['روز کلاس']
#                 group.group_grade=row['مقطع']
#                 group.group_gender=row['جنسیت']
#             user.groups.clear()
#             user.groups.add(group)

#             if not pd.isna(row['تاریخ']):
#                 year, month, day = map(int, row['تاریخ'].split('/'))
#                 payment_date = jdatetime.date(year, month, day).togregorian()
#             else:
#                 payment_date = None
            
#             if not pd.isna(row['تاریخ چک']):
#                 year, month, day = map(int, row['تاریخ چک'].split('/'))
#                 check_date = jdatetime.date(year, month, day).togregorian()
#             else:
#                 check_date = None
            
#             if not pd.isna(row['تاریخ ثبت نام']):
#                 year, month, day = map(int, row['تاریخ ثبت نام'].split('/'))
#                 registration_date = jdatetime.date(year, month, day).togregorian()
#             else:
#                 registration_date = None
            
#             # Create StudentUser object
#             student_user, created = StudentUser.objects.get_or_create(student_user=user)
#             for field, column in field_mapping.items():
#                 if not pd.isna(row[column]):
#                     setattr(student_user, field, row[column])
            
#             student_user.save()
#             student_user.create_averages()#this line should be performed for all users
            
#             # Create SignedCheck object
#             if not pd.isna(row['مبلغ چک']):
#                 signed_check = SignedCheck.objects.create(
#                     student=user,
#                     amout=row['مبلغ چک'],
#                     check_date=check_date,
#                     check_number=str(row['شماره چک']),
#                     bank=row['ثبت صیادی'],
#                     # description=row['c_description']
#                 )
                
                
#             # Create DirectMoney object
#             if not pd.isna(row['مبلغ نقدی']):
#                 direct_money = DirectMoney.objects.create(
#                     student=user,
#                     amout=row['مبلغ نقدی'],
#                     payment_date=payment_date,
#                     refrence_number=row['شماره مرجع'],
#                     following_number=row['شماره پیگیری'],
#                     card_number=row['4 رقم کارت'],
#                     payment_method=row['انتقال / POS'],
#                     bank=row['بانک عامل'],
#                     description=row['توضیحات']
#                 )

#         return Response(status=status.HTTP_201_CREATED)
        
        
        
        
 ####last working 100%       
# class UploadExcelView(views.APIView):
#     def post(self, request):
#         file = request.FILES['file']
#         data = pd.read_excel(file)
#         field_mapping = {
#             'father_name': 'نام پدر',
#             'phone_number': 'شماره دانش آموز',
#             'father_number': 'شماره پدر',
#             'mother_number': 'شماره مادر',
#             'home_number': 'شماره منزل',
#             'address': 'آدرس',
#             'student_school': 'مدرسه',
#             'student_type': 'رشته',
#             'student_gender': 'جنسیت',
#             'student_grade': 'مقطع'
#         }
#         for _, row in data.iterrows():
#             if pd.isna(row['کدملی']) or row['کد']='انصراف':
#                 continue
#             # Get or create User object
#             username = str(row['کد ملی'])
#             password = username[-4:]
#             user, created = User.objects.get_or_create(username=username)
#             if created:
#                 user.set_password(password)
#             user.first_name = row['نام']
#             user.last_name = row['نام خانوادگی']
#             user.save()

#             group_name = row['گروه']
#             group, created = Group.objects.get_or_create(name=group_name)
#             if created:
#                 group.group_time=row['ساعت کلاس']
#                 group.group_day=row['روز کلاس']
#                 group.group_grade=row['مقطع']
#                 group.group_gender=row['جنسیت']
#             user.groups.clear()
#             user.groups.add(group)

#             if not pd.isna(row['تاریخ']):
#                 try:
#                     year, month, day = map(int, row['تاریخ'].split('/'))
#                     payment_date = jdatetime.date(year, month, day).togregorian()
#                 except ValueError as e:
#                     print(f"Invalid payment date: {e}")
#                     payment_date = None
#             else:
#                 payment_date = None
            
#             if not pd.isna(row['تاریخ چک']):
#                 try:
#                     year, month, day = map(int, row['تاریخ چک'].split('/'))
#                     check_date = jdatetime.date(year, month, day).togregorian()
#                 except ValueError as e:
#                     print(f"Invalid check date: {e}")
#                     check_date = None
#             else:
#                 check_date = None
            
#             if not pd.isna(row['تاریخ ثبت نام']):
#                 try:
#                     year, month, day = map(int, row['تاریخ ثبت نام'].split('/'))
#                     registration_date = jdatetime.date(year, month, day).togregorian()
#                 except ValueError as e:
#                     print(f"Invalid registration date: {e}")
#                     registration_date = None
#             else:
#                 registration_date = None
            
#             # Create StudentUser object
#             student_user, created = StudentUser.objects.get_or_create(student_user=user)
#             for field, column in field_mapping.items():
#                 if not pd.isna(row[column]):
#                     setattr(student_user, field, row[column])
            
#             student_user.registration_date = registration_date
#             student_user.save()
#             student_user.create_averages()
            
#             if not pd.isna(row['مبلغ چک']):
#                 signed_check_kwargs = {
#                     "student": user,
#                     "amout": row.get('مبلغ چک', 0),
#                     "check_date": check_date,
#                     "check_number": str(row.get('شماره چک',  "-")),
#                     "bank": row.get('ثبت صیادی',  "-"),
#                     # "description": row.get('c_description', 0)
#                 }
#                 signed_check = SignedCheck.objects.create(**signed_check_kwargs)
                
#             # Create DirectMoney object
#             if not pd.isna(row['مبلغ نقدی']):
#                 card_number = row.get('4 رقم کارت', 0)
#                 if pd.isna(card_number):
#                     card_number = 0
#                 direct_money_kwargs = {
#                     "student": user,
#                     "amout": row.get('مبلغ نقدی', 0),
#                     "payment_date": payment_date,
#                     "refrence_number": row.get('شماره مرجع', "-"),
#                     "following_number": row.get('شماره پیگیری',"-"),
#                     "card_number":card_number,
#                     "payment_method": row.get('انتقال / POS', "-"),
#                     "bank": row.get('بانک عامل', "-"),
#                     "description": row.get('توضیحات', "-")
#                 }
                
#                 direct_money = DirectMoney.objects.create(**direct_money_kwargs)
                

#         return Response(status=status.HTTP_201_CREATED)

