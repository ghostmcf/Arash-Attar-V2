from rest_framework import serializers
from django.contrib.auth.models import User, Group
from ClassroomsPlatform.models import Classroom
from AssignmentPlatform.models import Assignment,AssignmentScore,AssignmentAverage
from StudentsInfo.models import StudentUser,SignedCheck,DirectMoney,Books,StudentYearRecord,YearExamRecord,YearAssignmentRecord,AttendanceRecord
from ExamsPlatform.models import Question,Exam,ExamAverage,ExamScore



#######################################


class SignedCheckSerializer (serializers.ModelSerializer):
    check_date = serializers.DateField(format="%Y-%m-%d", input_formats=['%Y-%m-%d',])
    class Meta:
        model = SignedCheck
        fields = "__all__" 
        
class DirectMoneySerializer (serializers.ModelSerializer):
    payment_date = serializers.DateField(format="%Y-%m-%d", input_formats=['%Y-%m-%d',])
    class Meta:
        model = DirectMoney
        fields = "__all__"         

class BooksSerializer(serializers.ModelSerializer):
    class Meta:
        model = Books
        fields = ['id','booksname',]
        # fields = "__all__"

class BooksUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = Books
        fields = ['booksname','id']
###################################################################
class AssignmentUserSerializer (serializers.ModelSerializer):
    class Meta:
        model = Assignment
        fields = ('assignment_id','AssignmentName','assignment_headline')    
        
class AssignmentScoreUserSerializer (serializers.ModelSerializer):
    assignment           = AssignmentUserSerializer(read_only=True)
    class Meta:
        model = AssignmentScore
        fields = ('id','score','assignment','assignment_presence','assignment_marked','assignment_student_file','assignment_teacher_file')
        read_only_fields = ['assignment_student_file', 'assignment_teacher_file']
        
class AssignmentAverageUserSerializer (serializers.ModelSerializer):
    assignmentscore_set =AssignmentScoreUserSerializer(many=True, read_only=True)
    class Meta:
        model = AssignmentAverage
        fields = ('average','assignment_abscent_count','assignmentscore_set')
 
##########
class ExamUserSerializer (serializers.ModelSerializer):
    class Meta:
        model = Exam
        fields = ('exam_id','ExamName','exam_headline') 

class ExamScoreUserSerializer (serializers.ModelSerializer):
    exam           = ExamUserSerializer(read_only=True)
    class Meta:
        model = ExamScore
        fields = ('id','score','exam','exam_peresence','exam_finished',)        
class ExamAverageUserSerializer (serializers.ModelSerializer):
    examscore_set =ExamScoreUserSerializer(many=True, read_only=True)
    class Meta:
        model = ExamAverage
        fields = ('average','final_average','exam_count','exam_abscent_count','examscore_set')
 
class ExamAverageNCSerializer (serializers.ModelSerializer):
    class Meta:
        model = ExamAverage
        fields = ['non_countable_count']
