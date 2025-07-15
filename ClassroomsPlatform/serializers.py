from rest_framework import serializers

from ClassroomsPlatform.models import Classroom,ClassroomPresence,ClassroomAverage


# class ClassSerializer (serializers.ModelSerializer):
#     content_set = serializers.SerializerMethodField()
#     class Meta:
#         model = Classroom
#         fields = "__all__"
#     def get_content_set(self, instance):
#         contents = instance.content_set.all().order_by('content_order')
#         return ContentSerializer(contents, many=True).data
    

class ClassSerializer (serializers.ModelSerializer):
    class Meta:
        model = Classroom
        fields = "__all__"

class ClassPresenceSerializer (serializers.ModelSerializer):
    class Meta:
        model = ClassroomPresence
        fields = "__all__"
        
class ClassAverageSerializer (serializers.ModelSerializer):
    class Meta:
        model = ClassroomAverage
        fields = ['absence_count']   
        
class ClassPercentSerializer (serializers.ModelSerializer):
    class Meta:
        model = ClassroomPresence
        fields = ['classroom_presence']
  
        
        
class ClassroomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Classroom
        fields = "__all__"
        # fields = ['classroom_id', 'ClassroomName', 'classroom_headline']

class ClassroomHeadlineSerializer(serializers.Serializer):
    classroom_headline = serializers.CharField()
    count = serializers.IntegerField()    