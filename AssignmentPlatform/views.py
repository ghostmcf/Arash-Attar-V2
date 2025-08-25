
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework import views,viewsets, parsers, response, status
from django.utils import timezone

from .models import Assignment, AssignmentScore
from .serializers import AssignmentSerializer, AssignmentScoreSerializer
import jdatetime
import pytz
import logging
from Frontend.upload_manager import auto_upload
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
                            # guided_headline = f"{i.assignment.assignment_headline} (در انتظار تصحیح) ارسال در: {jalali_datetime.strftime('%d')} {persian_month} {jalali_datetime.strftime('%H:%M')}"
                            guided_headline = f"{i.assignment.assignment_headline} (در انتظار تصحیح)"
                            guided_sentstatus = f" ارسال در: {jalali_datetime.strftime('%d')} {persian_month} {jalali_datetime.strftime('%H:%M')}"
                        else:
                            guided_headline = f'{i.assignment.assignment_headline} (در انتظار تصحیح – ایراد در فایل)'
                            # guided_headline = "ایراد در فایل"
                            guided_sentstatus= "ایراد در فایل"
                    else:
                        guided_score=AssignmentScoreSerializer(i).data
                        guided_headline= i.assignment.assignment_headline
                        guided_sentstatus= ""
                    temp_dict = {
                        # "score": AssignmentScoreSerializer(i).data,
                        "score": guided_score,
                        "assignment_available_time_end": i.assignment.assignment_available_time_end,
                        "assignment_file": i.assignment.assignment_file,
                        "AssignmentName": i.assignment.AssignmentName,
                        # "assignment_headline": i.assignment.assignment_headline,
                        "assignment_headline": guided_headline,
                        "assignment_filestatus": guided_sentstatus,
                        "assignment_available_time_end": i.assignment.assignment_available_time_end,
                        "assignment_finished": i.assignment.assignment_finished,
                        "assignment_extra_permission": i.assignment_permission,
                    }
                    try :
                        temp_dict.update({
                            "assignment_student_file": i.assignment_student_file,
                        })
                    except:
                        pass
                    
                    if i.assignment.assignment_finished:
                        try :
                            temp_dict.update({
                                "assignment_teacher_file": i.assignment_teacher_file,
                            })
                        except: 
                            pass
                        
                    assignment_dict.append(temp_dict)
            return Response(assignment_dict, status=status.HTTP_200_OK)
    def retrieve(self, request, pk=None):
        selected_assignment = get_object_or_404(Assignment, pk=pk)
        try:
            a = request.user.assignmentaverage.assignmentscore_set.select_related('assignment').get(assignment=pk)
        except AssignmentScore.DoesNotExist:
            return Response({"message": "You are not allowed"}, status=status.HTTP_403_FORBIDDEN)

        if a.assignment_finished:
            return Response({"message": "This assignment is already finished"}, status=status.HTTP_403_FORBIDDEN)

        return Response({
            "Assignment": AssignmentSerializer(selected_assignment).data,
            "Presence": AssignmentScoreSerializer(a).data
        }, status=status.HTTP_200_OK)
        
# Setup logging
logger = logging.getLogger("student_assignment")
logger.setLevel(logging.INFO)


#2.9.8 > With Deleting previous file + Wont accept Corrupt file
# class FileUploadView(views.APIView):
#     parser_classes = (parsers.MultiPartParser, parsers.FormParser)
#     permission_classes = [IsAuthenticated]
#     def is_pdf_corrupt(self, file_obj):
#         """ بررسی می‌کند که آیا فایل PDF خراب است یا خیر """
#         try:
#             file_obj.seek(0)  # رفتن به ابتدای فایل برای خواندن
#             pdf_document = fitz.open(stream=file_obj.read(), filetype="pdf")  # تست باز کردن فایل
#             pdf_document.close()
#             file_obj.seek(0)  # ریست کردن موقعیت خواندن فایل
#             return False  # فایل سالم است
#         except Exception as e:
#             logger.error(f"PDF file is corrupt: {str(e)}")
#             return True  # فایل خراب است
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
#             # بررسی خراب بودن فایل PDF
#             if self.is_pdf_corrupt(file_obj):
#                 logger.error("* Upload attempt failed - corrupt PDF file.")
#                 return response.Response({"message": "مشکلی در فایل ارسالی شما وجود دارد و رکورد جدید ثبت نمیشود"}, status=status.HTTP_400_BAD_REQUEST)
                
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



#   3.2.1   >   Upload Command + FTPS + Verfication + Log & Admin + Temp Storage
class FileUploadView(views.APIView):
    parser_classes = (parsers.MultiPartParser, parsers.FormParser)
    permission_classes = [IsAuthenticated]
    
    def post(self, request, assignment_id, format=None):
        current_user = request.user.username if request.user.is_authenticated else 'Anonymous'
        try:
            assignment_score = AssignmentScore.objects.get(
                assignment=assignment_id,
                assignment_average_reffer=request.user.assignmentaverage
            )
            logger.info(f"---Attempting: {current_user} - {assignment_id}|{assignment_score.id}")
            
            if assignment_score.assignment.finish_assignment():
                logger.error(f"* Upload attempt denied due to permissions or assignment status: {current_user}")
                return response.Response({"message": "You are not allowed to upload the file"}, status=status.HTTP_403_FORBIDDEN)
            
            file_obj = request.data.get('assignment_file')
            if not file_obj or not hasattr(file_obj, 'size'):
                logger.error(f"* No file was uploaded or the uploaded object is not a file: {current_user}")
                return response.Response({"message": "No file was uploaded or invalid file type"}, status=status.HTTP_400_BAD_REQUEST)

            # logger.info(f"Received file: {file_obj.name} with size: {file_obj.size} bytes {current_user}")
            logger.info(f"Received: {file_obj.size//1024}Kb {current_user} - {assignment_score.id}")
            
            if file_obj.size > 10 * 1024 * 1024:
                logger.error(f"* Upload attempt failed - file size exceeds limit: {current_user}")
                return response.Response({"message": "File too large"}, status=status.HTTP_400_BAD_REQUEST)

            if not file_obj.name.lower().endswith('.pdf'):
                logger.error("* Upload attempt failed - incorrect file type: {current_user}")
                return response.Response({"message": "Invalid file type"}, status=status.HTTP_400_BAD_REQUEST)
            
            logger.info(f"Uploading: {current_user} - {assignment_score.id}")
            assignment_score.assignment_student_file = auto_upload("assignment_student", assignment_score, file_obj)
            assignment_score.assignment_presence = True
            assignment_score.assignment_marked = False
            assignment_score.assignment_marked_by = ''
            assignment_score.updated_file_at = timezone.now()
            assignment_score.save(update_fields=['assignment_student_file', 'assignment_presence', 'updated_file_at','assignment_marked','assignment_marked_by'])
            logger.info(f"+++Successful: {current_user} - {assignment_score.id}")
            return response.Response({"message": "File uploaded and verified successfully", "file_url": assignment_score.assignment_student_file}, status=status.HTTP_200_OK)

        except AssignmentScore.DoesNotExist:
            return response.Response({"message": "Assignment not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return response.Response({"message": f"Error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
