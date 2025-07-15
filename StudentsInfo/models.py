from django.db import models
from django.contrib.auth.models import User, Group
from ExamsPlatform import models as E_models
from AssignmentPlatform import models as A_models
from ClassroomsPlatform import models as C_models
from os import path
from PIL import Image
from Frontend.function import path_and_rename
from django.db.models import Q



class StudentUser (models.Model) :
    student_user = models.OneToOneField(User , on_delete= models.CASCADE,null=True)
    # birth_date = models.DateField("تاریخ تولد",blank=True,null=True)
    father_name= models.CharField("نام پدر",blank=True,null=True,max_length=35)
    phone_number = models.CharField("شماره همراه",blank=True,null=True,max_length=12)
    father_number = models.CharField("شماره پدر",blank=True,null=True,max_length=12)
    mother_number = models.CharField("شماره مادر",blank=True,null=True,max_length=12)
    home_number = models.CharField("شماره ثابت",blank=True,null=True,max_length=12)
    address     =   models.CharField( "آدرس",blank=True,null=True,max_length=200)
    registration_date = models.DateField("تاریخ ثبت نام",blank=True,null=True)
    avatar              = models.ImageField("عکس پرسنلی",upload_to=path_and_rename('useravatar/'),default="useravatar/default-user.jpg")
    # scoresheet          = models.ImageField("عکس کارنامه",upload_to=path_and_rename('userscoresheet/'),null=True , blank=True)
    student_school      = models.CharField("مدرسه",max_length= 20  ,null=True , blank=True)
    average_exam        = models.IntegerField( "میانگین درصد آزمون",editable=False,default=0)
    average_assignment  = models.IntegerField( "میانگین درصد تکالیف",editable=False,default=0)
    abscent_count       = models.IntegerField( "تعداد غیبت",editable=False,default=0)
    #####
    student_type                   = models.CharField("رشته",max_length=25,null=True,blank=True)
    student_gender                 = models.CharField("جنسیت",max_length=15, choices=(
        ('پسر','پسر'),
        ('دختر','دختر')
    ) ,null=True,blank=True)
    student_grade                  = models.CharField("پایه",max_length=15, choices=(
        ('دهم','دهم'),
        ('یازدهم','یازدهم'),
        ('دوازدهم','دوازدهم')
    ) ,null=True,blank=True)
    ########
    student_status                 = models.CharField("وضعیت تحصیل",max_length=15, choices=(
        ('در حال تحصیل','در حال تحصیل'),
        ('انصراف','انصراف'),
        ('فارغ التحصیل','فارغ التحصیل'),
    ) ,null=True,blank=True)
    student_study_date                  = models.CharField("تاریخ تحصیل",max_length=60,null=True,blank=True)
    student_description                 = models.CharField("توضیحات",max_length= 300  ,null=True , blank=True)
    
    
    def student_group_info (self):
        if self.student_user.groups.all().count():
            self.student_gender = self.student_user.groups.all()[0].group_gender
            self.student_grade   = self.student_user.groups.all()[0].group_grade
            self.save()

    

    def create_averages(self):
        exam_average, created = E_models.ExamAverage.objects.get_or_create(user=self.student_user)
        assignment_average, created = A_models.AssignmentAverage.objects.get_or_create(user=self.student_user)
        classroom_average, created = C_models.ClassroomAverage.objects.get_or_create(user=self.student_user)
    
        exams = E_models.Exam.objects.filter(exam_group__in=self.student_user.groups.all(), exam_finished=False)
        existing_exam_scores = set(E_models.ExamScore.objects.filter(Q(exam__in=exams) & Q(exam_average_reffer=exam_average)).values_list('exam_id', flat=True))
        new_exam_scores = [E_models.ExamScore(exam=exam, exam_average_reffer=exam_average) for exam in exams if exam.exam_id not in existing_exam_scores]
        E_models.ExamScore.objects.bulk_create(new_exam_scores)
    
        assignments = A_models.Assignment.objects.filter(assignment_group__in=self.student_user.groups.all(), assignment_finished=False)
        existing_assignment_scores = set(A_models.AssignmentScore.objects.filter(Q(assignment__in=assignments) & Q(assignment_average_reffer=assignment_average)).values_list('assignment_id', flat=True))
        new_assignment_scores = [A_models.AssignmentScore(assignment=assignment, assignment_average_reffer=assignment_average) for assignment in assignments if assignment.assignment_id not in existing_assignment_scores]
        A_models.AssignmentScore.objects.bulk_create(new_assignment_scores)
    
        classrooms = C_models.Classroom.objects.filter(classroom_groups__in=self.student_user.groups.all(), classroom_finished=False)
        existing_classroom_presences = set(C_models.ClassroomPresence.objects.filter(Q(classroom__in=classrooms) & Q(classroom_average_reffer=classroom_average)).values_list('classroom_id', flat=True))
        new_classroom_presences = [C_models.ClassroomPresence(classroom=classroom, classroom_average_reffer=classroom_average) for classroom in classrooms if classroom.classroom_id not in existing_classroom_presences]
        C_models.ClassroomPresence.objects.bulk_create(new_classroom_presences)
        print(str(self.student_user)+"create average")
    
    def resize_img(self):
        super().save()  # saving image first
        if path.exists(self.avatar.path):
            img = Image.open(self.avatar.path) # Open image using self
            if img.height != 400 or img.width != 300:
                new_img = (400, 300)
                img=img.resize(new_img)
                # print(self.avatar.path)
                # remove(self.avatar.path)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                img.save(self.avatar.path, "JPEG", quality=80)
        # if path.exists(self.scoresheet.path):
        #     scsheet=Image.open(self.scoresheet.path)
        #     if scsheet.height != 800 or scsheet.width != 600:
        #         new_scsheet = (800, 600)
        #         scsheet=scsheet.resize(new_scsheet)
        #         scsheet.save(self.scoresheet.path, "JPEG", quality=80)
        try:
            path.exists(self.scoresheet.path)
        except:
            pass
        else:    
            scsheet=Image.open(self.scoresheet.path)
            if scsheet.height != 800 or scsheet.width != 600:
                new_scsheet = (800, 600)
                scsheet=scsheet.resize(new_scsheet)
                if scsheet.mode != 'RGB':
                    scsheet = scsheet.convert('RGB')
                scsheet.save(self.scoresheet.path, "JPEG", quality=80)
        
    def __str__(self) -> str:
        self.student_group_info()
        self.resize_img()
        return "%s    " % (self.create_averages()) 

