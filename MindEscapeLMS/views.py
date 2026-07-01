from django.contrib.auth import login
from rest_framework.response import Response
from rest_framework.permissions import AllowAny,IsAuthenticated,IsAdminUser
from rest_framework.views import APIView
from .serializers import StudentUserSerializer
from django.contrib.auth.models import User
from rest_framework import generics
from knox.views import LoginView as KnoxLoginView, LogoutView as KnoxLogoutView, LogoutAllView as KnoxLogoutAllView
from .auth import SessionTrackingTokenAuthentication
from rest_framework import status
from drf_spectacular.utils import extend_schema, extend_schema_view
from drf_spectacular.types import OpenApiTypes
from .serializers import LoginSerializer
from .totp import totp_required_for, get_confirmed_device, user_payload
# Create your views here.


@extend_schema_view(post=extend_schema(request=LoginSerializer, responses=OpenApiTypes.OBJECT))
class LoginView(KnoxLoginView):
    """ورودِ دو‌مرحله‌ای با پشتیبانی TOTP (اجباری فقط برای staff/superuser).

    مرحله ۱: {username, password}
      - کاربر عادی/دانش‌آموز → توکن بلافاصله صادر می‌شود.
      - staff/superuser بدونِ دستگاهِ تأییدشده → {"otp_setup_required": true} (بدون توکن).
      - staff/superuser با دستگاه، بدونِ کد → {"otp_required": true} (بدون توکن).
    مرحله ۲: {username, password, otp_token}
      - کدِ درست → توکن صادر می‌شود؛ کدِ غلط → خطای ۴۰۰.
    """
    permission_classes = (AllowAny,)
    authentication_classes = ()

    def post(self, request, format=None):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        if totp_required_for(user):
            device = get_confirmed_device(user)
            if device is None:
                # اجباری است ولی هنوز فعال نشده → فرانت باید کاربر را به setup ببرد
                return Response({"otp_setup_required": True}, status=status.HTTP_200_OK)
            otp_token = (request.data.get("otp_token") or "").strip()
            if not otp_token:
                return Response({"otp_required": True}, status=status.HTTP_200_OK)
            if not device.verify_token(otp_token):
                return Response({"detail": "کد تأیید دو‌مرحله‌ای نادرست است."},
                                status=status.HTTP_400_BAD_REQUEST)

        login(request, user)
        return super().post(request, format)

    def get_post_response_data(self, request, token, instance):
        # ثبتِ نشستِ فعال برای این توکنِ تازه (پنل دستگاه‌های فعال). نباید لاگین را بشکند.
        try:
            from StudentsInfo.session_tracking import record_login
            record_login(request, instance)
        except Exception:
            pass
        # پاسخِ پیش‌فرضِ knox ({expiry, token}) را با اطلاعات کاربر غنی می‌کنیم تا فرانت
        # بدون یک درخواستِ اضافه بداند کاربر کیست و چه نقشی دارد.
        data = super().get_post_response_data(request, token, instance)
        data["user"] = user_payload(request.user)
        return data

# Class based view to Get User Details using Token Authentication
class UserDetailAPI(APIView):
    authentication_classes = [SessionTrackingTokenAuthentication]
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
# authentication_classes صریحاً روی زیرکلاسِ ما ست می‌شود تا اسکیمای امنیتی یکدست بماند
# (وگرنه این ویوها knox.auth.TokenAuthentication را می‌آورند و تداخلِ نام رخ می‌دهد).
class LogoutView(KnoxLogoutView):
    authentication_classes = (SessionTrackingTokenAuthentication,)

    @extend_schema(request=None, responses=OpenApiTypes.OBJECT)
    def post(self, request, format=None):
        return super().post(request, format)


class LogoutAllView(KnoxLogoutAllView):
    authentication_classes = (SessionTrackingTokenAuthentication,)

    @extend_schema(request=None, responses=OpenApiTypes.OBJECT)
    def post(self, request, format=None):
        return super().post(request, format)
      