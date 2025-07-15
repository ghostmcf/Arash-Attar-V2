from django.urls import path
from . import views
from rest_framework.routers import DefaultRouter

app_name='ClassroomsPlatform'

router=DefaultRouter()
router.register('', views.ClassroomViewset, basename='classrooms')

urlpatterns = [

]

urlpatterns += router.urls


