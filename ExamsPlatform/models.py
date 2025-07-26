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
from django.core.files import File
from django.conf import settings
from Frontend.upload_manager import TEMP_DIR , auto_upload
# Create your models here.
import requests
from django.core.files.uploadedfile import SimpleUploadedFile



def download_file(url, local_path):
    """دانلود فایل از URL و ذخیره در مسیر local_path"""
    r = requests.get(url, stream=True)
    r.raise_for_status()
    with open(local_path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)
    return local_path

def compress_image(input_path, output_path, max_width=1200, quality=85):
    """کم کردن حجم تصویر با حفظ کیفیت نسبی"""
    img = Image.open(input_path).convert('RGB')
    if img.width > max_width:
        ratio = max_width / float(img.width)
        height = int((float(img.height) * float(ratio)))
        img = img.resize((max_width, height), Image.LANCZOS)
    img.save(output_path, 'JPEG', quality=quality)
    return output_path

class Question (models.Model) :
    question_id             = models.UUIDField("شماره شناسایی آزمون",primary_key=True,default=uuid1,help_text="شماره شناسایی سوال به طور خودکار ساخته میشود و باید بی همتا باشد،لطفا تغییر ندهید")
    question_headline       = models.CharField("تیتر سوال",max_length=50,help_text="قسمتی از سوال از جهت شناسایی آن توسط کاربر، توجه داشته باشید که تیتر سوال در امتحان نمایش داده نمیشود و صرفا حهت سهولت در پنل مدیریت است")
    question_category       = models.CharField("موضوع سوال",max_length=50,help_text="قسمتی از سوال از جهت شناسایی آن توسط کاربر، توجه داشته باشید که تیتر سوال در امتحان نمایش داده نمیشود و صرفا حهت سهولت در پنل مدیریت است")
    question_creation_time  = models.DateTimeField("زمان ساخت سوال",auto_now_add=True)
    question_answer_img     = models.CharField("تصویر جواب سوال",max_length=500, blank=True ,null=True,help_text="در صورت نیاز")
    question_img            = models.CharField("تصویر سوال",max_length=500, blank=True ,null=True,help_text="در صورت نیاز")
    question_answer         = models.IntegerField("پاسخ سوال",default=False)
    question_time           = models.IntegerField("زمان مجاز سوال",default=120,help_text="واحد ثانیه")
    question_book           = models.CharField("کتاب سوال",max_length=50, blank=True ,null=True)
    question_grade          = models.CharField("مقطع سوال",max_length=50, blank=True ,null=True)


    def resize_img(self):
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
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    img.save(self.question_img.path, "JPEG", quality=90)        
        
    def __str__(self) -> str:
        # self.resize_img()
        return "%s   ,Question Answer: %s  ,Question Creation Date: %s " % (self.question_headline ,self.question_answer ,datetime.now().strftime("%c") ) 

