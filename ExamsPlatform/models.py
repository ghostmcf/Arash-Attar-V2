from django.db import models
from uuid import uuid1,UUID
from datetime import datetime,timedelta
from django.contrib.auth.models import User,Group
from django.utils import timezone
from time import gmtime , strftime
from os import path
import os
from fpdf import FPDF
from PIL import Image
from Frontend.function import path_and_rename
from django.core.files import File
from django.conf import settings
# from django.db.models import Sum, Count, Case, When
# Create your models here.


class Question (models.Model) :
    question_id             = models.UUIDField("شماره شناسایی آزمون",primary_key=True,default=uuid1,help_text="شماره شناسایی سوال به طور خودکار ساخته میشود و باید بی همتا باشد،لطفا تغییر ندهید")
    question_headline       = models.CharField("تیتر سوال",max_length=50,help_text="قسمتی از سوال از جهت شناسایی آن توسط کاربر، توجه داشته باشید که تیتر سوال در امتحان نمایش داده نمیشود و صرفا حهت سهولت در پنل مدیریت است")
    question_category       = models.CharField("موضوع سوال",max_length=50,help_text="قسمتی از سوال از جهت شناسایی آن توسط کاربر، توجه داشته باشید که تیتر سوال در امتحان نمایش داده نمیشود و صرفا حهت سهولت در پنل مدیریت است")
    question_creation_time  = models.DateTimeField("زمان ساخت سوال",auto_now_add=True)
    question_answer_img     = models.ImageField("تصویر جواب سوال",upload_to=path_and_rename("aqimg"),max_length=500, blank=True ,null=True,help_text="در صورت نیاز")
    question_img            = models.ImageField("تصویر سوال",upload_to=path_and_rename("qimg"),max_length=500, blank=True ,null=True,help_text="در صورت نیاز")
    question_answer         = models.IntegerField("پاسخ سوال",default=False)
    question_time           = models.IntegerField("زمان مجاز سوال",default=120,help_text="واحد ثانیه")
    question_book           = models.CharField("کتاب سوال",max_length=50, blank=True ,null=True)
    question_grade          = models.CharField("مقطع سوال",max_length=50, blank=True ,null=True)


    def resize_img(self):
            # saving image first
            # if path.exists(self.question_img.path):
            try:
                super().save()
                path.exists(self.question_img.path)
                img = Image.open(self.question_img.path) # Open image using self
            except:
                self.question_img=''
                self.save()
            else:
                if img.height != 200 or img.width != 400:
                    new_img = (400, 200)
                    img=img.resize(new_img)
                    # print(self.avatar.path)
                    # remove(self.avatar.path)
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    img.save(self.question_img.path, "JPEG", quality=90)        
        
    def __str__(self) -> str:
        self.resize_img()
        return "%s   ,Question Answer: %s  ,Question Creation Date: %s " % (self.question_headline ,self.question_answer ,datetime.now().strftime("%c") ) 



