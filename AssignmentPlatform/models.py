from django.db import models
from django.contrib.auth.models import User,Group
import uuid
from datetime import datetime,timedelta
from django.utils import timezone
from datetime import datetime
from Frontend.function import path_and_rename
# Create your models here.
from decimal import Decimal

class Assignment (models.Model) :
    assignment_group            = models.ForeignKey(Group,verbose_name="گروه",on_delete=models.CASCADE)
    assignment_id               = models.UUIDField("شماره شناسایی تکلیف",primary_key=True,default=uuid.uuid1,help_text="شماره شناسایی تکلیف به طور خودکار ساخته میشود و باید بی همتا باشد،لطفا تغییر ندهید")
    AssignmentName              = models.CharField("نام تکلیف",max_length=100 , blank=True ,null=True)
    assignment_headline         = models.CharField("موضوع تکلیف",max_length=100 , blank=True ,null=True)   
    assignment_description      = models.TextField("توضیحات تکلیف",max_length=500,blank=True,null=True)    
    assignment_creation_time          = models.DateTimeField("زمان ساخت تکلیف",auto_now_add=True)
    assignment_available_time_start   = models.DateTimeField("زمان شروع تکلیف",default= datetime.now())
    assignment_available_time_end     = models.DateTimeField("زمان پایان تکلیف",default= datetime.now() + timedelta(days=1))
    assignment_permission             = models.BooleanField("وضعیت  دسترسی تکلیف",default=True)
    assignment_finished               = models.BooleanField("وضعیت  اتمام تکلیف",default=False)
    assignment_extra_score            = models.IntegerField("نمره اضافه",default=0)
    assignment_file                     = models.FileField("فایل تکلیف",upload_to=path_and_rename("assignment_file"),max_length=500, blank=True ,null=True)
    assignment_answer_file              = models.FileField("فایل پاسخ تکلیف",upload_to=path_and_rename("assignment_answer_file"),max_length=500, blank=True ,null=True)


    
    def finish_assignment(self):
        if self.assignment_available_time_end < timezone.now() and not self.assignment_finished:
            self.assignment_finished = True
            self.assignment_permission = False
            self.save()
    
            assignment_scores = self.assignmentscore_set.filter(assignment_finished=False)
            assignment_scores.update(assignment_finished=True)
    
            # Calculate scores
            scores_to_update = []
            for assignment_score in assignment_scores:
                if not assignment_score.assignment_presence and not assignment_score.assignment_marked:
                    assignment_score.score = 0
                    assignment_score.assignment_marked=True
                    assignment_score.assignment_marked_by="System"
                    assignment_score.save()
                    # scores_to_update.append(assignment_score)
                elif assignment_score.assignment_marked:
                    assignment_score.score = sum([
                        assignment_score.q1_score, assignment_score.q2_score, assignment_score.q3_score, assignment_score.q4_score, assignment_score.q5_score,
                        assignment_score.q6_score, assignment_score.q7_score, assignment_score.q8_score, assignment_score.q9_score, assignment_score.q10_score,
                        assignment_score.q11_score, assignment_score.q12_score, assignment_score.q13_score, assignment_score.q14_score, assignment_score.q15_score,
                        assignment_score.q16_score, assignment_score.q17_score, assignment_score.q18_score, assignment_score.q19_score, assignment_score.q20_score,
                        assignment_score.extra_score, self.assignment_extra_score
                    ])
                    if assignment_score.score > 100:
                        assignment_score.score = 100
                    scores_to_update.append(assignment_score)
    
            # Update scores in bulk
            AssignmentScore.objects.bulk_update(scores_to_update, ['score'])
    
            # Calculate averages
            averages_to_update = {}
            for score in scores_to_update:
                average = score.assignment_average_reffer
                if average not in averages_to_update:
                    averages_to_update[average] = {
                        'sum': 0,
                        'count': 0,
                        'absent_count': 0
                    }
                if score.assignment_presence:
                    averages_to_update[average]['sum'] += score.score
                    averages_to_update[average]['count'] += 1
                else:
                    averages_to_update[average]['absent_count'] += 1
    
            for average, data in averages_to_update.items():
                average.average = data['sum'] / data['count'] if data['count'] > 0 else 0
                average.assignment_count = data['count']
                average.assignment_abscent_count = data['absent_count']
            
            # Update averages in bulk
            AssignmentAverage.objects.bulk_update(averages_to_update.keys(), ['average', 'assignment_count', 'assignment_abscent_count'])

   
    
    
    def create_assignment_score(self):
        student_ids = self.assignment_group.user_set.values_list('id', flat=True)
        existing_student_ids = AssignmentScore.objects.filter(assignment=self, assignment_average_reffer__user__in=student_ids).values_list('assignment_average_reffer__user', flat=True)
        new_student_ids = set(student_ids) - set(existing_student_ids)
        new_assignment_scores = []
        for student_id in new_student_ids:
            student = User.objects.select_related('assignmentaverage').get(id=student_id)
            student_assignmentaverage = student.assignmentaverage
            a = AssignmentScore(assignment_average_reffer=student_assignmentaverage, assignment=self, assignment_presence=False)
            new_assignment_scores.append(a)
        AssignmentScore.objects.bulk_create(new_assignment_scores)
    
    
    def update_assignment_score(self):
        student_ids = self.assignment_group.user_set.values_list('id', flat=True)
        assignment_scores = self.assignmentscore_set.filter(assignment_average_reffer__in=student_ids)
        for assignment_score in assignment_scores:
            assignment_score.get_score()

    

    def __str__(self):
        # self.assignment_info()
        self.create_assignment_score()
        self.update_assignment_score()
        return "%s Creation Time: %s" % (self.AssignmentName, self.assignment_creation_time.strftime("%c"))
    

