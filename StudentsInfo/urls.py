from django.urls import path , include
from rest_framework.routers import DefaultRouter
from . import views


router = DefaultRouter()
router.register('',views.UsersIndex)
# router.register('',views.ChangePasswordView)
# router.register('',views.ChangeAvatarView)

app_name='StudentsInfo'

urlpatterns = [
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    path('change-avatar/', views.ChangeAvatarView.as_view() , name="ChangePassword" ),
    # path('<str:studentnum>/', views.StuSelectorView , name="studentpanel"),
    # path('update-direct-money/', views.update_direct_money_view, name='update_direct_money'),
]
urlpatterns += router.urls