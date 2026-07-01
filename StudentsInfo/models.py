from django.db import models
from django.contrib.auth.models import User, Group
from django.utils import timezone
from ExamsPlatform import models as E_models
from AssignmentPlatform import models as A_models
from ClassroomsPlatform import models as C_models
from django.db.models import Q


class StudentUser (models.Model) :
    student_user        = models.OneToOneField(User , on_delete= models.CASCADE,null=True)
    # birth_date = models.DateField("تاریخ تولد",blank=True,null=True)
    father_name         = models.CharField("نام پدر",blank=True,null=True,max_length=35)
    phone_number        = models.CharField("شماره همراه",blank=True,null=True,max_length=12)
    father_number       = models.CharField("شماره پدر",blank=True,null=True,max_length=12)
    mother_number       = models.CharField("شماره مادر",blank=True,null=True,max_length=12)
    home_number         = models.CharField("شماره ثابت",blank=True,null=True,max_length=12)
    address             = models.CharField( "آدرس",blank=True,null=True,max_length=200)
    registration_date   = models.DateField("تاریخ ثبت نام",blank=True,null=True)
    student_school      = models.CharField("مدرسه",max_length= 20  ,null=True , blank=True)
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
    student_time                   = models.CharField("ساعت کلاس دانش آموز",max_length=25,null=True,blank=True)
    student_day                    = models.CharField("روز کلاس دانش آموز",max_length=25,null=True,blank=True)
    ########
    student_status                 = models.CharField("وضعیت تحصیل",max_length=15, choices=(
        ('در حال تحصیل','در حال تحصیل'),
        ('انصراف','انصراف'),
        ('فارغ التحصیل','فارغ التحصیل'),
    ) ,null=True,blank=True,db_index=True)
    student_study_date                  = models.CharField("تاریخ تحصیل",max_length=60,null=True,blank=True)
    student_description                 = models.CharField("توضیحات",max_length= 300  ,null=True , blank=True)
    # پنل پیامک: آخرین مقصدی که برای این دانش‌آموز پیامک نمره فرستادیم
    last_sms_target                     = models.CharField("آخرین مقصد پیامک",max_length=10, choices=(
        ('mother','مادر'),
        ('father','پدر'),
        ('both','هردو'),
    ) ,null=True,blank=True)
    
    
    def student_group_info (self):
        if self.student_user.groups.all().count():
            self.student_gender = self.student_user.groups.all()[0].group_gender
            self.student_grade  = self.student_user.groups.all()[0].group_grade
            self.student_day    = self.student_user.groups.all()[0].group_day
            self.student_time   = self.student_user.groups.all()[0].group_time
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
    
        classrooms = C_models.Classroom.objects.filter(classroom_groups__in=self.student_user.groups.all(),classroom_status__in=[C_models.ClassroomStatus.ACTIVE, C_models.ClassroomStatus.RUNNING])
        existing_classroom_presences = set(C_models.ClassroomPresence.objects.filter(Q(classroom__in=classrooms) & Q(classroom_average_reffer=classroom_average)).values_list('classroom_id', flat=True))
        new_classroom_presences = [C_models.ClassroomPresence(classroom=classroom, classroom_average_reffer=classroom_average) for classroom in classrooms if classroom.classroom_id not in existing_classroom_presences]
        C_models.ClassroomPresence.objects.bulk_create(new_classroom_presences)


    def __str__(self) -> str:
        # بدون عارضه‌ی جانبی؛ student_group_info/create_averages صراحتاً در ویوها صدا زده می‌شوند
        if self.student_user:
            return "%s %s" % (self.student_user.first_name, self.student_user.last_name)
        return "StudentUser %s" % self.pk

class SignedCheck (models.Model) :
    student         = models.ForeignKey(User,on_delete= models.CASCADE)
    amout           = models.CharField("مبلغ",max_length=50)
    check_date      = models.CharField("تاریخ چک",max_length=50,blank=True,null=True)
    check_number    = models.CharField("شماره چک",max_length=50,blank=True,null=True)
    bank            = models.CharField("بانک صیادی",max_length=30,blank=True,null=True)
    reg_status      = models.BooleanField("وضعیت ثبت صیادی",blank=True,null=True)
    description     = models.CharField("توضیحات چک",max_length=250,blank=True,null=True)
    
class DirectMoney (models.Model) :
    student             = models.ForeignKey(User,on_delete= models.CASCADE)
    amout               = models.CharField("مبلغ",max_length=50)
    payment_date        = models.CharField("تاریخ پرداخت",max_length=50,blank=True,null=True)
    refrence_number     = models.CharField("شماره رهگیری",max_length=50,blank=True,null=True)
    following_number    = models.CharField("شماره پیگیری",max_length=200,blank=True,null=True)
    card_number         = models.CharField("چهار رقم آخر کارت",max_length=50,blank=True,null=True)
    payment_method      = models.CharField("شیوه انتقال",max_length=30,blank=True,null=True)
    bank                = models.CharField("بانک عامل",max_length=30,blank=True,null=True)
    description         = models.CharField("توضیحات",max_length=250,blank=True,null=True)
 
