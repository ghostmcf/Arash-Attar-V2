from django.urls import path
from . import views

from django.conf.urls.static import static

app_name='ExamsPlatform'
urlpatterns = [
    path('', views.index , name='index'),
    path('exam/<uuid:examnum>', views.ExamView , name='exampage'),
    path('exam/<uuid:examnum>/inchange/<str:req_type>', views.InExamChangeView , name='inexamchange'),
    path('exam/<uuid:examnum>/cal/<str:command>', views.question_cal , name='questioncal')
]
        
