from django.contrib import admin
from . import models
# Register your models here.

@admin.register(models.Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('ExamName', 'exam_group', 'exam_headline', 'exam_id', 'exam_available_time_start', 'exam_permission', 'exam_finished')
    list_filter = ('exam_group', 'exam_creation_time', 'exam_permission')
    fieldsets = (
        ("مشخصات آزمون", {
            'fields': (('ExamName', 'exam_headline', 'exam_id'), ('exam_group', 'questions'), ('exam_description'), ('exam_answer_file'),)
        }),
        ('زمان آزمون', {
            'fields': ('exam_available_time_start', 'exam_available_time_end', 'exam_maxenterance_time', 'exam_duration'),
        }),
        ('تنظیمات آزمون', {
            'fields': (('exam_permission', 'exam_running', 'exam_finished'), ('student_returns', 'exam_extra_score'))
        }),
        ('پیامک', {
            'fields': (('sms_permission', 'sms_sent', 'sms_sent_at'),)
        }),
    )

@admin.register(models.Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display=('question_headline','question_category','question_grade','question_book','question_img','question_time','question_answer_img',)
    # list_filter=('exam',)



@admin.register(models.ExamScore)
class ExamScoreAdmin(admin.ModelAdmin):
    list_display = ('exam', 'exam_average_reffer', 'score', 'exam_permission', 'exam_peresence', 'exam_finished')
    list_filter = ('exam', 'exam_average_reffer', 'score', 'exam_permission', 'exam_peresence', 'exam_finished')
    fieldsets = (
        ("مشخصات نمره آزمون", {
            'fields': (('exam', 'exam_average_reffer'), ('score',),)
        }),
        ('تنظیمات نمره آزمون', {
            'fields': (('exam_permission', 'exam_peresence', 'exam_finished'), ('student_available_extra_time_end', 'student_extra_score'), ('connect_times', 'active_question_number', 'max_question_number'), ('questions_list', 'questions_answer_list','user_choice',), ('active_deadline', 'frontier_remaining'), ('returns_count',), ('wrong_counts','none_counts',),)
        })
    )


@admin.register(models.ExamAverage)
class ExamAverageAdmin(admin.ModelAdmin):
    list_display=('user','average') 
    list_filter=('user',)
