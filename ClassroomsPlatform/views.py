from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from . import models ,serializers
from rest_framework import status,viewsets
from django.db.models import Count
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes


@extend_schema_view(
    retrieve=extend_schema(
        parameters=[OpenApiParameter('id', OpenApiTypes.STR, OpenApiParameter.PATH)],
        responses=OpenApiTypes.OBJECT,
    ),
    get_by_headline=extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT),
    headlines=extend_schema(responses=OpenApiTypes.OBJECT),
    update_presence=extend_schema(
        parameters=[OpenApiParameter('id', OpenApiTypes.STR, OpenApiParameter.PATH)],
        request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT),
    update_video_progress=extend_schema(
        parameters=[OpenApiParameter('id', OpenApiTypes.STR, OpenApiParameter.PATH)],
        request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT),
)
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
        except models.ClassroomPresence.DoesNotExist:
            return Response({"message":"You are not allowed"}, status=status.HTTP_403_FORBIDDEN)

        # ورودی اجباری است و باید لیست باشد
        classroom_presence_data = request.data.get('classroom_presence')
        if not isinstance(classroom_presence_data, list):
            return Response({"message": "classroom_presence (list) is required"}, status=status.HTTP_400_BAD_REQUEST)

        numeric_data = [x for x in classroom_presence_data if isinstance(x, (int, float))]
        if len(numeric_data) == 0:
            return Response({"message": "No numeric presence values provided"}, status=status.HTTP_400_BAD_REQUEST)

        presence_percentage = sum(numeric_data) / len(numeric_data)
        models.ClassroomPresence.objects.filter(pk=presence.pk).update(
            classroom_presence_percentage=presence_percentage,
            classroom_presence=classroom_presence_data
        )
        return Response(status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'], url_path='video-progress')
    def update_video_progress(self, request, pk=None):
        """پلیر دوره‌ای موقعیت فعلی ویدیو را می‌فرستد؛ بک‌اند «دورترین نقطه» را نگه می‌دارد.
        body: {"content_index": 1..5, "position": ثانیه, "duration": ثانیه (اختیاری)}"""
        try:
            presence = request.user.classroomaverage.classroompresence_set.get(classroom=pk)
        except models.ClassroomPresence.DoesNotExist:
            return Response({"message": "You are not allowed"}, status=status.HTTP_403_FORBIDDEN)

        try:
            content_index = int(request.data.get('content_index'))
            position = float(request.data.get('position'))
        except (TypeError, ValueError):
            return Response({"message": "content_index و position لازم‌اند"}, status=status.HTTP_400_BAD_REQUEST)
        if not 1 <= content_index <= 5 or position < 0:
            return Response({"message": "مقدار نامعتبر"}, status=status.HTTP_400_BAD_REQUEST)

        duration = request.data.get('duration')
        try:
            duration = float(duration) if duration is not None else None
        except (TypeError, ValueError):
            duration = None

        progress = presence.video_progress if isinstance(presence.video_progress, dict) else {}
        key = str(content_index)
        entry = progress.get(key) or {}
        new_max = max(float(entry.get('max_position') or 0), position)   # فقط رو به جلو رشد می‌کند
        dur = duration or entry.get('duration')
        percent = round(min(new_max / dur * 100, 100), 2) if dur else entry.get('percent', 0)
        progress[key] = {'max_position': round(new_max, 2), 'duration': dur, 'percent': percent}
        presence.video_progress = progress

        # «میزان حضور» = میانگین درصدِ ویدیوهای دیده‌شده
        percents = [v.get('percent', 0) for v in progress.values() if v.get('percent') is not None]
        if percents:
            presence.classroom_presence_percentage = round(sum(percents) / len(percents), 2)

        presence.save(update_fields=['video_progress', 'classroom_presence_percentage'])
        return Response({
            'content_index': content_index,
            'max_position': round(new_max, 2),
            'percent': percent,
            'overall_percent': float(presence.classroom_presence_percentage),
        }, status=status.HTTP_200_OK)