class Exam (models.Model) :
    exam_group                  = models.ForeignKey(Group,verbose_name="گروه",on_delete=models.CASCADE,blank=True ,null=True)
    questions                   = models.ManyToManyField(Question,verbose_name="آزمون")
    ExamName                    = models.CharField("نام آزمون",max_length=100 , blank=True ,null=True)
    exam_headline               = models.CharField("موضوع آزمون",max_length=100 , blank=True ,null=True)
    exam_id                     = models.UUIDField("شماره شناسایی آزمون",primary_key=True,default=uuid1,help_text="شماره شناسایی آزمون به طور خودکار ساخته میشود و باید بی همتا باشد،لطفا تغییر ندهید")    
    exam_description            = models.CharField("فایل آزمون",max_length=500, blank=True ,null=True)
    exam_answer_file            = models.CharField("فایل پاسخنامه آزمون",max_length=500, blank=True ,null=True)
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
    exam_note                   = models.CharField("توضیح آزمون",max_length=100 , blank=True ,null=True)
    
    def merge_question_answer_images(self):
        exam_temp_dir = os.path.join(TEMP_DIR, f"exam_{self.exam_id}".replace("-", ""))
        os.makedirs(exam_temp_dir, exist_ok=True)
        print(f"[INFO] Temporary directory created: {exam_temp_dir}")

        pdf = FPDF(unit='mm', format='A4')
        cleanup_files = []
        final_pdf_path = None

        try:
            for question in self.questions.all():
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                pdf.cell(0, 10, f"Title: {question.question_id}", ln=True)
                # pdf.cell(0, 10, f"Title: {question.question_headline}", ln=True)
                # pdf.cell(0, 12, f"Book: {question.question_book}", ln=True)
                # pdf.cell(0, 14, f"Grade: {question.question_grade}", ln=True)

                # Generate safe filenames
                q_img_local = os.path.join(exam_temp_dir, f"{question.question_id}_q.jpg")
                a_img_local = os.path.join(exam_temp_dir, f"{question.question_id}_a.jpg")

                # Download and compress
                if question.question_img:
                    try:
                        download_file(question.question_img, q_img_local)
                        compress_image(q_img_local, q_img_local)
                        cleanup_files.append(q_img_local)
                    except Exception as e:
                        print(f"[ERROR] Failed to process question image: {e}")

                if question.question_answer_img:
                    try:
                        download_file(question.question_answer_img, a_img_local)
                        compress_image(a_img_local, a_img_local)
                        cleanup_files.append(a_img_local)
                    except Exception as e:
                        print(f"[ERROR] Failed to process answer image: {e}")

                # Add images if exist
                try:
                    if os.path.exists(q_img_local):
                        pdf.image(q_img_local, x=10, y=20, w=90, type='JPEG')
                    if os.path.exists(a_img_local):
                        pdf.image(a_img_local, x=10, y=150, w=90, type='JPEG')
                except Exception as e:
                    print(f"[ERROR] Failed to insert image into PDF: {e}")

            # Save PDF with exam_id
            final_pdf_path = os.path.join(exam_temp_dir, f"{self.exam_id}.pdf")
            print(f"[INFO] Saving PDF: {final_pdf_path}")
            pdf.output(final_pdf_path, 'F')

            # Check file size before upload
            if not os.path.exists(final_pdf_path) or os.path.getsize(final_pdf_path) == 0:
                print("[ERROR] PDF file is empty or missing!")
                return False

            # Upload
            with open(final_pdf_path, 'rb') as f:
                file_data = f.read()
                uploaded_file = SimpleUploadedFile(f"{self.exam_id}.pdf", file_data, content_type="application/pdf")
                self.exam_answer_file = auto_upload("exam_answer", self, file_obj=uploaded_file)
                self.save(update_fields=['exam_answer_file',])
                print("[INFO] PDF uploaded successfully")
                

        finally:
            # Cleanup
            for file_path in cleanup_files:
                if os.path.exists(file_path):
                    os.remove(file_path)
            if final_pdf_path and os.path.exists(final_pdf_path):
                os.remove(final_pdf_path)
            if os.path.exists(exam_temp_dir):
                os.rmdir(exam_temp_dir)
            print("[INFO] Cleanup complete")


    
    
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
        # self.merge_question_answer_images()
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
    non_countable_count = models.IntegerField("تعداد آزمون های حذفی",default=3)
    final_average       = models.DecimalField("میانگین امتحانات با حذف کمترین درصدها",default=0,max_digits=5, decimal_places=2)
    
   
    def get_average(self):
        # ۱. جمع‌آوری داده‌ها با دو کوئری ساده
        online  = list(self.examscore_set.filter(exam_finished=True,countable=True).values_list('score', 'exam_peresence'))
        offline = list(self.examscoreoffline_set.filter(countable=True).values_list('score', 'exam_peresence'))

        records = online + offline
        total = len(records)

        # اگر هیچ امتحانی وجود ندارد
        if total == 0:
            self.exam_count = 0
            self.exam_abscent_count = 0
            self.average = 0
            self.final_average = 0
            self.save(update_fields=['exam_count', 'exam_abscent_count', 'average', 'final_average'])
            return 0

        # ۲. تفکیک نمرات حاضرها
        present_scores = [score for score, present in records if present]
        present_count = len(present_scores)
        abscent_count = total - present_count

        # ۳. محاسبه میانگین ساده (با فرض صفر برای غایب‌ها)
        total_score = sum(present_scores)
        avg = round(total_score / total, 2)

        # ۴. میانگین با حذف کمترین‌ها (اگر شرایط برقرار باشد)
        if total > 10 and present_count > self.non_countable_count:
            trimmed_scores = sorted(present_scores)[self.non_countable_count:]
            final_avg = round(sum(trimmed_scores) / len(trimmed_scores), 2)
        else:
            final_avg = avg

        # ۵. ذخیره با یک save
        self.exam_count = total
        self.exam_abscent_count = abscent_count
        self.average = avg
        self.final_average = final_avg
        self.save(update_fields=['exam_count', 'exam_abscent_count', 'average', 'final_average'])

        return avg
    
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
    countable               = models.BooleanField("محاسبه در میانگین",default=True)

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
    
    
    def __str__(self) :
        # self.get_score()
        return "  %s %s         , نمره:  %s ,       امتحان:  %s,   حضور در امتحان:  %s ,  مجوز برتر:  %s" % (self.exam_average_reffer.user.first_name,self.exam_average_reffer.user.last_name,self.score,self.exam.ExamName,self.exam_peresence,self.exam_permission) 

class ExamScoreOffline (models.Model) :
    exam                    = models.ForeignKey(Exam ,verbose_name="آزمون",on_delete=models.CASCADE)
    exam_average_reffer     = models.ForeignKey(ExamAverage,verbose_name="دانش آموز",on_delete=models.CASCADE)
    score                   = models.DecimalField("درصد آزمون",default=0,max_digits=5, decimal_places=2)
    exam_peresence          = models.BooleanField("حضور در آزمون",default=True)
    updated_at              = models.DateTimeField(auto_now=True,auto_now_add=False)
    countable               = models.BooleanField("محاسبه در میانگین",default=True)   
    # student_extra_score     = models.IntegerField("نمره اضافه",default=0)
    # exam_note               = models.CharField("توضیحات",max_length=100 , blank=True ,null=True)
    # wrong_counts            = models.IntegerField(default=0)
    # none_counts             = models.IntegerField(default=0)