class SignedCheck (models.Model) :
    student = models.ForeignKey(User,on_delete= models.CASCADE)
    amout = models.CharField("مبلغ",max_length=50)
    check_date  = models.DateField("تاریخ چک",blank=True,null=True)
    check_number    = models.CharField("شماره چک",max_length=50,blank=True,null=True)
    bank    = models.CharField("بانک صیادی",max_length=30,blank=True,null=True)
    description   = models.CharField("بانک صیادی",max_length=250,blank=True,null=True)
    
class DirectMoney (models.Model) :
    student = models.ForeignKey(User,on_delete= models.CASCADE)
    amout = models.CharField("مبلغ",max_length=50)
    payment_date  = models.DateField("تاریخ پرداخت",blank=True,null=True)
    refrence_number    = models.CharField("شماره رهگیری",max_length=50,blank=True,null=True)
    following_number = models.CharField("شماره پیگیری",max_length=200,blank=True,null=True)
    card_number = models.CharField("چهار رقم آخر کارت",max_length=50,blank=True,null=True)
    payment_method    = models.CharField("شیوه انتقال",max_length=30,blank=True,null=True)
    bank    = models.CharField("بانک صیادی",max_length=30,blank=True,null=True)
    description   = models.CharField("بانک صیادی",max_length=250,blank=True,null=True)
 
class Books (models.Model) :
    student = models.ManyToManyField(User, verbose_name="جزوه", blank=True)
    booksname    = models.CharField("نام جزوه",max_length=50,blank=True,null=True)

Group.add_to_class('group_time', models.CharField("ساعت کلاس",max_length= 30
     ,null=True , blank=True))

Group.add_to_class('group_day', models.CharField("روز کلاس",max_length= 20 , choices=(
        # ('5','شنبه'),
        # ('6','یکشنبه'),
        # ('0','دوشنبه'),
        # ('1','سه شنبه'),
        # ('2','چهارشنبه'),
        # ('3','پنج شنبه'),
        # ('4','جمعه'),
        ('شنبه','شنبه'),
        ('یکشنبه','یکشنبه'),
        ('دوشنبه','دوشنبه'),
        ('ه شنبه','سه شنبه'),
        ('چهارشنبه','چهارشنبه'),
        ('ج شنبه','پنج شنبه'),
        ('جمعه','جمعه'),
    ) ,null=True , blank=True))     

Group.add_to_class('group_gender', models.CharField("جنسیت",max_length= 5 , choices=(
        ('پسر','پسر'),
        ('دختر','دختر')
    ) ,null=True , blank=True))

Group.add_to_class('group_grade', models.CharField("مقطع",max_length= 8 , choices=(
        ('دهم','دهم'),
        ('یازدهم','یازدهم'),
        ('دوازدهم','دوازدهم')
    ) ,null=True , blank=True))
Group.add_to_class('group_cost', models.IntegerField("مبلغ کلاس" ,null=True , blank=True))

