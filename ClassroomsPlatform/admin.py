from django.contrib import admin
from . import models
# Register your models here.



@admin.register(models.ClassroomAverage)
class ClassroomAverageAdmin(admin.ModelAdmin):
    list_display=('user','absence_count') 
    list_filter=('user','absence_count')
    fieldsets = (
        ("مشخصات دانش آموز" , {
            'fields': ('user','absence_count') ,
        }),     
    )

@admin.register(models.ClassroomPresence)
class ClassroomPresenceAdmin(admin.ModelAdmin):
    list_display=('classroom_average_reffer','classroom','classroom_presence','classroom_presence_percentage') 
    list_filter=('classroom_average_reffer','classroom','classroom_presence')
    search_fields = ('classroom_average_reffer__name', 'classroom__ClassroomName')
    fieldsets = (
        ("مشخصات حضور در جلسه" , {
            'fields': ('classroom_average_reffer','classroom',),
        }),
        ('تنظیمات' , {
            'fields': ('classroom_presence_percentage','classroom_presence','classroom_finished','classroom_permission',),
        }),        
    )

@admin.register(models.Classroom)
class ClassroomAdmin (admin.ModelAdmin):
    list_display = ('ClassroomName','classroom_creation_time','classroom_presence')
    list_filter = ('ClassroomName', 'classroom_creation_time', 'classroom_presence')
    search_fields = ('ClassroomName', 'classroom_headline')
    fieldsets = (
        ("مشخصات کلاس" , {
            'fields': (('ClassroomName','classroom_headline') ,('classroom_groups',))
        }),
        ('زمانبندی' , {
            'fields': ('classroom_available_time_start','classroom_available_time_end'),
        }), 
        ('تنظیمات کلاس' , {
            'fields': (('classroom_presence','classroom_status',),('classroom_creation_completion',)),
        }),       
    )

