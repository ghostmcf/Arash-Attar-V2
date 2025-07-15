from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from . import models
# from django.utils import timezone

from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from . import models ,serializers
from ManagementApp.serializers import UserSerializer
from rest_framework import status,viewsets
from rest_framework.permissions import IsAuthenticated,IsAdminUser
from rest_framework.decorators import api_view,permission_classes
from rest_framework.views import APIView
from django.contrib.auth import authenticate
# Create your views here.

# from django.http import HttpResponse
# import datetime


@permission_classes([IsAuthenticated])
@api_view(['GET'])
def index (request ):
    try:
        a=request.user.studentuser
    except:
        return Response({"message":"You are not allowed"}, status=status.HTTP_403_FORBIDDEN)
    else:
        return Response({"Student":serializers.StudentUserSerializer(request.user.studentuser).data,"StudentName":{"firstname":request.user.first_name,"lastname":request.user.last_name}}) 

@permission_classes([IsAuthenticated])
@api_view(['GET'])
def StuSelectorView (request ,studentnum):
    selected_student = get_object_or_404(models.StudentUser,pk=studentnum)
    # try:
    #     a=models.StudentUser.get(student_user=studentnum)
    #     # a=mdoels Student_user.get(student_user=studentnum)
    # except:
    #     return Response({"message":"You are not allowed"}, status=status.HTTP_403_FORBIDDEN)
    # else:
    #     return Response({"Student":serializers.StudentUserSerializer(selected_student).data}) 
    return Response({"Student":serializers.StudentUserSerializer(request.user.studentuser).data}) 
    
    
class UsersIndex (viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    http_method_names = ['get']
    permission_classes = [IsAuthenticated]
    def list(self, request):
        permission_classes = [IsAuthenticated]
        queryset = User.objects.all()
        user = get_object_or_404(queryset, pk=request.user.id)
        serializer = UserSerializer(user)
        return Response(serializer.data)
    def retrive(self, request, pk=None):
        permission_classes = [IsAdminUser]
        response = {'message': 'Update function is not offered in this path.'}
        return Response(response, status=status.HTTP_403_FORBIDDEN)


class ChangePasswordView(APIView):
    http_method_names = ['post']
    permission_classes = [IsAuthenticated]
    def post(self, request):
        user = authenticate(username=request.user.username, password=request.data['old_password'])
        if user:
            user.set_password(request.data['new_password'])
            user.save()
            return Response({'status': 'password changed'}, status=status.HTTP_200_OK)
        else:
            return Response({'status': 'wrong credentials'}, status=status.HTTP_400_BAD_REQUEST)        
            
         
class ChangeAvatarView(APIView):
    http_method_names = ['patch']
    permission_classes = [IsAuthenticated]
    def patch(self, request):
        # student = models.StudentUser.objects.get(pk=request.user.id)
        student = request.user.studentuser
        student.avatar = request.data['avatar']
        student.save()
        return Response({'status': 'avatar changed'}, status=status.HTTP_200_OK)

    # return render(request,'index.html')
#user.groups.add(name='groupname')
# my_group = Group.objects.get(name='my_group_name') 
# my_group.user_set.add(your_user)


##############Bug Fix on Null Directmoney "payment_date"
# @permission_classes([IsAuthenticated])
# @api_view(['GET'])
# def update_direct_money_view(request):
#     # Find all DirectMoney records with a null payment_date
#     direct_moneys = models.DirectMoney.objects.filter(payment_date__isnull=True)
#     # Open a file to write the usernames
#     with open('direct_money_usernames.txt', 'w') as file:
#         for direct_money in direct_moneys:
#             # Get the username of the student
#             username = direct_money.student.username

#             # Write the username to the file
#             file.write(f'{username}\n')

#             # Update the payment_date to 2000-01-01
#             direct_money.payment_date = datetime.date(2000, 1, 1)
#             direct_money.save()

#     return HttpResponse("Successfully updated payment_date and stored usernames in direct_money_usernames.txt")
    