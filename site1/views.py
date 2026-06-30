from django.shortcuts import render
from django.contrib.auth import login
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny,IsAuthenticated,IsAdminUser
from rest_framework.views import APIView
from rest_framework.authtoken.serializers import AuthTokenSerializer
from .serializers import StudentUserSerializer
from django.contrib.auth.models import User
# from rest_framework.authentication import TokenAuthentication,SessionAuthentication
from rest_framework import generics
from knox.views import LoginView as KnoxLoginView, LogoutView as KnoxLogoutView, LogoutAllView as KnoxLogoutAllView
from knox.auth import TokenAuthentication
from drf_spectacular.utils import extend_schema, extend_schema_view
from drf_spectacular.types import OpenApiTypes

# Create your views here.


@extend_schema_view(post=extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT))
class LoginView(KnoxLoginView):
    permission_classes = (AllowAny,)
    authentication_classes = ()

    def post(self, request, format=None):
        serializer = AuthTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)
        return super().post(request, format=None)

# Class based view to Get User Details using Token Authentication
class UserDetailAPI(APIView):
    # authentication_classes = [SessionAuthentication, TokenAuthentication]
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        content = {
            'user': str(request.user),  # `django.contrib.auth.User` instance.
            'auth': str(request.auth),  # None
        }
        return Response(content)

#Class based view to register user
class RegisterUserAPIView(generics.CreateAPIView):
  # ثبت‌نام حضوری/اکسلی است؛ ساخت اکانت فقط توسط ادمین (قبلاً AllowAny بود = ثبت‌نام عمومی، ریسک امنیتی)
  permission_classes = (IsAdminUser,)
  serializer_class = StudentUserSerializer


# ساب‌کلاس‌های نازکِ logout فقط برای annotate کردن schema (ویوهای خودِ knox W002 می‌دادند)
class LogoutView(KnoxLogoutView):
    @extend_schema(request=None, responses=OpenApiTypes.OBJECT)
    def post(self, request, format=None):
        return super().post(request, format)


class LogoutAllView(KnoxLogoutAllView):
    @extend_schema(request=None, responses=OpenApiTypes.OBJECT)
    def post(self, request, format=None):
        return super().post(request, format)
      