class Books (models.Model) :
    student     = models.ManyToManyField(User, verbose_name="جزوه", blank=True)
    booksname   = models.CharField("نام جزوه",max_length=50,blank=True,null=True)

class StudentHistory (models.Model) :
    student             = models.ForeignKey(User,on_delete= models.CASCADE)
    father_name         = models.CharField("نام پدر",blank=True,null=True,max_length=35)
    phone_number        = models.CharField("شماره همراه",blank=True,null=True,max_length=12)
    father_number       = models.CharField("شماره پدر",blank=True,null=True,max_length=12)
    mother_number       = models.CharField("شماره مادر",blank=True,null=True,max_length=12)
    home_number         = models.CharField("شماره ثابت",blank=True,null=True,max_length=12)
    address             = models.CharField( "آدرس",blank=True,null=True,max_length=200)
    registration_date   = models.DateField("تاریخ ثبت نام",blank=True,null=True)
    school              = models.CharField("مدرسه",max_length= 20  ,null=True , blank=True)
    ClassroomAbscents   = models.CharField("تعداد غیبت جلسات",max_length=10)
    ExamAverage         = models.CharField("میانگین درصد امتحانات",max_length=10)
    ExamAverageFine     = models.CharField("میانگین درصد امتحانات با حذف 3  کمترین نمرات",max_length=10)
    ExamAbscent         = models.CharField("تعداد غیبت آزمون ها",max_length=10)
    AssignmentAverage   = models.CharField("میانگین درصد تکالیف",max_length=10)
    AssignmentAbscent   = models.CharField("تعداد غیبت تکالیف",max_length=10)
    #####
    type                = models.CharField("رشته",max_length=25,null=True,blank=True)
    gender              = models.CharField("جنسیت",max_length=15, choices=(
        ('پسر','پسر'),
        ('دختر','دختر')
    ) ,null=True,blank=True)
    grade               = models.CharField("پایه",max_length=15, choices=(
        ('دهم','دهم'),
        ('یازدهم','یازدهم'),
        ('دوازدهم','دوازدهم')
    ) ,null=True,blank=True)
    ########
    status              = models.CharField("وضعیت تحصیل",max_length=15, choices=(
        ('در حال تحصیل','در حال تحصیل'),
        ('انصراف','انصراف'),
        ('فارغ التحصیل','فارغ التحصیل'),
    ) ,null=True,blank=True)
    study_date          = models.CharField("سال تحصیلی",max_length=25,null=True,blank=True)
    description         = models.CharField("توضیحات",max_length= 300  ,null=True , blank=True)
    

class Notification(models.Model):
    title           = models.CharField(max_length=150)
    message         = models.TextField()
    # group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="notifications")
    groups           = models.ManyToManyField(Group)
    is_persistent   = models.BooleanField(default=False)
    is_finished     = models.BooleanField(default=False)
    created_at      = models.DateTimeField(auto_now_add=True)

class UserNotification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name="user_notifications")


# ───────────────────────── آرشیو سال تحصیلی ─────────────────────────
# هنگام بایگانی پایان سال، یک اسنپ‌شات از وضعیت تحصیلی هر دانش‌آموز ساخته می‌شود
# تا پس از حذف Exam/Assignment/Classroom/Group، رکورد سال‌به‌سال باقی بماند.
class StudentYearRecord (models.Model) :
    # SET_NULL تا اگر بعداً اکانت دانش‌آموز حذف شد، تاریخچه از بین نرود
    student                  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='year_records', verbose_name="دانش آموز")
    student_name             = models.CharField("نام دانش آموز", max_length=120, null=True, blank=True)
    study_year               = models.CharField("سال تحصیلی", max_length=20, db_index=True)   # مثل "۱۴۰۳-۱۴۰۴"
    grade                    = models.CharField("پایه", max_length=15, null=True, blank=True)   # مثل "یازدهم"
    group_name               = models.CharField("گروه", max_length=150, null=True, blank=True)
    student_type             = models.CharField("رشته", max_length=25, null=True, blank=True)
    # سه میانگین کل
    exam_average             = models.DecimalField("میانگین امتحانات", max_digits=5, decimal_places=2, default=0)
    exam_final_average       = models.DecimalField("میانگین امتحانات (با حذف کمترین‌ها)", max_digits=5, decimal_places=2, default=0)
    exam_count               = models.IntegerField("تعداد امتحانات", default=0)
    exam_absent_count        = models.IntegerField("غیبت امتحان", default=0)
    assignment_average       = models.DecimalField("میانگین تکالیف", max_digits=5, decimal_places=2, default=0)
    assignment_count         = models.IntegerField("تعداد تکالیف", default=0)
    assignment_absent_count  = models.IntegerField("غیبت تکلیف", default=0)
    classroom_absence_count  = models.IntegerField("غیبت کلاس", default=0)
    status                   = models.CharField("وضعیت پایان سال", max_length=15, null=True, blank=True)  # در حال تحصیل / فارغ التحصیل / انصراف
    created_at               = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'study_year')
        ordering = ['study_year', 'id']

    def __str__(self) -> str:
        return "%s - %s (%s)" % (self.student_name or self.student, self.study_year, self.grade)


