from rest_framework import serializers
from . import models


class ExamAverageSerializer (serializers.ModelSerializer):
    class Meta:
        model = models.ExamAverage
        fields = "__all__"


class ExamScoreSerializer (serializers.ModelSerializer):
    class Meta:
        model = models.ExamScore
        fields = ("id","exam_finished","exam_peresence","student_available_extra_time_end","active_question_number","questions_list","user_choice","last_question_time","returns_count","exam","exam_average_reffer","none_counts","wrong_counts")
        
        
# class TheScoreSerializer (serializers.ModelSerializer):
#     class Meta:
#         model = models.ExamScore
#         fields = ("score",)
                
        


class ExamSerializer (serializers.ModelSerializer):
    class Meta:
        model = models.Exam
        fields = ('exam_id','ExamName','exam_headline','exam_description','exam_available_time_start','exam_available_time_end','exam_duration','exam_maxenterance_time','exam_group')

