from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework.views import APIView
from .serializers import UserSerializer,RegisterSerializer,StudentUserSerializer
from django.contrib.auth.models import User
from rest_framework.authentication import TokenAuthentication,SessionAuthentication
from rest_framework import generics
from StudentsInfo.models import StudentUser

# Create your views here.

# Class based view to Get User Details using Token Authentication
class UserDetailAPI(APIView):
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        content = {
            'user': str(request.user),  # `django.contrib.auth.User` instance.
            'auth': str(request.auth),  # None
        }
        return Response(content)

#Class based view to register user
class RegisterUserAPIView(generics.CreateAPIView):
  permission_classes = (AllowAny,)
  serializer_class = StudentUserSerializer
      