class YearExamRecord (models.Model) :
    year_record = models.ForeignKey(StudentYearRecord, on_delete=models.CASCADE, related_name='exam_records')
    title       = models.CharField("نام آزمون", max_length=100, null=True, blank=True)
    headline    = models.CharField("موضوع", max_length=100, null=True, blank=True)
    date        = models.DateTimeField("تاریخ", null=True, blank=True)
    score       = models.DecimalField("درصد", max_digits=5, decimal_places=2, default=0)
    present     = models.BooleanField("حضور", default=False)
    is_offline  = models.BooleanField("آفلاین", default=False)


class YearAssignmentRecord (models.Model) :
    year_record = models.ForeignKey(StudentYearRecord, on_delete=models.CASCADE, related_name='assignment_records')
    title       = models.CharField("نام تکلیف", max_length=100, null=True, blank=True)
    headline    = models.CharField("موضوع", max_length=100, null=True, blank=True)
    date        = models.DateTimeField("تاریخ", null=True, blank=True)
    score       = models.DecimalField("درصد", max_digits=5, decimal_places=2, default=0)
    present     = models.BooleanField("ارسال/حضور", default=False)


# ───────────────────────── حضور و غیاب حضوری ─────────────────────────
# هر ردیف = حضور/غیبت یک دانش‌آموز در یک جلسه‌ی حضوری (از اکسل مرکز همگام می‌شود).
class AttendanceRecord (models.Model) :
    student       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendance_records', verbose_name="دانش آموز")
    group_name    = models.CharField("گروه", max_length=150, null=True, blank=True)
    session_title = models.CharField("موضوع جلسه", max_length=150, null=True, blank=True)
    date          = models.DateField("تاریخ جلسه", null=True, blank=True, db_index=True)
    present       = models.BooleanField("حاضر", default=True)
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', 'id']

    def __str__(self) -> str:
        return "%s - %s (%s)" % (self.student, self.session_title, "حاضر" if self.present else "غایب")

Group.add_to_class('group_time',    models.CharField("ساعت کلاس",max_length= 30
     ,null=True , blank=True))

Group.add_to_class('group_day',     models.CharField("روز کلاس",max_length= 20 , choices=(
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
        ('سه شنبه','سه شنبه'),
        ('چهارشنبه','چهارشنبه'),
        ('پنج شنبه','پنج شنبه'),
        ('جمعه','جمعه'),
    ) ,null=True , blank=True))     

Group.add_to_class('group_gender',  models.CharField("جنسیت",max_length= 5 , choices=(
        ('پسر','پسر'),
        ('دختر','دختر')
    ) ,null=True , blank=True))

Group.add_to_class('group_grade',   models.CharField("مقطع",max_length= 8 , choices=(
        ('دهم','دهم'),
        ('یازدهم','یازدهم'),
        ('دوازدهم','دوازدهم')
    ) ,null=True , blank=True))

Group.add_to_class('group_cost',    models.IntegerField("مبلغ کلاس" ,null=True , blank=True))


class TokenSession(models.Model):
    """نشستِ فعالِ متناظر با هر توکنِ Knox (برای پنل «دستگاه‌های فعال»).

    Knox خودش فقط digest/user/created/expiry را نگه می‌دارد؛ این مدل متادیتای
    قابل‌نمایش (IP، User-Agent، دستگاه، کشور، آخرین‌استفاده) را ذخیره می‌کند.

    عمداً به‌جای FK به مدلِ swappableِ knox، فقط digestِ توکن (=PK آن) را به‌صورت یک
    فیلدِ ساده نگه می‌داریم: هم از دردسرِ FK به مدلِ swappable (خطای SQLite) پرهیز
    می‌شود و هم DB-agnostic می‌ماند. «زنده‌بودن» نشست با join به AuthTokenهای فعال
    تعیین می‌شود؛ ردیف‌های یتیم (توکنشان حذف شده) شبانه با cleanup_tokens پاک می‌شوند.
    """
    token_digest = models.CharField("digest توکن", max_length=128, unique=True, db_index=True)
    token_key    = models.CharField("پیشوند توکن", max_length=25, blank=True, default='')
    user         = models.ForeignKey(User, on_delete=models.CASCADE,
                                     related_name='token_sessions', verbose_name="کاربر")
    ip_address   = models.GenericIPAddressField("آی‌پی", null=True, blank=True)
    user_agent   = models.TextField("User-Agent", blank=True, default='')
    device       = models.CharField("دستگاه", max_length=120, blank=True, default='')
    country      = models.CharField("کشور", max_length=80, blank=True, default='')
    created      = models.DateTimeField("ورود", default=timezone.now)
    last_used    = models.DateTimeField("آخرین استفاده", default=timezone.now, db_index=True)

    class Meta:
        ordering = ['-last_used']
        verbose_name = "نشست فعال"
        verbose_name_plural = "نشست‌های فعال"

    def __str__(self) -> str:
        return "%s - %s (%s)" % (self.user, self.device or "?", self.ip_address or "?")