class Exam (models.Model) :
    exam_group                  = models.ForeignKey(Group,verbose_name="گروه",on_delete=models.CASCADE,blank=True ,null=True)
    questions                   = models.ManyToManyField(Question,verbose_name="آزمون")
    ExamName                    = models.CharField("نام آزمون",max_length=100 , blank=True ,null=True)
    exam_headline               = models.CharField("موضوع آزمون",max_length=100 , blank=True ,null=True)
    exam_id                     = models.UUIDField("شماره شناسایی آزمون",primary_key=True,default=uuid1,help_text="شماره شناسایی آزمون به طور خودکار ساخته میشود و باید بی همتا باشد،لطفا تغییر ندهید")    
    exam_description            = models.FileField("فایل آزمون",upload_to=path_and_rename("eimg"),max_length=500, blank=True ,null=True)
    exam_answer_file            = models.FileField("فایل پاسخنامه آزمون",upload_to=path_and_rename("aimg"),default="useravatar/default-user.jpg",max_length=500, blank=True ,null=True)
    exam_creation_time          = models.DateTimeField("زمان ساخت آزمون",default= datetime.now())
    exam_available_time_start   = models.DateTimeField("زمان شروع آزمون",default= datetime.now())
    exam_available_time_end     = models.DateTimeField("زمان پایان آزمون",default= datetime.now() + timedelta(minutes=20))
    exam_duration               = models.TimeField("مدت زمان آزمون",blank=True , null= True)
    exam_maxenterance_time      = models.DateTimeField("زمان ورود مجاز آزمون",blank=True , null= True)
    ###########
    exam_permission             = models.BooleanField("مجوز آزمون",default=True)
    exam_running                = models.BooleanField("آزمون در حال برگزاری",default=False)
    exam_finished               = models.BooleanField("وضعیت  اتمام آزمون",default=False)
    student_returns             = models.IntegerField("تعداد بازگشت",default=2)
    exam_extra_score            = models.IntegerField("نمره اضافه",default=0)
    

  
    def merge_question_answer_images(self):
        newDir = os.path.join(self.exam_group.name, self.exam_headline)
        new_pdf_subdir = os.path.join(settings.MEDIA_ROOT, newDir)
        if not os.path.exists(new_pdf_subdir):
            os.makedirs(new_pdf_subdir)

        pdf = FPDF()
        questions = self.questions.all()
        for question in questions:
            pdf.add_page()
            question_img = Image.open(question.question_img.path).convert('RGB')
            question_answer_img = Image.open(question.question_answer_img.path).convert('RGB')

            question_img_path = os.path.join(new_pdf_subdir, f'{question.question_id}_img.jpg')
            question_answer_img_path = os.path.join(new_pdf_subdir, f'{question.question_id}_answer_img.jpg')

            question_img.save(question_img_path)
            question_answer_img.save(question_answer_img_path)

            pdf.image(question_img_path, x=10, y=8, w=100)
            pdf.image(question_answer_img_path, x=10, y=148, w=100)

        new_pdf_path = os.path.join(new_pdf_subdir, self.ExamName + ".pdf")
        pdf.output(new_pdf_path, 'F')

        with open(new_pdf_path, 'rb') as f:
            self.exam_answer_file.save(self.ExamName + '.pdf', File(f))
        self.save()

            
    def set_exam_time(self):
        a=self.questions.all()
        b=0
        for q in a :
            b += q.question_time
        self.exam_duration= strftime("%H:%M:%S", gmtime(b))
        if self.exam_maxenterance_time :
            self.exam_maxenterance_time = self.exam_available_time_start + timedelta(minutes=10)
            self.exam_available_time_end = self.exam_available_time_start + timedelta(seconds=b)
        self.save()
        return self.exam_duration
        
        
    def is_running(self):
        if self.exam_available_time_end >= timezone.now() >= self.exam_available_time_start and self.exam_permission:    
            if not self.exam_running:
                self.exam_running=True
                self.save()
            return True
        else:
            if self.exam_running:
                self.exam_running=False
                self.save()
            return False
            
    
    
    def finish_exam(self):
        if self.exam_available_time_end < timezone.now() and not self.exam_finished:
            self.exam_finished = True
            self.exam_permission = False
            self.save()
            student_ids = self.exam_group.user_set.values_list('id', flat=True)
            self.examscore_set.filter(exam_average_reffer__user__in=student_ids).update(exam_finished=True)
            for score in self.examscore_set.filter(exam_average_reffer__user__in=student_ids, exam_permission=False):
            # for score in self.examscore_set.filter(exam_average_reffer__user__in=student_ids):
                score.get_score()
            print("Exam Ended")



    def create_exam_score(self):
        for student in self.exam_group.user_set.all() :                
            student_examaverage=student.examaverage
            if(self.examscore_set.filter(exam_average_reffer = student_examaverage.id).exists()):    
                # print(str(student.username) + " Has ExamScore")
                # print(f"\n")
                pass
            else:
                a=ExamScore(exam_average_reffer=student_examaverage,exam=self,exam_peresence=False,returns_count=self.student_returns,)
                a.save() 
                # print(str(student.username) + " ExamScore Created")
                # print(f"\n")
        
    def update_exam_score(self):
        if self.exam_finished:
            for student in self.exam_group.user_set.all() :   
                try:
                    self.examscore_set.get(exam_average_reffer__user = student.id).get_score() 
                except:
                    pass
                else:
                    pass

    def __str__(self) -> str:
        # self.create_exam_score()
        # self.update_exam_score()
        self.set_exam_time()
        # self.finish_exam()
        return "%s     Start:%s" % (self.ExamName, self.exam_available_time_start.strftime("%c"))
            

# should be created on user registration
class ExamAverage (models.Model) :
    user                = models.OneToOneField(User ,verbose_name="دانش آموز",on_delete=models.CASCADE,)
    average             = models.DecimalField("میانگین امتحانات",default=0,max_digits=5, decimal_places=2)
    exam_count          = models.IntegerField("تعداد امتحانات",default=0)
    exam_abscent_count  = models.IntegerField("تعداد غیبت",default=0)
    def get_average(self):
        scoreset = self.examscore_set.filter(exam_finished=True)
        self.exam_count=scoreset.count()
        exam_sum=0  
        abscent_sum=0             
        if self.exam_count :
            for exams in scoreset :
                if exams.exam_peresence :
                    exam_sum += exams.score                    
                else:
                    abscent_sum +=1
            self.exam_abscent_count=abscent_sum
            self.average = round(exam_sum/self.exam_count,2)
            self.save()
        else:
            self.average=0        
        return self.average


    def __str__(self) :
        return "  %s %s    ,میانگین: %s" % (self.user.first_name,self.user.last_name,self.get_average()) 


