from django.urls import path
from . import views

from rest_framework.routers import DefaultRouter

app_name='AssignmentPlatform'


router = DefaultRouter()
router.register('', views.AssignmentViewSet, basename='assignment')

urlpatterns = [
    path('<uuid:assignment_id>/upload/', views.FileUploadView.as_view(), name='file-upload'),
]

urlpatterns += router.urls