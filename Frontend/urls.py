from django.urls import path,include
from . import views

app_name='Frontend'
urlpatterns = [
    path('dashboard/exam-box', views.ExamBox , name='user-profile'),
    path('dashboard/classroom-box', views.ClassroomBox , name='user-profile'),
    path('dashboard/assignment-box', views.AssignmentBox , name='user-profile'),
    path('dashboard/userinfo-box', views.UserInfoBox , name='user-profile'),
]