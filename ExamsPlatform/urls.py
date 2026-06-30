from django.urls import path
from . import views

from django.conf.urls.static import static

app_name='ExamsPlatform'
urlpatterns = [
    path('', views.index , name='index'),
    path('exam/<uuid:examnum>', views.ExamView , name='exampage'),
    path('exam/<uuid:examnum>/v2/flow/<str:req_type>', views.exam_flow , name='exam-flow'),
    path('exam/<uuid:examnum>/v2/choice/<str:command>', views.exam_choice , name='exam-choice'),
]
        
