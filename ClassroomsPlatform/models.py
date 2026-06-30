from django.db import models
from django.contrib.auth.models import User,Group
from django.utils import timezone
from uuid import uuid4

# Create your models here.
class ClassroomStatus(models.TextChoices):
    ACTIVE      = 'active', 'فعال'
    DEACTIVE    = 'deactive', 'غیرفعال'
    RUNNING     = 'running', 'در حال برگزاری'
    FINISHED    = 'finished', 'اتمام یافته'

class Classroom (models.Model) :
    ClassroomName                           = models.CharField ("نام جلسه",max_length=150, blank= True , null = True,)
    classroom_id                            = models.UUIDField("شماره شناسایی کلاس",primary_key=True,default=uuid4,help_text="شماره شناسایی کلاس به طور خودکار ساخته میشود و باید بی همتا باشد،لطفا تغییر ندهید")
    classroom_headline                      = models.CharField ("موضوع جلسه",max_length=150, blank= True , null = True,)
    classroom_creation_time                 = models.DateTimeField(auto_now_add=True,db_index=True)
    classroom_available_time_start          = models.DateTimeField("زمان انتشار کلاس",default= timezone.now)
    classroom_available_time_end            = models.DateTimeField("زمان پایان دسترسی ",default= timezone.now)
    classroom_presence                      = models.BooleanField ("انجام حضور و غیاب",default=False)
    classroom_status                        = models.CharField("وضعیت برگزاری کلاس",max_length=20,choices=ClassroomStatus.choices,default=ClassroomStatus.ACTIVE,db_index=True)
    classroom_groups                        = models.ManyToManyField(Group)
    content1_url1                            = models.CharField ('کیفیت اول',max_length=250, blank= True , null = True)
    content1_url2                            = models.CharField ('کیفیت دوم',max_length=250, blank= True , null = True)
    content2_url1                            = models.CharField ('کیفیت اول',max_length=250, blank= True , null = True)
    content2_url2                            = models.CharField ('کیفیت دوم',max_length=250, blank= True , null = True)
    content3_url1                            = models.CharField ('کیفیت اول',max_length=250, blank= True , null = True)
    content3_url2                            = models.CharField ('کیفیت دوم',max_length=250, blank= True , null = True)
    content4_url1                            = models.CharField ('کیفیت اول',max_length=250, blank= True , null = True)
    content4_url2                            = models.CharField ('کیفیت دوم',max_length=250, blank= True , null = True)
    content5_url1                            = models.CharField ('کیفیت اول',max_length=250, blank= True , null = True)
    content5_url2                            = models.CharField ('کیفیت دوم',max_length=250, blank= True , null = True)
    
    def is_running(self):
        now = timezone.now()
        new_status = self.classroom_status  # وضعیت فعلی        
        if self.classroom_available_time_start <= now <= self.classroom_available_time_end and self.classroom_status in [ClassroomStatus.ACTIVE, ClassroomStatus.RUNNING]:
            if self.classroom_status != ClassroomStatus.RUNNING:
                new_status = ClassroomStatus.RUNNING
            result = True       
        else:
            if now < self.classroom_available_time_start:
                # هنوز شروع نشده → ACTIVE
                if self.classroom_status != ClassroomStatus.ACTIVE:
                    new_status = ClassroomStatus.ACTIVE
                result = False            
            elif now > self.classroom_available_time_end:
                # زمان پایان رسیده → پایان کلاس
                self.finish_classroom()
                return False
        # اگر وضعیت جدید با وضعیت فعلی فرق دارد → ذخیره کن
        if new_status != self.classroom_status:
            self.classroom_status = new_status
            self.save(update_fields=['classroom_status'])
        return result

            
    def finish_classroom(self):
        now = timezone.now()
        # فقط وقتی زمان پایان گذشته و وضعیت هنوز FINISHED نیست
        if now > self.classroom_available_time_end and self.classroom_status != ClassroomStatus.FINISHED:
            self.classroom_status = ClassroomStatus.FINISHED
            # آپدیت وضعیت حضور برای دانش‌آموزان گروه‌های مرتبط
            presence_records = self.classroompresence_set.select_related('classroom_average_reffer').all()
            for presence in presence_records:
                if not presence.classroom_finished:
                    presence.classroom_finished = True
                    presence.save(update_fields=['classroom_finished'])
                # presence.make_present()  # فرض: این متد حضور را ثبت می‌کند
            # ذخیره فقط تغییرات لازم
            self.save(update_fields=['classroom_status',])

    def create_classroom_presence(self):
        classroom_presences = []
        for group in self.classroom_groups.all():
            for student in group.user_set.all():
                student_classroomaverage = student.classroomaverage
                if not self.classroompresence_set.filter(classroom_average_reffer=student_classroomaverage).exists():
                    # Create a list for classroom_presence
                    classroom_presence_list = [0 if self.content1_url1 else None,
                                               0 if self.content2_url1 else None,
                                               0 if self.content3_url1 else None,
                                               0 if self.content4_url1 else None,
                                               0 if self.content5_url1 else None]
                    classroom_presences.append(ClassroomPresence(classroom_average_reffer=student_classroomaverage, classroom=self, classroom_presence=classroom_presence_list))
        ClassroomPresence.objects.bulk_create(classroom_presences)

    def update_classroom_presence(self):
        classroom_presences = []
        classroom_presences_update = []
        for group in self.classroom_groups.all():
            for student in group.user_set.all():
                student_classroomaverage = student.classroomaverage
                if not self.classroompresence_set.filter(classroom_average_reffer=student_classroomaverage).exists():
                    # Create a list for classroom_presence
                    classroom_presence_list = [0 if self.content1_url1 else None,
                                               0 if self.content2_url1 else None,
                                               0 if self.content3_url1 else None,
                                               0 if self.content4_url1 else None,
                                               0 if self.content5_url1 else None]
                    classroom_presences.append(ClassroomPresence(classroom_average_reffer=student_classroomaverage, classroom=self, classroom_presence=classroom_presence_list))
                else:
                    a=self.classroompresence_set.get(classroom_average_reffer=student_classroomaverage)
                    temp_list = a.classroom_presence
                    if not isinstance(temp_list, list):
                        temp_list = [None, None, None, None, None]  # default value
                    temp_list2 = [
                        0 if self.content1_url1 and temp_list[0] is None else (None if not self.content1_url1 else temp_list[0]),
                        0 if self.content2_url1 and temp_list[1] is None else (None if not self.content2_url1 else temp_list[1]),
                        0 if self.content3_url1 and temp_list[2] is None else (None if not self.content3_url1 else temp_list[2]),
                        0 if self.content4_url1 and temp_list[3] is None else (None if not self.content4_url1 else temp_list[3]),
                        0 if self.content5_url1 and temp_list[4] is None else (None if not self.content5_url1 else temp_list[4]),
                    ]
                    numeric_data = [x for x in temp_list2 if isinstance(x, (int, float))]
                    if len(numeric_data) > 0:
                        a.classroom_presence_percentage = sum(numeric_data) / len(numeric_data)
                    a.classroom_presence=temp_list2
                    classroom_presences_update.append(a)
        ClassroomPresence.objects.bulk_create(classroom_presences)
        ClassroomPresence.objects.bulk_update(classroom_presences_update, ['classroom_presence','classroom_presence_percentage'])

    def __str__(self):
        # بدون عارضه‌ی جانبی؛ create_classroom_presence در ویوها صدا زده می‌شود
        return "  %s %s  " % (self.ClassroomName,self.classroom_headline,)


