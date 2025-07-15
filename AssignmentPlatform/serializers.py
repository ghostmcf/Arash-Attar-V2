from rest_framework import serializers

from AssignmentPlatform.models import Assignment,AssignmentScore,AssignmentAverage


class AssignmentSerializer (serializers.ModelSerializer):
    class Meta:
        model = Assignment
        fields = "__all__"

class AssignmentScoreSerializer (serializers.ModelSerializer):
    class Meta:
        model = AssignmentScore
        fields = "__all__"

class AssignmentAverageSerializer (serializers.ModelSerializer):
    class Meta:
        model = AssignmentAverage
        fields = "__all__"


class AssignmentScoreUploadSerializer (serializers.ModelSerializer):
    class Meta:
        model = AssignmentScore
        fields = ['assignment_student_file']
        read_only_fields = ["updated_file_at"]
    
    # def create(self, validated_data):
    #     obj=super().create(validated_data)
    #     obj.updated_file_at = timezone.now()
    #     obj.save()
    #     return obj