class AssignmentAverage (models.Model) :
    user                    = models.OneToOneField(User ,verbose_name="دانش آموز",on_delete=models.CASCADE,)
    average                 = models.DecimalField("میانگین تکالیف",default=0,max_digits=5, decimal_places=2)
    assignment_count        = models.IntegerField("تعداد تکالیف",default=0)
    assignment_abscent_count= models.IntegerField("تکالیف غایب",default=0)

    def get_average(self):        
        scoreset=self.assignmentscore_set.all().filter(assignment_finished=True)
        self.assignment_count=scoreset.count()
        assignment_sum=0  
        abscent_sum=0             
        if self.assignment_count :
            for assignments in scoreset :
                if assignments.assignment_presence :
                    assignment_sum += assignments.score                    
                else:
                    abscent_sum +=1
            self.assignment_abscent_count=abscent_sum
            self.average = round(assignment_sum/self.assignment_count,2)
            self.save()
        else:
            self.average=0 
            #bug on removing all scores with no score but average , only call save
        return self.average
        
    def __str__(self) :
        return "  %s %s    ,میانگین: %s" % (self.user.first_name,self.user.last_name,self.get_average()) 


class AssignmentScore (models.Model) :
    assignment                = models.ForeignKey(Assignment ,verbose_name="تکلیف",on_delete=models.CASCADE)
    assignment_average_reffer = models.ForeignKey(AssignmentAverage,verbose_name="دانش آموز",on_delete=models.CASCADE)
    assignment_student_file   = models.FileField("تکلیف دانش آموز",upload_to=path_and_rename('assignment/students/'),max_length=500, blank=True ,null=True)
    assignment_teacher_file   = models.FileField("تصحیح دانش آموز",upload_to=path_and_rename('assignment/students/answers/'),max_length=500, blank=True ,null=True)
    score                     = models.DecimalField("درصد تکلیف",default=0,max_digits=5, decimal_places=2)
    assignment_permission     = models.BooleanField("مجوز دستی تکلیف",default=False)
    assignment_presence       = models.BooleanField("ارسال تکلیف",default=False)
    assignment_finished       = models.BooleanField("پایان تکلیف",default=False)
    assignment_marked         = models.BooleanField("وضعیت تصحیح تکلیف",default=False)
    assignment_marked_by      = models.CharField("مصحح",max_length=100 , blank=True ,null=True)
    score_nums                = (
        ( 0 , 0),
        ( 1 , 1),
        ( 2 , 2),
        ( 3 , 3),
        ( 4 , 4),
        ( 5 , 5),
    )
    updated_file_at = models.DateTimeField(auto_now_add=True)
    extra_score     = models.DecimalField("درصد اضافه",max_digits=5, decimal_places=2, default=0.00)            
    q1_score = models.DecimalField("نمره سوال 1", max_digits=4, decimal_places=2, blank=True, null=True, default=None)
    q2_score = models.DecimalField("نمره سوال 2", max_digits=4, decimal_places=2, blank=True, null=True, default=None)
    q3_score = models.DecimalField("نمره سوال 3", max_digits=4, decimal_places=2, blank=True, null=True, default=None)
    q4_score = models.DecimalField("نمره سوال 4", max_digits=4, decimal_places=2, blank=True, null=True, default=None)
    q5_score = models.DecimalField("نمره سوال 5", max_digits=4, decimal_places=2, blank=True, null=True, default=None)
    q6_score = models.DecimalField("نمره سوال 6", max_digits=4, decimal_places=2, blank=True, null=True, default=None)
    q7_score = models.DecimalField("نمره سوال 7", max_digits=4, decimal_places=2, blank=True, null=True, default=None)
    q8_score = models.DecimalField("نمره سوال 8", max_digits=4, decimal_places=2, blank=True, null=True, default=None)
    q9_score = models.DecimalField("نمره سوال 9", max_digits=4, decimal_places=2, blank=True, null=True, default=None)
    q10_score = models.DecimalField("نمره سوال 10", max_digits=4, decimal_places=2, blank=True, null=True, default=None)
    # q1_score        = models.DecimalField("نمره سوال 1",max_digits=4, decimal_places=2, default=2)
    # q2_score        = models.DecimalField("نمره سوال 2",max_digits=4, decimal_places=2, default=2)
    # q3_score        = models.DecimalField("نمره سوال 3",max_digits=4, decimal_places=2, default=2)
    # q4_score        = models.DecimalField("نمره سوال 4",max_digits=4, decimal_places=2, default=2)
    # q5_score        = models.DecimalField("نمره سوال 5",max_digits=4, decimal_places=2, default=2)
    # q6_score        = models.DecimalField("نمره سوال 6",max_digits=4, decimal_places=2, default=2)
    # q7_score        = models.DecimalField("نمره سوال 7",max_digits=4, decimal_places=2, default=2)
    # q8_score        = models.DecimalField("نمره سوال 8",max_digits=4, decimal_places=2, default=2)
    # q9_score        = models.DecimalField("نمره سوال 9",max_digits=4, decimal_places=2, default=2)
    # q10_score       = models.DecimalField("نمره سوال 10",max_digits=4, decimal_places=2, default=2)
    q11_score       = models.DecimalField("نمره سوال 11",max_digits=4, decimal_places=2, default=0.00)
    q12_score       = models.DecimalField("نمره سوال 12",max_digits=4, decimal_places=2, default=0.00)
    q13_score       = models.DecimalField("نمره سوال 13",max_digits=4, decimal_places=2, default=0.00)
    q14_score       = models.DecimalField("نمره سوال 14",max_digits=4, decimal_places=2, default=0.00)
    q15_score       = models.DecimalField("نمره سوال 15",max_digits=4, decimal_places=2, default=0.00)
    q16_score       = models.DecimalField("نمره سوال 16",max_digits=4, decimal_places=2, default=0.00)
    q17_score       = models.DecimalField("نمره سوال 17",max_digits=4, decimal_places=2, default=0.00)
    q18_score       = models.DecimalField("نمره سوال 18",max_digits=4, decimal_places=2, default=0.00)
    q19_score       = models.DecimalField("نمره سوال 19",max_digits=4, decimal_places=2, default=0.00)
    q20_score       = models.DecimalField("نمره سوال 20",max_digits=4, decimal_places=2, default=0.00)
    
    
    def get_score(self):
        if not self.assignment_presence and self.assignment_finished and not self.assignment_marked:
            self.score = 0
            self.save(update_fields=['score'])
            self.assignment_average_reffer.get_average()
        elif self.assignment_marked:
            # self.score = sum([
            #     self.q1_score, self.q2_score, self.q3_score, self.q4_score, self.q5_score,
            #     self.q6_score, self.q7_score, self.q8_score, self.q9_score, self.q10_score,
            #     self.q11_score, self.q12_score, self.q13_score, self.q14_score, self.q15_score,
            #     self.q16_score, self.q17_score, self.q18_score, self.q19_score, self.q20_score,
            #     self.extra_score, self.assignment.assignment_extra_score
            # ])
            scores = [
                Decimal(self.q1_score or 0.00), Decimal(self.q2_score or 0.00), Decimal(self.q3_score or 0.00),
                Decimal(self.q4_score or 0.00), Decimal(self.q5_score or 0.00), Decimal(self.q6_score or 0.00),
                Decimal(self.q7_score or 0.00), Decimal(self.q8_score or 0.00), Decimal(self.q9_score or 0.00),
                Decimal(self.q10_score or 0.00), Decimal(self.q11_score), Decimal(self.q12_score),
                Decimal(self.q13_score), Decimal(self.q14_score), Decimal(self.q15_score),
                Decimal(self.q16_score), Decimal(self.q17_score), Decimal(self.q18_score),
                Decimal(self.q19_score), Decimal(self.q20_score), Decimal(self.extra_score),
                Decimal(self.assignment.assignment_extra_score)
            ]

            self.score = sum(scores)
            if self.score > 100 :
                self.score = 100
            self.save(update_fields=['score'])
            self.assignment_average_reffer.get_average()
    
    def __str__(self) :
        self.get_score()
        return "  %s %s         , نمره:  %s ,       تکلیف:  %s" % (self.assignment_average_reffer.user.first_name,self.assignment_average_reffer.user.last_name,self.score,self.assignment.AssignmentName) 
