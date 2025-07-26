from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views


router = DefaultRouter()
router.register('',views.UsersIndex)


app_name='StudentsInfo'

urlpatterns = [
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),
]
urlpatterns += router.urls