from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from rest_framework.decorators import api_view
from rest_framework.response import Response
from . import models ,serializers
from ManagementApp.serializers import UserSerializer
from rest_framework import status,viewsets
from rest_framework.permissions import IsAuthenticated,IsAdminUser
from rest_framework.decorators import api_view,permission_classes
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from knox.models import AuthToken
# Create your views here.
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, inline_serializer
from drf_spectacular.types import OpenApiTypes
from rest_framework import serializers as rfs



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def index (request ):
    try:
        a=request.user.studentuser
    except:
        return Response({"message":"You are not allowed"}, status=status.HTTP_403_FORBIDDEN)
    else:
        return Response({"Student":serializers.StudentUserSerializer(request.user.studentuser).data,"StudentName":{"firstname":request.user.first_name,"lastname":request.user.last_name}}) 

@api_view(['GET'])
@permission_classes([IsAuthenticated])
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

    @extend_schema(
        request=inline_serializer(name='ChangePasswordRequest', fields={
            'old_password': rfs.CharField(),
            'new_password': rfs.CharField(),
        }),
        responses=OpenApiTypes.OBJECT,
    )
    def post(self, request):
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        if not old_password or not new_password:
            return Response({'status': 'old_password and new_password are required'},
                            status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=request.user.username, password=old_password)
        if not user:
            return Response({'status': 'wrong credentials'}, status=status.HTTP_400_BAD_REQUEST)

        # اعتبارسنجی قدرت رمز جدید
        try:
            validate_password(new_password, user=user)
        except ValidationError as e:
            return Response({'status': 'weak password', 'errors': e.messages},
                            status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        # باطل‌کردن همه‌ی توکن‌های فعال تا کاربر با رمز جدید دوباره لاگین کند
        AuthToken.objects.filter(user=user).delete()
        return Response({'status': 'password changed'}, status=status.HTTP_200_OK)


class ActiveSessionsView(APIView):
    """لیستِ دستگاه‌ها/نشست‌های فعالِ کاربرِ جاری.

    منبعِ حقیقت برای «فعال‌بودن»، توکن‌های زنده‌ی Knox است؛ متادیتای هر توکن از
    TokenSession جوین می‌شود. توکنِ بدونِ متادیتا (مثلاً ساخته‌شده پیش از این قابلیت)
    هم با فیلدهای خالی نمایش داده می‌شود.
    """
    http_method_names = ['get']
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        current = getattr(request.auth, 'pk', None)
        tokens = AuthToken.objects.filter(user=request.user)
        meta = {s.token_digest: s for s in models.TokenSession.objects.filter(user=request.user)}
        data = []
        for t in tokens:
            s = meta.get(t.pk)
            data.append({
                'id': s.id if s else None,
                'token_key': t.token_key,          # پیشوندِ عمومی برای شناسایی (نه خودِ توکن)
                'ip_address': s.ip_address if s else None,
                'device': s.device if s else '',
                'country': s.country if s else '',
                'created': s.created if s else t.created,
                'last_used': s.last_used if s else None,
                'expiry': t.expiry,
                'current': (t.pk == current),
            })
        return Response(data, status=status.HTTP_200_OK)


class RevokeSessionView(APIView):
    """لغوِ یک نشست: حذفِ توکنِ Knox آن دستگاه (کاربر روی آن دستگاه خارج می‌شود)."""
    http_method_names = ['delete']
    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses=OpenApiTypes.OBJECT)
    def delete(self, request, pk):
        try:
            session = models.TokenSession.objects.get(pk=pk, user=request.user)
        except models.TokenSession.DoesNotExist:
            return Response({'message': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)
        # حذفِ توکنِ Knox متناظر (خروجِ آن دستگاه) و سپس ردیفِ نشست
        AuthToken.objects.filter(pk=session.token_digest).delete()
        session.delete()
        return Response({'message': 'Session revoked'}, status=status.HTTP_200_OK)


