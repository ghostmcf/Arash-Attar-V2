from django.urls import path
from . import views
from rest_framework.routers import DefaultRouter
from django.conf import settings
from django.conf.urls.static import static


router = DefaultRouter()
router.register('groups',views.GroupsIndex)
router.register('classrooms',views.ClassroomsIndex)
router.register('assignments',views.AssignmentsIndex,basename='assignment')
router.register('assignment-scores',views.AssignmentScoresIndex)
router.register('exams',views.ExamsIndex)
router.register('exam-scores',views.ExamScoresIndex,basename='examscore')
router.register('questions',views.QuestionsIndex,basename='question')
# router.register('question-banks',views.QuestionBanksIndex)
router.register(r'users',views.UsersIndex)
router.register('directmoney',views.DirectMoneyIndex)
router.register('signedcheck',views.SignedCheckIndex)
router.register('books',views.BooksIndex)
router.register("notifications", views.NotificationViewSet, basename="notification")
router.register(r'smsmanager', views.SMSManagerIndex, basename='smsmanager')


app_name='ManagementApp'
urlpatterns = [
    path('upload-excel/', views.UploadExcelView.as_view(), name='upload-excel'),
    path('change-password/', views.change_user_password, name='change-password'),
    path('zappier/', views.zappier, name='zappier'),
    # path('kick-all/', views.invalidate_authenticated_users, name='kick-logged-users'),
    
]

urlpatterns += router.urls