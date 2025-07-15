
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework import views,viewsets, parsers, response, status
from django.utils import timezone

from rest_framework.decorators import action
from .models import Assignment, AssignmentScore
from .serializers import AssignmentSerializer, AssignmentScoreSerializer
import os
import jdatetime
import pytz
import fitz
import logging

# Create your views here.

class AssignmentViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        try:
            assignment_list = request.user.assignmentaverage.assignmentscore_set.select_related('assignment').order_by('-assignment_finished', '-assignment__assignment_available_time_end')
        except:
            return Response({"message": "No data"}, status=status.HTTP_404_NOT_FOUND)
        else:
            assignment_dict = []
            for i in assignment_list:
                if i.assignment.assignment_available_time_start < timezone.now():
                    i.assignment.finish_assignment()
                    if not i.assignment_marked and i.assignment_presence:
                        if i.assignment_finished:
                            guided_score="در انتظار تصحیح"
                        else:
                            guided_score=AssignmentScoreSerializer(i).data
                        if i.assignment_student_file:
                            guided_name=i.assignment.assignment_headline+"(در انتظار تصحیح)"
                            # guided_headline = f'<a href="{i.assignment_student_file}" target="_blank">{guided_name}</a>'
                            persian_months = {
                                "Farvardin": "فروردین",
                                "Ordibehesht": "اردیبهشت",
                                "Khordad": "خرداد",
                                "Tir": "تیر",
                                "Mordad": "مرداد",
                                "Shahrivar": "شهریور",
                                "Mehr": "مهر",
                                "Aban": "آبان",
                                "Azar": "آذر",
                                "Dey": "دی",
                                "Bahman": "بهمن",
                                "Esfand": "اسفند",
                            }
                            tehran_tz = pytz.timezone("Asia/Tehran")
                            localized_time = i.updated_file_at.astimezone(tehran_tz)
                            jalali_datetime = jdatetime.datetime.fromgregorian(datetime=localized_time)
                            persian_month = persian_months[jalali_datetime.strftime('%B')]
                            guided_headline = f"{i.assignment.assignment_headline} (در انتظار تصحیح) ارسال در: {jalali_datetime.strftime('%d')} {persian_month} {jalali_datetime.strftime('%H:%M')}"
                        else:
                            guided_headline = f'{i.assignment.assignment_headline} (در انتظار تصحیح – ایراد در فایل)'
                    else:
                        guided_score=AssignmentScoreSerializer(i).data
                        guided_headline=i.assignment.assignment_headline
                    temp_dict = {
                        # "score": AssignmentScoreSerializer(i).data,
                        "score": guided_score,
                        "assignment_available_time_end": i.assignment.assignment_available_time_end,
                        "assignment_file": i.assignment.assignment_file.url,
                        "AssignmentName": i.assignment.AssignmentName,
                        # "assignment_headline": i.assignment.assignment_headline,
                        "assignment_headline": guided_headline,
                        "assignment_available_time_end": i.assignment.assignment_available_time_end,
                        "assignment_finished": i.assignment.assignment_finished,
                        "assignment_permission": i.assignment.assignment_permission,
                        "assignment_extra_permission": i.assignment_permission,
                    }
                    try :
                        temp_dict.update({
                            "assignment_student_file": i.assignment_student_file.url,
                        })
                    except:
                        pass
                    
                    if i.assignment.assignment_finished:
                        try :
                            temp_dict.update({
                                "assignment_teacher_file": i.assignment_teacher_file.url,
                            })
                        except: 
                            pass
                        
                    assignment_dict.append(temp_dict)
            return Response(assignment_dict, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        selected_assignment = get_object_or_404(Assignment, pk=pk)
        try:
            a = request.user.assignmentaverage.assignmentscore_set.select_related('assignment').get(assignment=pk)
            a.assignment_permission
        except:
            return Response({"message": "You are not allowed"}, status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({"Assignment": AssignmentSerializer(selected_assignment).data, "Presence": AssignmentScoreSerializer(a).data}, status=status.HTTP_200_OK)



# class FileUploadView(views.APIView):
#     parser_classes = (parsers.MultiPartParser, parsers.FormParser)
#     def post(self, request, assignment_id, format=None):
#         # Check if the conditions are met
#         assignment_score = AssignmentScore.objects.get(assignment=assignment_id,assignment_average_reffer=request.user.assignmentaverage)
#         assignment = assignment_score.assignment
        
#         # if (assignment_score.assignment_finished or not assignment.assignment_permission or assignment.assignment_available_time_end > timezone.now()) and not assignment_score.assignment_permission:
#         #     return response.Response({"message": "You are not allowed to upload the file"}, status=status.HTTP_403_FORBIDDEN)
        
#         if (assignment_score.assignment_finished or not assignment.assignment_permission) and not assignment_score.assignment_permission:
#             return response.Response({"message": "You are not allowed to upload the file"}, status=status.HTTP_403_FORBIDDEN)
        
#         # Continue with the file upload
#         file_obj = request.data.get('assignment_file')
#         if file_obj is None:
#             # Handle the case where the assignment_file key does not exist
#             return response.Response({"message": "No file was uploaded"}, status=status.HTTP_400_BAD_REQUEST)
#         assignment_score.assignment_student_file = file_obj
#         assignment_score.assignment_presence = True
#         assignment_score.assignment_permission = False
#         assignment_score.updated_file_at = timezone.now()
#         # assignment_score.save()
#         try:
#             assignment_score.save()
#         except Exception as e:
#             # Handle the error
#             return response.Response({"message": "An error occurred while saving the file"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#         return response.Response(status=status.HTTP_204_NO_CONTENT)



# Setup logging
logger = logging.getLogger(__name__)


##Ver2.0
# class FileUploadView(views.APIView):
#     parser_classes = (parsers.MultiPartParser, parsers.FormParser)

#     def post(self, request, assignment_id, format=None):
#         current_time = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
#         user = request.user.username if request.user.is_authenticated else 'Anonymous'
        
#         # Log the attempt with timestamp and username
#         logger.info(f"{current_time} Attempting file upload by user: {user} for assignment ID: {assignment_id}")

#         try:
#             assignment_score = AssignmentScore.objects.get(assignment=assignment_id, assignment_average_reffer=request.user.assignmentaverage)
#             assignment = assignment_score.assignment
            
#             # Permission check
#             if assignment_score.assignment_finished :
#                 logger.warning(f"{current_time} Upload attempt denied for user: {user} due to permissions or assignment status.")
#                 return response.Response({"message": "You are not allowed to upload the file"}, status=status.HTTP_403_FORBIDDEN)
            
#             file_obj = request.data.get('assignment_file')
#             if file_obj is None:
#                 logger.error(f"{current_time} No file was uploaded - file object not found in request by user: {user}.")
#                 return response.Response({"message": "No file was uploaded"}, status=status.HTTP_400_BAD_REQUEST)
            
#             # Check file size
#             if file_obj.size > 10 * 1024 * 1024:  # Example limit: 10MB
#                 logger.error(f"{current_time} Upload attempt failed for user: {user} - file size exceeds limit.")
#                 return response.Response({"message": "File too large"}, status=status.HTTP_400_BAD_REQUEST)

#             # Check file type
#             if not file_obj.name.lower().endswith('.pdf'):
#                 logger.error(f"{current_time} Upload attempt failed for user: {user} - incorrect file type.")
#                 return response.Response({"message": "Invalid file type"}, status=status.HTTP_400_BAD_REQUEST)

#             # Assign file to model and update attributes
#             assignment_score.assignment_student_file = file_obj
#             assignment_score.assignment_presence = True
#             assignment_score.assignment_permission = False
#             assignment_score.updated_file_at = timezone.now()
            
#             assignment_score.save()
#             logger.info(f"{current_time} File uploaded and saved successfully by user: {user}.")
#             return response.Response(status=status.HTTP_204_NO_CONTENT)

#         except AssignmentScore.DoesNotExist:
#             logger.error(f"{current_time} AssignmentScore object not found by user: {user}.")
#             return response.Response({"message": "Assignment not found"}, status=status.HTTP_404_NOT_FOUND)
#         except Exception as e:
#             logger.error(f"{current_time} Unexpected error occurred during file upload by user: {user}: {str(e)}")
#             return response.Response({"message": f"An error occurred while saving the file: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



##Ver 2.8
# class FileUploadView(views.APIView):
#     parser_classes = (parsers.MultiPartParser, parsers.FormParser)

#     def post(self, request, assignment_id, format=None):
#         current_user = request.user.username if request.user.is_authenticated else 'Anonymous'
#         logger.info(f"---{timezone.now()} Attempting file upload by user: {current_user} for assignment ID: {assignment_id}")

#         try:
#             assignment_score = AssignmentScore.objects.get(assignment=assignment_id, assignment_average_reffer=request.user.assignmentaverage)
#             assignment = assignment_score.assignment

#             if assignment_score.assignment_finished :
#                 logger.warning("* Upload attempt denied due to permissions or assignment status.")
#                 return response.Response({"message": "You are not allowed to upload the file"}, status=status.HTTP_403_FORBIDDEN)

#             file_obj = request.data.get('assignment_file')
#             if not file_obj or not hasattr(file_obj, 'size'):
#                 logger.error("* No file was uploaded or the uploaded object is not a file.")
#                 return response.Response({"message": "No file was uploaded or invalid file type"}, status=status.HTTP_400_BAD_REQUEST)

#             logger.info(f"Received file: {file_obj.name} with size: {file_obj.size} bytes")
#             if file_obj.size > 10 * 1024 * 1024:  # 10MB size limit
#                 logger.error("* Upload attempt failed - file size exceeds limit.")
#                 return response.Response({"message": "File too large"}, status=status.HTTP_400_BAD_REQUEST)

#             if not file_obj.name.lower().endswith('.pdf'):
#                 logger.error("* Upload attempt failed - incorrect file type.")
#                 return response.Response({"message": "Invalid file type"}, status=status.HTTP_400_BAD_REQUEST)

#             assignment_score.assignment_student_file = file_obj
#             assignment_score.assignment_presence = True
#             assignment_score.assignment_permission = False
#             assignment_score.updated_file_at = timezone.now()
#             assignment_score.save()
#             logger.info("File uploaded and saved successfully.")

#             return response.Response(status=status.HTTP_204_NO_CONTENT)

#         except AssignmentScore.DoesNotExist:
#             logger.error("* AssignmentScore object not found.")
#             return response.Response({"message": "Assignment not found"}, status=status.HTTP_404_NOT_FOUND)
#         except Exception as e:
#             logger.error(f"* Unexpected error occurred during file upload: {str(e)}")
            # return response.Response({"message": f"An error occurred while saving the file: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#2.9 > With Deleting previous file
# class FileUploadView(views.APIView):
#     parser_classes = (parsers.MultiPartParser, parsers.FormParser)
#     def post(self, request, assignment_id, format=None):
#         current_user = request.user.username if request.user.is_authenticated else 'Anonymous'
#         logger.info(f"---{timezone.now()} Attempting file upload by user: {current_user} for assignment ID: {assignment_id}")

#         try:
#             assignment_score = AssignmentScore.objects.get(assignment=assignment_id, assignment_average_reffer=request.user.assignmentaverage)
#             assignment = assignment_score.assignment

#             if assignment_score.assignment_finished:
#                 logger.warning("* Upload attempt denied due to permissions or assignment status.")
#                 return response.Response({"message": "You are not allowed to upload the file"}, status=status.HTTP_403_FORBIDDEN)

#             file_obj = request.data.get('assignment_file')
#             if not file_obj or not hasattr(file_obj, 'size'):
#                 logger.error("* No file was uploaded or the uploaded object is not a file.")
#                 return response.Response({"message": "No file was uploaded or invalid file type"}, status=status.HTTP_400_BAD_REQUEST)

#             logger.info(f"Received file: {file_obj.name} with size: {file_obj.size} bytes")
#             if file_obj.size > 10 * 1024 * 1024:  # 10MB size limit
#                 logger.error("* Upload attempt failed - file size exceeds limit.")
#                 return response.Response({"message": "File too large"}, status=status.HTTP_400_BAD_REQUEST)

#             if not file_obj.name.lower().endswith('.pdf'):
#                 logger.error("* Upload attempt failed - incorrect file type.")
#                 return response.Response({"message": "Invalid file type"}, status=status.HTTP_400_BAD_REQUEST)

#             # حذف فایل قبلی اگر وجود داشته باشد
#             if assignment_score.assignment_student_file:
#                 old_file_path = assignment_score.assignment_student_file.path
#                 if os.path.exists(old_file_path):
#                     os.remove(old_file_path)
#                     logger.info(f"Previous file {old_file_path} deleted successfully.")

#             # ذخیره فایل جدید
#             assignment_score.assignment_student_file = file_obj
#             assignment_score.assignment_presence = True
#             assignment_score.assignment_permission = False
#             assignment_score.updated_file_at = timezone.now()
#             assignment_score.save()
#             logger.info("File uploaded and saved successfully.")

#             return response.Response(status=status.HTTP_204_NO_CONTENT)

#         except AssignmentScore.DoesNotExist:
#             logger.error("* AssignmentScore object not found.")
#             return response.Response({"message": "Assignment not found"}, status=status.HTTP_404_NOT_FOUND)
#         except Exception as e:
#             logger.error(f"* Unexpected error occurred during file upload: {str(e)}")
#             return response.Response({"message": f"An error occurred while saving the file: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




#2.9.8 > With Deleting previous file + Wont accept Corrupt file
class FileUploadView(views.APIView):
    parser_classes = (parsers.MultiPartParser, parsers.FormParser)
    permission_classes = [IsAuthenticated]
    def is_pdf_corrupt(self, file_obj):
        """ بررسی می‌کند که آیا فایل PDF خراب است یا خیر """
        try:
            file_obj.seek(0)  # رفتن به ابتدای فایل برای خواندن
            pdf_document = fitz.open(stream=file_obj.read(), filetype="pdf")  # تست باز کردن فایل
            pdf_document.close()
            file_obj.seek(0)  # ریست کردن موقعیت خواندن فایل
            return False  # فایل سالم است
        except Exception as e:
            logger.error(f"PDF file is corrupt: {str(e)}")
            return True  # فایل خراب است
    def post(self, request, assignment_id, format=None):
        current_user = request.user.username if request.user.is_authenticated else 'Anonymous'
        logger.info(f"---{timezone.now()} Attempting file upload by user: {current_user} for assignment ID: {assignment_id}")

        try:
            assignment_score = AssignmentScore.objects.get(assignment=assignment_id, assignment_average_reffer=request.user.assignmentaverage)
            assignment = assignment_score.assignment

            if assignment_score.assignment_finished:
                logger.warning("* Upload attempt denied due to permissions or assignment status.")
                return response.Response({"message": "You are not allowed to upload the file"}, status=status.HTTP_403_FORBIDDEN)

            file_obj = request.data.get('assignment_file')
            if not file_obj or not hasattr(file_obj, 'size'):
                logger.error("* No file was uploaded or the uploaded object is not a file.")
                return response.Response({"message": "No file was uploaded or invalid file type"}, status=status.HTTP_400_BAD_REQUEST)

            logger.info(f"Received file: {file_obj.name} with size: {file_obj.size} bytes")
            if file_obj.size > 10 * 1024 * 1024:  # 10MB size limit
                logger.error("* Upload attempt failed - file size exceeds limit.")
                return response.Response({"message": "File too large"}, status=status.HTTP_400_BAD_REQUEST)

            if not file_obj.name.lower().endswith('.pdf'):
                logger.error("* Upload attempt failed - incorrect file type.")
                return response.Response({"message": "Invalid file type"}, status=status.HTTP_400_BAD_REQUEST)
            # بررسی خراب بودن فایل PDF
            if self.is_pdf_corrupt(file_obj):
                logger.error("* Upload attempt failed - corrupt PDF file.")
                return response.Response({"message": "مشکلی در فایل ارسالی شما وجود دارد و رکورد جدید ثبت نمیشود"}, status=status.HTTP_400_BAD_REQUEST)
                
            # حذف فایل قبلی اگر وجود داشته باشد
            if assignment_score.assignment_student_file:
                old_file_path = assignment_score.assignment_student_file.path
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)
                    logger.info(f"Previous file {old_file_path} deleted successfully.")

            # ذخیره فایل جدید
            assignment_score.assignment_student_file = file_obj
            assignment_score.assignment_presence = True
            assignment_score.assignment_permission = False
            assignment_score.updated_file_at = timezone.now()
            assignment_score.save()
            logger.info("File uploaded and saved successfully.")

            return response.Response(status=status.HTTP_204_NO_CONTENT)

        except AssignmentScore.DoesNotExist:
            logger.error("* AssignmentScore object not found.")
            return response.Response({"message": "Assignment not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"* Unexpected error occurred during file upload: {str(e)}")
            return response.Response({"message": f"An error occurred while saving the file: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


