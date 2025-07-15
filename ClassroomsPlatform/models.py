from django.db import models
from datetime import datetime
from django.contrib.auth.models import User,Group
from django.utils import timezone
from uuid import uuid1

# Create your models here.
class Classroom (models.Model) :
    ClassroomName                           = models.CharField ("نام جلسه",max_length=150, blank= True , null = True,)
    classroom_id                            = models.UUIDField("شماره شناسایی کلاس",primary_key=True,default=uuid1,help_text="شماره شناسایی کلاس به طور خودکار ساخته میشود و باید بی همتا باشد،لطفا تغییر ندهید")
    classroom_headline                      = models.CharField ("موضوع جلسه",max_length=150, blank= True , null = True,)
    classroom_creation_time                 = models.DateTimeField(auto_now_add=True)
    classroom_available_time_start          = models.DateTimeField("زمان انتشار کلاس",default= datetime.now())
    classroom_available_time_end            = models.DateTimeField("زمان پایان دسترسی ",default= datetime.now())
    classroom_presence                      = models.BooleanField ("انجام حضور و غیاب",default=False)
    classroom_permission                    = models.BooleanField ("برگزاری کلاس",default=True)
    classroom_running                       = models.BooleanField ("کلاس در حال برگزاری",default=False)
    classroom_finished                      = models.BooleanField ("پایان کلاس",default=False)
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
        if self.classroom_available_time_end >= timezone.now() >= self.classroom_available_time_start and self.classroom_permission:    
            if not self.classroom_running:
                self.classroom_running=True
                self.save()
            return True
        else:
            if self.classroom_running:
                self.classroom_running=False
                self.save()
            return False

    def finish_classroom(self):
        if self.classroom_available_time_end < timezone.now() and self.classroom_finished == False:    
            self.classroom_finished=True
            self.classroom_permission=False            
            for groups in self.classroom_groups.all():    
                for student in groups.user_set.all() :
                    if self.classroompresence_set.filter(classroom_average_reffer = student.id).exists():
                        a=self.classroompresence_set.get(classroom_average_reffer = student.id)
                        if not a.classroom_finished :
                            a.classroom_finished=True                                    
                            a.save()                                                       
                        a.make_present()                          
            self.save()
            print("Classroom Ended")

    # def create_classroom_presence(self):
    #     for groups in self.classroom_groups.all():    
    #         for student in groups.user_set.all() :                
    #             if(self.classroompresence_set.filter(classroom_average_reffer = student.id).exists()):    
    #                 print(str(student.username) + " Has ClassroomPresence")
    #                 print(f"\n")                           
    #             else:      
    #                 try:
    #                     student_classroomaverage=student.classroomaverage
    #                 except:
    #                     student.studentuser.create_averages()
    #                     student_classroomaverage=student.classroomaverage
    #                 else:
    #                     pass 
    #                 student_classroomaverage=student.classroomaverage     
    #                 if self.classroom_presence:
    #                     a=ClassroomPresence(classroom_average_reffer=student_classroomaverage,classroom=self,classroom_presence=False,)
    #                 else:
    #                     a=ClassroomPresence(classroom_average_reffer=student_classroomaverage,classroom=self,classroom_presence=True,)
    #                 a.save()            
    #                 print(str(student.username) + " ClassroomPresence Created")
    #                 print(f"\n")
    #     self.save()
    # def create_classroom_presence(self):
    #     for group in self.classroom_groups.all():
    #         for student in group.user_set.all():
    #             student_classroomaverage = student.classroomaverage
    #             if not self.classroompresence_set.filter(classroom_average_reffer=student_classroomaverage).exists():
    #                 if self.classroom_presence:
    #                     a = ClassroomPresence(classroom_average_reffer=student_classroomaverage, classroom=self, classroom_presence=False)
    #                 else:
    #                     a = ClassroomPresence(classroom_average_reffer=student_classroomaverage, classroom=self, classroom_presence=True)
    #                 print(str(student.username) + " ClassroomPresence Created")
    #                 a.save()
    #     # self.save()
    
    
    
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
    
    ############ Version of Changing all datas
    # def update_classroom_presence(self):
    #     classroom_presences = []
    #     classroom_presences_update = []
    #     for group in self.classroom_groups.all():
    #         for student in group.user_set.all():
    #             student_classroomaverage = student.classroomaverage
    #             if not self.classroompresence_set.filter(classroom_average_reffer=student_classroomaverage).exists():
    #                 # Create a list for classroom_presence
    #                 classroom_presence_list = [0 if self.content1_url1 else None,
    #                                           0 if self.content2_url1 else None,
    #                                           0 if self.content3_url1 else None,
    #                                           0 if self.content4_url1 else None,
    #                                           0 if self.content5_url1 else None]
    #                 classroom_presences.append(ClassroomPresence(classroom_average_reffer=student_classroomaverage, classroom=self, classroom_presence=classroom_presence_list))
    #             else:
    #                 a=self.classroompresence_set.get(classroom_average_reffer=student_classroomaverage)
    #                 temp_list = [None, None, None, None, None]  # default value
    #                 if isinstance(a.classroom_presence, dict):
    #                     temp_list = [
    #                         a.classroom_presence["content1"],
    #                         a.classroom_presence["content2"],
    #                         a.classroom_presence["content3"],
    #                         a.classroom_presence["content4"],
    #                         a.classroom_presence["content5"],
    #                     ]
    #                 temp_list2=[]
    #                 temp_list2 = [
    #                     0 if self.content1_url1 and temp_list[0] is None else (None if not self.content1_url1 else temp_list[0]),
    #                     0 if self.content2_url1 and temp_list[1] is None else (None if not self.content2_url1 else temp_list[1]),
    #                     0 if self.content3_url1 and temp_list[2] is None else (None if not self.content3_url1 else temp_list[2]),
    #                     0 if self.content4_url1 and temp_list[3] is None else (None if not self.content4_url1 else temp_list[3]),
    #                     0 if self.content5_url1 and temp_list[4] is None else (None if not self.content5_url1 else temp_list[4]),
    #                 ]
    #                 a.classroom_presence=temp_list2
    #                 classroom_presences_update.append(a)
    #     ClassroomPresence.objects.bulk_create(classroom_presences)
    #     ClassroomPresence.objects.bulk_update(classroom_presences_update, ['classroom_presence'])
    #########Version in dictionary mode
    # def create_classroom_presence(self):
    #     classroom_presences = []
    #     for group in self.classroom_groups.all():
    #         for student in group.user_set.all():
    #             student_classroomaverage = student.classroomaverage
    #             if not self.classroompresence_set.filter(classroom_average_reffer=student_classroomaverage).exists():
    #                 # Create a dictionary for classroom_presence
    #                 classroom_presence_dict = {
    #                     'content1_url1': 0 if self.content1_url1 else None,
    #                     'content2_url1': 0 if self.content2_url1 else None,
    #                     'content3_url1': 0 if self.content3_url1 else None,
    #                     'content4_url1': 0 if self.content4_url1 else None,
    #                     'content5_url1': 0 if self.content5_url1 else None,
    #                 }
    #                 classroom_presences.append(ClassroomPresence(classroom_average_reffer=student_classroomaverage, classroom=self, classroom_presence=classroom_presence_dict))
    #     ClassroomPresence.objects.bulk_create(classroom_presences)

    ####Update
    # def update_classroom_presence(self):
    #     classroom_presences = []
    #     classroom_presences_update = []
    #     for group in self.classroom_groups.all():
    #         for student in group.user_set.all():
    #             student_classroomaverage = student.classroomaverage
    #             if not self.classroompresence_set.filter(classroom_average_reffer=student_classroomaverage).exists():
    #                 # Create a dictionary for classroom_presence
    #                 classroom_presence_dict = {
    #                     'content1': 0 if self.content1_url1 else None,
    #                     'content2': 0 if self.content2_url1 else None,
    #                     'content3': 0 if self.content3_url1 else None,
    #                     'content4': 0 if self.content4_url1 else None,
    #                     'content5': 0 if self.content5_url1 else None,
    #                 }
    #                 classroom_presences.append(ClassroomPresence(classroom_average_reffer=student_classroomaverage, classroom=self, classroom_presence=classroom_presence_dict))
    #             else:
    #                 a=self.classroompresence_set.get(classroom_average_reffer=student_classroomaverage)
    #                 if isinstance(a.classroom_presence, list):
    #                     temp_dict = {
    #                         'content1': a.classroom_presence[0],
    #                         'content2': a.classroom_presence[1],
    #                         'content3': a.classroom_presence[2],
    #                         'content4': a.classroom_presence[3],
    #                         'content5': a.classroom_presence[4],
    #                     }
    #                     a.classroom_presence=temp_dict
    #                 elif isinstance(a.classroom_presence, bool) or not a.classroom_presence.get('content1'):
    #                     temp_dict = {
    #                         'content1': None,
    #                         'content2': None,
    #                         'content3': None,
    #                         'content4': None,
    #                         'content5': None,
    #                     }
    #                     a.classroom_presence=temp_dict
                        
    #                 classroom_presence_dict = a.classroom_presence
    #                 classroom_presence_dict = {
    #                     'content1': 0 if self.content1_url1 and classroom_presence_dict['content1'] is None else (None if not self.content1_url1 else classroom_presence_dict['content1']),
    #                     'content2': 0 if self.content2_url1 and classroom_presence_dict['content2'] is None else (None if not self.content2_url1 else classroom_presence_dict['content2']),
    #                     'content3': 0 if self.content3_url1 and classroom_presence_dict['content3'] is None else (None if not self.content3_url1 else classroom_presence_dict['content3']),
    #                     'content4': 0 if self.content4_url1 and classroom_presence_dict['content4'] is None else (None if not self.content4_url1 else classroom_presence_dict['content4']),
    #                     'content5': 0 if self.content5_url1 and classroom_presence_dict['content5'] is None else (None if not self.content5_url1 else classroom_presence_dict['content5']),
    #                 }
    #                 a.classroom_presence=classroom_presence_dict
    #                 classroom_presences_update.append(a)
    #     ClassroomPresence.objects.bulk_create(classroom_presences)
    #     ClassroomPresence.objects.bulk_update(classroom_presences_update, ['classroom_presence'])



    ### LAST VERSION WORKING BEFOR classpresence {0,0,0,0,0}
    # def create_classroom_presence(self):
    #     classroom_presences = []
    #     for group in self.classroom_groups.all():
    #         for student in group.user_set.all():
    #             student_classroomaverage = student.classroomaverage
    #             if not self.classroompresence_set.filter(classroom_average_reffer=student_classroomaverage).exists():
    #                 classroom_presence = not self.classroom_presence
    #                 classroom_presences.append(ClassroomPresence(classroom_average_reffer=student_classroomaverage, classroom=self, classroom_presence=classroom_presence))
    #     ClassroomPresence.objects.bulk_create(classroom_presences)
    

    
    def __str__(self):
        self.create_classroom_presence()
        # self.finish_classroom() #remove later
        return "  %s %s  " % (self.ClassroomName,self.classroom_headline,) 