class ExamScore (models.Model) :
    exam                    = models.ForeignKey(Exam ,verbose_name="آزمون",on_delete=models.CASCADE)
    exam_average_reffer     = models.ForeignKey(ExamAverage,verbose_name="دانش آموز",on_delete=models.CASCADE)
    score                   = models.DecimalField("درصد آزمون",default=0,max_digits=5, decimal_places=2)
    exam_permission         = models.BooleanField("مجوز برتر آزمون",default=False)
    exam_peresence          = models.BooleanField("حضور در آزمون",default=False)
    exam_finished           = models.BooleanField("پایان آزمون",default=False)
    student_available_extra_time_end     = models.DateTimeField("زمان اضافه پایان آزمون کاربر",blank=True,null=True)
    student_extra_score     = models.IntegerField("نمره اضافه",default=0)
    connect_times           = models.IntegerField(default=0)
    active_question_number  = models.IntegerField(default=1)
    questions_list          = models.JSONField('لیست سوالات امتحان',default=dict)
    questions_answer_list   = models.JSONField('لیست پاسخنامه سوالات',default=dict)
    user_choice             = models.JSONField('لیست انتخاب کاربر',default=dict)
    last_question_time      = models.DateTimeField("زمان شروع سوال",blank=True,null=True)    
    returns_count           = models.IntegerField(default=2)
    wrong_counts            = models.IntegerField(default=0)
    none_counts             = models.IntegerField(default=0)
    updated_at              = models.DateTimeField(auto_now=True,auto_now_add=False)
     
    def get_score(self):
        true_counts         =  0
        false_counts        =  0
        n_counts             =  0
        self.exam_permission    = False
        if self.exam_finished and self.exam_peresence :
            for questions in range(len(self.questions_list)):
                user_choice = self.user_choice[questions]
                question    = self.questions_list[questions]                
                if not user_choice == 0:
                    selected_question_answer  = int(Question.objects.get(pk=UUID(question)).question_answer)
                    if user_choice == selected_question_answer :
                        true_counts +=1
                    else:
                        false_counts +=1 
                elif user_choice == 0 :
                    n_counts +=1
            #######        
            self.score = round((( (true_counts*3) - false_counts ) / (len(self.questions_list)*3)) *100,2)
            self.score = self.score + self.exam.exam_extra_score + self.student_extra_score
            if self.score >= 100 :
                self.score = 100
            self.wrong_counts=false_counts
            self.none_counts =n_counts
        elif not self.exam_finished and not self.exam_peresence :
            self.score=0
        elif self.exam_finished and not self.exam_peresence:
            self.score=0
        self.save()
        self.exam_average_reffer.get_average()        
    # def get_score(self):
    #     true_counts = 0
    #     false_counts = 0
    #     n_counts = 0
    #     self.exam_finished = True
    #     self.exam_permission = False
    #     if self.exam_peresence:
    #         questions = Question.objects.in_bulk(self.questions_list)
    #         for question_id, user_choice in zip(self.questions_list, self.user_choice):
    #             if user_choice:
    #                 question = questions[UUID(question_id)]
    #                 selected_question_answer = str(question.question_answer)
    #                 if user_choice == selected_question_answer:
    #                     true_counts += 1
    #                 else:
    #                     false_counts += 1
    #             elif user_choice == "0":
    #                 n_counts += 1
    
    #         self.score = round((( (true_counts*3) - false_counts ) / (len(self.questions_list)*3)) *100,2)
    #         self.score = self.score + self.exam.exam_extra_score + self.student_extra_score
    #         if self.score >= 100 :
    #             self.score = 100
    #         self.wrong_counts=false_counts
    #         self.none_counts =n_counts
    #     elif not self.exam_peresence:
    #         self.score=0
    #     self.save()
    #     self.exam_average_reffer.get_average()   
    
    def __str__(self) :
        # self.get_score()
        return "  %s %s         , نمره:  %s ,       امتحان:  %s,   حضور در امتحان:  %s ,  مجوز برتر:  %s" % (self.exam_average_reffer.user.first_name,self.exam_average_reffer.user.last_name,self.score,self.exam.ExamName,self.exam_peresence,self.exam_permission) 
   