class ClassroomAverage (models.Model) :
    user            = models.OneToOneField(User ,verbose_name="دانش آموز",on_delete=models.CASCADE,)
    absence_count   = models.IntegerField("تعداد غیبت",default=0)

    def get_absence(self):
        self.absence_count=self.classroompresence_set.all().filter(classroom_presence=False,classroom_finished=True).count()
        self.save()
        return self.absence_count      

    def __str__(self) :
        # از مقدار ذخیره‌شده استفاده می‌کنیم؛ get_absence() در __str__ باعث محاسبه و save می‌شد
        return "  %s %s    ,تعداد غیبت: %s" % (self.user.first_name,self.user.last_name,self.absence_count)


class ClassroomPresence (models.Model) :
    classroom                       = models.ForeignKey(Classroom ,verbose_name="کلاس",on_delete=models.CASCADE)
    classroom_average_reffer        = models.ForeignKey(ClassroomAverage,verbose_name="دانش آموز",on_delete=models.CASCADE,)
    # classroom_presence              = models.BooleanField("وضعیت حضور",default=False)
    classroom_finished              = models.BooleanField("پایان کلاس دانش آموز",default=False)
    classroom_permission            = models.BooleanField("مجوز برتر",default=True)
    classroom_presence_percentage   = models.DecimalField("میزان حضور در جلسه ",default=0,max_digits=5, decimal_places=2)
    classroom_presence              = models.JSONField("وضعیت حضور",default=dict)
    # تا کجای هر ویدیو دیده شده: {"1": {"max_position": ثانیه, "duration": ثانیه, "percent": ...}, ...}
    video_progress                  = models.JSONField("پیشرفت تماشای ویدیو",default=dict,blank=True)
    # پیشرفت تماشای هر ویدیو: {"1": {"max_position": ثانیه, "duration": ثانیه, "percent": درصد}, ...}
    video_progress                  = models.JSONField("پیشرفت ویدیوها",default=dict,blank=True)
    
    
    # def make_present(self):
    #     if self.classroom.classroom_presence :    
    #         if self.classroom_presence_percentage > 80 and self.classroom.classroom_finished :
    #             self.classroom_presence=True
    #             self.save()
    #         elif self.classroom.classroom_finished:
    #             self.classroom_average_reffer.get_absence()  
    #     else:
    #         self.classroom_presence=True
    #         self.save()
    
    
    ####The below section will cause high server cpu cosumption
    def get_presence(self):
        self.classroom_average_reffer.get_absence()
        