class ClassroomAverage (models.Model) :
    user            = models.OneToOneField(User ,verbose_name="دانش آموز",on_delete=models.CASCADE,)
    absence_count   = models.IntegerField("تعداد غیبت",default=0)

    def get_absence(self):
        self.absence_count=self.classroompresence_set.all().filter(classroom_presence=False,classroom_finished=True).count()
        self.save()
        return self.absence_count      

    def __str__(self) :
        return "  %s %s    ,تعداد غیبت: %s" % (self.user.first_name,self.user.last_name,self.get_absence()) 


class ClassroomPresence (models.Model) :
    classroom                       = models.ForeignKey(Classroom ,verbose_name="کلاس",on_delete=models.CASCADE)
    classroom_average_reffer        = models.ForeignKey(ClassroomAverage,verbose_name="دانش آموز",on_delete=models.CASCADE,)
    # classroom_presence              = models.BooleanField("وضعیت حضور",default=False)
    classroom_finished              = models.BooleanField("پایان کلاس دانش آموز",default=False)
    classroom_permission            = models.BooleanField("مجوز برتر",default=True)
    classroom_presence_percentage   = models.DecimalField("میزان حضور در جلسه ",default=0,max_digits=5, decimal_places=2)
    classroom_presence              = models.JSONField("وضعیت حضور",default=dict)
    
    
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
        
        
    # def count_content(self):
    #     c=self.classroom.content_set.all()
    #     for i in c :
    #         if not i in self.classroom_presence:
    #             self.classroom_presence.append(i)
    #     self.save()

    # def __str__(self) :
    #     # self.count_content()
    #     # self.make_present()
    #     return "  %s %s    ,      کلاس:  %s" % (self.classroom_average_reffer.user.first_name,self.classroom_average_reffer.user.last_name,self.classroom.ClassroomName) 