#############################################
class GroupsSerializer (serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ("id","name","group_time","group_day","group_gender","group_grade",)
        
        
class SmallStudentInfoSerializer (serializers.ModelSerializer):
    class Meta:
        model = StudentUser 
        fields = ('father_name','student_school')

class StudentInfoSerializer (serializers.ModelSerializer):
    class Meta:
        model = StudentUser
        # فیلدها صریح (به‌جای __all__)
        fields = (
            'id', 'student_user', 'father_name', 'phone_number', 'father_number',
            'mother_number', 'home_number', 'address', 'registration_date',
            'student_school', 'student_type', 'student_gender', 'student_grade',
            'student_time', 'student_day', 'student_status', 'student_study_date',
            'student_description',
        )

class UserSerializer (serializers.ModelSerializer):
    studentuser  = StudentInfoSerializer( read_only=True)
    examaverage = ExamAverageUserSerializer( read_only=True)
    assignmentaverage = AssignmentAverageUserSerializer( read_only=True)
    directmoney_set=DirectMoneySerializer(many=True, read_only=True)
    signedcheck_set=SignedCheckSerializer(many=True, read_only=True)
    class Meta:
        model = User
        fields = ('id','is_active','username','first_name','last_name','groups','studentuser','assignmentaverage','examaverage','directmoney_set','signedcheck_set')
        # extra_kwargs = {
        #     'date_joined': {'required': False},
        # }
        # extra_kwargs = {'password': {'write_only': True}}

class SmallUserSerializer (serializers.ModelSerializer):
    studentuser  = SmallStudentInfoSerializer( read_only=True)
    groups       = GroupsSerializer(many=True)
    class Meta:
        model = User
        fields = ('id','username','first_name','last_name','groups','studentuser',)     
    
class GroupSerializer (serializers.ModelSerializer):
    user_set  = SmallUserSerializer(many=True, read_only=True)
    class Meta:
        model = Group
        fields = ("id",'user_set',"name","group_time","group_day","group_gender","group_grade",'group_cost')
###################################CREATING USER

# class CreateUserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ['id','username', 'first_name', 'last_name','email']

class CreateStudentUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentUser
        fields = ['id', 'student_user', 'father_name', 'phone_number', 'father_number', 'mother_number', 'home_number', 'address', 'registration_date', 'student_school', 'student_type', 'student_gender', 'student_grade']
        
class UpdateStudentUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentUser
        fields = ['id', 'student_user', 'father_name', 'phone_number', 'father_number', 'mother_number', 'home_number', 'address', 'registration_date','student_school', 'student_type', 'student_gender', 'student_grade']       
###################################################################

class ClassroomSerializer (serializers.ModelSerializer):
    # classroom_creation_time         = serializers.DateTimeField(format="%Y-%m-%d", input_formats=['%Y-%m-%d',])
    # classroom_available_time_start  = serializers.DateTimeField(format="%Y-%m-%d", input_formats=['%Y-%m-%d',])
    classroom_available_time_end    = serializers.DateTimeField(format="%Y-%m-%d", input_formats=['%Y-%m-%d',])
    class Meta:
        model = Classroom
        fields = "__all__"
        

class ClassroomsSerializer (serializers.ModelSerializer):
    classroom_groups       = GroupsSerializer(many=True)
    classroom_available_time_end = serializers.DateTimeField(format="%Y-%m-%d", input_formats=['%Y-%m-%d',])
    class Meta:
        model = Classroom
        fields = ('ClassroomName','classroom_id','classroom_headline','classroom_available_time_end','classroom_presence','classroom_status','classroom_groups')#,'content1_url1','content2_url1','content3_url1','content4_url1','content5_url1')   
################################################################
class AssignmentSerializer (serializers.ModelSerializer):
    assignment_available_time_start   = serializers.DateTimeField(format="%Y-%m-%d %H:%M", input_formats=['%Y-%m-%d %H:%M',])
    assignment_available_time_end     = serializers.DateTimeField(format="%Y-%m-%d %H:%M", input_formats=['%Y-%m-%d %H:%M',])
    # assignment_creation_time          = serializers.DateTimeField(format="%Y-%m-%d %H:%M", input_formats=['%Y-%m-%d %H:%M',])
    class Meta:
        model = Assignment
        fields = "__all__"
        read_only_fields = ['assignment_file', 'assignment_answer_file']
            
class AssignmentSerializerWithGroup (serializers.ModelSerializer):
    assignment_group       = GroupsSerializer()
    assignment_available_time_start   = serializers.DateTimeField(format="%Y-%m-%d %H:%M", input_formats=['%Y-%m-%d %H:%M',])
    assignment_available_time_end     = serializers.DateTimeField(format="%Y-%m-%d %H:%M", input_formats=['%Y-%m-%d %H:%M',])
    # assignment_creation_time          = serializers.DateTimeField(format="%Y-%m-%d %H:%M", input_formats=['%Y-%m-%d %H:%M',])
    class Meta:
        model = Assignment
        fields = "__all__"  
        read_only_fields = ['assignment_file', 'assignment_answer_file']

        
class AssignmentAverageSerializer (serializers.ModelSerializer):
    class Meta:
        model = AssignmentAverage
        fields = "__all__"               
############
class AssignmentForScoreSerializer (serializers.ModelSerializer):
    class Meta:
        model = Assignment
        fields = ('assignment_id','AssignmentName','assignment_headline','assignment_finished') 

class AssignmentAverageForScoreSerializer (serializers.ModelSerializer):
    user          = SmallUserSerializer()
    class Meta:
        model = AssignmentAverage
        fields = ('user',) 
        
class OnlyNameUserSerializer (serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id','username','first_name','last_name') 
        
class AssignmentAverageForPrimaryInfosScoreSerializer (serializers.ModelSerializer):
    user          = OnlyNameUserSerializer()
    class Meta:
        model = AssignmentAverage
        fields = ('user',)
        
class AssignmentScoreSerializer (serializers.ModelSerializer):
    assignment_average_reffer   = AssignmentAverageForScoreSerializer()
    assignment                  = AssignmentForScoreSerializer()
    updated_file_at            = serializers.DateTimeField(format="%Y-%m-%d %H:%M", input_formats=['%Y-%m-%d %H:%M',])
    class Meta:
        model = AssignmentScore
        fields = "__all__"  
        read_only_fields = ['assignment_student_file', 'assignment_teacher_file']
        
class AssignmentScoresSerializer (serializers.ModelSerializer):
    assignment_average_reffer   = AssignmentAverageForPrimaryInfosScoreSerializer()
    assignment           = AssignmentForScoreSerializer()
    updated_file_at            = serializers.DateTimeField(format="%Y-%m-%d %H:%M", input_formats=['%Y-%m-%d %H:%M',])
    class Meta:
        model = AssignmentScore
        fields = ('id','score','assignment_average_reffer','updated_file_at','assignment','assignment_teacher_file','assignment_student_file','assignment_presence','assignment_finished','assignment_marked','assignment_marked_by')    
        read_only_fields = ['assignment_student_file', 'assignment_teacher_file']
###########################################################
class QuestionSerializer (serializers.ModelSerializer):
    # question_creation_time  = serializers.DateTimeField(format="%Y-%m-%d %H:%M", input_formats=['%Y-%m-%d %H:%M',])
    class Meta:
        model = Question
        fields = "__all__"  
        read_only_fields = ['question_img', 'question_answer_img']
        
    # questions= QuestionSerializer(many=True, read_only=True)

        
class ExamSerializer (serializers.ModelSerializer):
    # exam_creation_time          = serializers.DateTimeField(format="%Y-%m-%d %H:%M", input_formats=['%Y-%m-%d %H:%M',])
    exam_available_time_start   = serializers.DateTimeField(format="%Y-%m-%d %H:%M", input_formats=['%Y-%m-%d %H:%M',])
    exam_available_time_end     = serializers.DateTimeField(format="%Y-%m-%d %H:%M", input_formats=['%Y-%m-%d %H:%M',])
    exam_maxenterance_time      = serializers.DateTimeField(format="%Y-%m-%d %H:%M", input_formats=['%Y-%m-%d %H:%M',])
    class Meta:
        model = Exam
        fields = "__all__"  
        read_only_fields = ['exam_answer_file', 'exam_description']
        
class ExamSerializerWithGroup (serializers.ModelSerializer):
    exam_group=GroupsSerializer()
    # exam_creation_time          = serializers.DateTimeField(format="%Y-%m-%d %H:%M", input_formats=['%Y-%m-%d %H:%M',])
    exam_available_time_start   = serializers.DateTimeField(format="%Y-%m-%d %H:%M", input_formats=['%Y-%m-%d %H:%M',])
    exam_available_time_end     = serializers.DateTimeField(format="%Y-%m-%d %H:%M", input_formats=['%Y-%m-%d %H:%M',])
    exam_maxenterance_time      = serializers.DateTimeField(format="%Y-%m-%d %H:%M", input_formats=['%Y-%m-%d %H:%M',])
    class Meta:
        model = Exam
        fields = "__all__"  
        read_only_fields = ['exam_answer_file', 'exam_description']   
             
        
        
class ExamSerializerWithQuestion (serializers.ModelSerializer):
    questions= QuestionSerializer(many=True, read_only=True)
    # exam_creation_time          = serializers.DateTimeField(format="%Y-%m-%d %H:%M", input_formats=['%Y-%m-%d %H:%M',])
    exam_available_time_start   = serializers.DateTimeField(format="%Y-%m-%d %H:%M", input_formats=['%Y-%m-%d %H:%M',])
    exam_available_time_end     = serializers.DateTimeField(format="%Y-%m-%d %H:%M", input_formats=['%Y-%m-%d %H:%M',])
    exam_maxenterance_time      = serializers.DateTimeField(format="%Y-%m-%d %H:%M", input_formats=['%Y-%m-%d %H:%M',])
    class Meta:
        model = Exam
        fields = "__all__"
        read_only_fields = ['exam_answer_file', 'exam_description']

class ExamNameSerializer (serializers.ModelSerializer):
    class Meta:
        model = Exam
        fields = ('ExamName',) 
        
        
class ExamScoresSerializerWithExamName (serializers.ModelSerializer):   
    # updated_at                          = serializers.DateTimeField(format="%Y-%m-%d %H:%M", input_formats=['%Y-%m-%d %H:%M',])
    exam           = ExamNameSerializer()
    student_available_extra_time_end    = serializers.DateTimeField(format="%Y-%m-%d %H:%M", input_formats=['%Y-%m-%d %H:%M',])
    class Meta:
        model = ExamScore
        fields = "__all__" 
        

class ExamScoresSerializer (serializers.ModelSerializer):
    # updated_at                          = serializers.DateTimeField(format="%Y-%m-%d %H:%M", input_formats=['%Y-%m-%d %H:%M',])
    student_available_extra_time_end    = serializers.DateTimeField(format="%Y-%m-%d %H:%M", input_formats=['%Y-%m-%d %H:%M',])
    class Meta:
        model = ExamScore
        fields = "__all__"


# ───────────────── آرشیو سال تحصیلی (نمودار پروفایل) ─────────────────
class YearExamRecordSerializer (serializers.ModelSerializer):
    date = serializers.DateTimeField(format="%Y-%m-%d %H:%M", required=False)
    class Meta:
        model = YearExamRecord
        fields = ('title', 'headline', 'date', 'score', 'present', 'is_offline')


class YearAssignmentRecordSerializer (serializers.ModelSerializer):
    date = serializers.DateTimeField(format="%Y-%m-%d %H:%M", required=False)
    class Meta:
        model = YearAssignmentRecord
        fields = ('title', 'headline', 'date', 'score', 'present')


class AttendanceRecordSerializer (serializers.ModelSerializer):
    date = serializers.DateField(format="%Y-%m-%d", required=False)
    class Meta:
        model = AttendanceRecord
        fields = ('id', 'group_name', 'session_title', 'date', 'present')


class StudentYearRecordSerializer (serializers.ModelSerializer):
    exam_records       = YearExamRecordSerializer(many=True, read_only=True)
    assignment_records = YearAssignmentRecordSerializer(many=True, read_only=True)
    class Meta:
        model = StudentYearRecord
        fields = (
            'id', 'study_year', 'grade', 'group_name', 'student_type', 'status',
            'exam_average', 'exam_final_average', 'exam_count', 'exam_absent_count',
            'assignment_average', 'assignment_count', 'assignment_absent_count',
            'classroom_absence_count', 'exam_records', 'assignment_records',
        )