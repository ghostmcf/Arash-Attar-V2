# Create your views here.
from rest_framework.decorators import api_view
from rest_framework.response import Response
from ExamsPlatform import serializers as E_serializer
from AssignmentPlatform import serializers as A_serializer

from rest_framework import status
from rest_framework.decorators import api_view,permission_classes
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from rest_framework.views import APIView

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ExamBox(request):
    try:
        now = timezone.now()
        exams_item = request.user.groups.all()[0].exam_set.filter(
            exam_available_time_start__lte=now
        ).order_by('-exam_permission', '-exam_available_time_end')[0]
        exams_avg = request.user.examaverage
    except IndexError:  # Catching specific error when no exams are available
        return Response(status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return Response((E_serializer.ExamSerializer(exams_item).data, E_serializer.ExamAverageSerializer(exams_avg).data), status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def AssignmentBox(request):
    try:
        now = timezone.now()
        assignment_listed = request.user.groups.all()[0].assignment_set.filter(
            assignment_available_time_start__lte=now
        ).order_by('-assignment_available_time_start')[:3]
        assignment_avg = request.user.assignmentaverage
    except IndexError:  # Catching specific error when user has no groups
        return Response(status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        listed_assignment = list(assignment_listed)
        assignment_dict = [A_serializer.AssignmentSerializer(i).data for i in listed_assignment]
        return Response((assignment_dict, A_serializer.AssignmentAverageSerializer(assignment_avg).data), status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ClassroomBox(request):
    try:
        classroom_average   = request.user.classroomaverage#.absence_count
    except:
        return Response(status=status.HTTP_404_NOT_FOUND)
    else:
        return Response({'Total':classroom_average.classroompresence_set.all().count(),'abscent_count':classroom_average.absence_count},status=status.HTTP_200_OK)
        


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def UserInfoBox(request):
    try:
        selected_group   = request.user.groups.all()[0]
    except:
        return Response(status=status.HTTP_404_NOT_FOUND)
    else:
        return Response({'group_day':selected_group.group_day,'group_time':selected_group.group_time,'group_grade':selected_group.group_grade,'group_type':request.user.studentuser.student_type,},status=status.HTTP_200_OK)


