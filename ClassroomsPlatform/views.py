from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from . import models ,serializers
from rest_framework import status,viewsets
from django.db.models import Count
from rest_framework.permissions import IsAuthenticated



class ClassroomViewset(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def get_by_headline(self, request):
        try:
            group = request.user.groups.all()[0]
            class_list = group.classroom_set.filter(classroom_headline=request.POST.get("headline")).order_by('-classroom_status','-classroom_available_time_end',)
        except:
            return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            serializer = serializers.ClassroomSerializer(class_list, many=True)
            return Response(serializer.data)

    def retrieve(self, request, pk=None):
        selected_class = get_object_or_404(models.Classroom, pk=pk)
        try:
            # presence = request.user.classroomaverage.classroompresence_set.select_related('classroom_average_reffer').get(classroom=pk)
            presence = request.user.classroomaverage.classroompresence_set.get(classroom=pk)
            presence.classroom_permission
        except:
            return Response({"message":"You are not allowed"}, status=status.HTTP_403_FORBIDDEN)
        else:
            class_serializer = serializers.ClassroomSerializer(selected_class)
            presence_serializer = serializers.ClassPresenceSerializer(presence)
            return Response({"Class": class_serializer.data, "Presence": presence_serializer.data})
    
    @action(detail=False)
    def headlines(self, request):
        try:
            group = request.user.groups.all()[0]
            class_list = group.classroom_set.values('classroom_headline').annotate(count=Count('classroom_headline')).order_by('-count')
        except:
            return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            serializer = serializers.ClassroomHeadlineSerializer(class_list, many=True)
            return Response(serializer.data) 
    @action(detail=True, methods=['patch'])
    def update_presence(self, request, pk=None):
        try:
            presence = request.user.classroomaverage.classroompresence_set.get(classroom=pk)
        except:
            return Response({"message":"You are not allowed"}, status=status.HTTP_403_FORBIDDEN)
        else:
            # data = request.data['classroom_presence']
            # classroom_presence_data = json.loads(data)
            # classroom_presence_data = request.data['classroom_presence']
            # if len(classroom_presence_data) > 0:
            #     # presence_percentage = sum(classroom_presence_data.values()) / len(classroom_presence_data)
            #     presence_percentage = sum(classroom_presence_data) / len(classroom_presence_data)
            #     models.ClassroomPresence.objects.filter(pk=presence.pk).update(
            #         classroom_presence_percentage=presence_percentage,
            #         classroom_presence=classroom_presence_data
            #     )
            #     return Response(status=status.HTTP_200_OK)
            classroom_presence_data = request.data['classroom_presence']
            numeric_data = [x for x in classroom_presence_data if isinstance(x, (int, float))]
            if len(numeric_data) > 0:
                presence_percentage = sum(numeric_data) / len(numeric_data)
                models.ClassroomPresence.objects.filter(pk=presence.pk).update(
                    classroom_presence_percentage=presence_percentage,
                    classroom_presence=classroom_presence_data
                )
                return Response(status=status.HTTP_200_OK)
    # @action(detail=True, methods=['patch'])
    # def update_presence(self, request, pk=None):
    #     try:
    #         presence = request.user.classroomaverage.classroompresence_set.get(classroom=pk)
    #     except:
    #         return Response({"message":"You are not allowed"}, status=status.HTTP_403_FORBIDDEN)
    #     else:
    #         data = request.data['classroom_presence']
    #         classroom_presence_data = json.loads(data)
    #         if len(classroom_presence_data) > 0:
    #             presence_percentage = sum(classroom_presence_data) / len(classroom_presence_data)
    #             presence.classroompresence_set.filter(classroom=pk).update(
    #                 classroom_presence_percentage=presence_percentage,
    #                 classroom_presence=classroom_presence_data
    #             )
    #             return Response(status=status.HTTP_200_OK)
