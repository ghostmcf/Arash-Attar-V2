from django.contrib import admin
from . import models
# Register your models here.



@admin.register(models.Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('AssignmentName', 'assignment_group', 'assignment_headline', 'assignment_id', 'assignment_available_time_start', 'assignment_finished')
    list_filter = ('assignment_group', 'assignment_creation_time',)
    fieldsets = (
        ("مشخصات تکلیف", {
            'fields': (('AssignmentName', 'assignment_headline', 'assignment_id'), ('assignment_group',), ('assignment_description'), ('assignment_file', 'assignment_answer_file'),)
        }),
        ('زمان تکلیف', {
            'fields': ('assignment_available_time_start', 'assignment_available_time_end'),
        }),
        ('تنظیمات تکلیف', {
            'fields': (('assignment_finished'), ('assignment_extra_score',))
        })
    )


@admin.register(models.AssignmentScore)
class AssignmentScoreAdmin(admin.ModelAdmin):
    list_display = ('assignment','updated_file_at', 'assignment_average_reffer', 'score', 'assignment_permission', 'assignment_presence', 'assignment_finished')
    list_filter = ('assignment', 'assignment_average_reffer', 'score', 'assignment_permission', 'assignment_presence', 'assignment_finished')
    fieldsets = (
        ("مشخصات نمره تکلیف", {
            'fields': (('assignment', 'assignment_average_reffer'), ('score',), ('assignment_student_file', 'assignment_teacher_file'))
        }),
        ('تنظیمات نمره تکلیف', {
            'fields': (('assignment_permission', 'assignment_presence', 'assignment_finished'), ('assignment_marked','assignment_marked_by'), ('extra_score',), ('q1_score', 'q2_score', 'q3_score'), ('q4_score', 'q5_score', 'q6_score'), ('q7_score', 'q8_score', 'q9_score'), ('q10_score', 'q11_score', 'q12_score'), ('q13_score', 'q14_score', 'q15_score'), ('q16_score', 'q17_score', 'q18_score'), ('q19_score', 'q20_score'))
        })
    )


@admin.register(models.AssignmentAverage)
class AssignmentAverageAdmin(admin.ModelAdmin):
    list_display=('user','average') 
    list_filter=('user',) 

