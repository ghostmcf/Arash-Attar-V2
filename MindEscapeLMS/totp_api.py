"""اندپوینت‌های JSON برای مدیریتِ TOTP (بدونِ هیچ صفحه/HTML؛ فرانت UI را می‌سازد).

- POST /2fa/setup   {username, password}            → {otpauth_url, secret}
- POST /2fa/confirm {username, password, otp_token}  → {token, expiry, user}
- GET  /2fa/status  (با توکن)                        → {enabled, required}

setup/confirm با یوزر/پسورد دوباره احراز هویت می‌کنند (چون در جریانِ لاگین‌اند و هنوز
توکن صادر نشده). سیاست: فقط staff/superuser مجازند؛ کاربران عادی TOTP ندارند.
"""
import base64

from django.contrib.auth import login as dj_login
from knox.models import AuthToken
from knox.settings import knox_settings
from rest_framework import status
from rest_framework.fields import DateTimeField
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django_otp.plugins.otp_totp.models import TOTPDevice
from drf_spectacular.utils import extend_schema, inline_serializer
from drf_spectacular.types import OpenApiTypes
from rest_framework import serializers as rfs

from .serializers import LoginSerializer
from .totp import totp_required_for, get_confirmed_device, user_payload


def _issue_token(request, user):
    """صدور توکنِ Knox پس از احراز هویتِ کاملِ دو‌مرحله‌ای (+ ثبتِ نشست)."""
    dj_login(request, user)   # سیگنالِ user_logged_in (ریست axes + last_login)
    instance, token = AuthToken.objects.create(user)
    try:
        from StudentsInfo.session_tracking import record_login
        record_login(request, instance)
    except Exception:
        pass
    expiry = (DateTimeField(format=knox_settings.EXPIRY_DATETIME_FORMAT)
              .to_representation(instance.expiry) if instance.expiry else None)
    return Response({"expiry": expiry, "token": token, "user": user_payload(user)},
                    status=status.HTTP_200_OK)


class TOTPSetupView(APIView):
    """ساختِ دستگاهِ TOTP تأییدنشده و بازگرداندنِ otpauth_url + secret برای نمایشِ QR در فرانت."""
    permission_classes = ()
    authentication_classes = ()

    @extend_schema(
        request=LoginSerializer,
        responses=OpenApiTypes.OBJECT,
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        if not totp_required_for(user):
            return Response({"detail": "TOTP فقط برای حساب‌های مدیریتی است."},
                            status=status.HTTP_403_FORBIDDEN)
        if get_confirmed_device(user) is not None:
            return Response({"detail": "TOTP از قبل فعال است."},
                            status=status.HTTP_400_BAD_REQUEST)

        device = (TOTPDevice.objects.filter(user=user, confirmed=False).first()
                  or TOTPDevice.objects.create(user=user, name='default', confirmed=False))
        secret = base64.b32encode(device.bin_key).decode('utf-8')
        return Response({"otpauth_url": device.config_url, "secret": secret},
                        status=status.HTTP_200_OK)


class TOTPConfirmView(APIView):
    """تأییدِ دستگاهِ TOTP با کد و صدورِ توکن (پایانِ فعال‌سازی = لاگینِ کامل)."""
    permission_classes = ()
    authentication_classes = ()

    @extend_schema(
        request=inline_serializer(name='TOTPConfirmRequest', fields={
            'username': rfs.CharField(),
            'password': rfs.CharField(),
            'otp_token': rfs.CharField(help_text='کد ۶ رقمیِ اپ Authenticator'),
        }),
        responses=OpenApiTypes.OBJECT,
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        if not totp_required_for(user):
            return Response({"detail": "TOTP فقط برای حساب‌های مدیریتی است."},
                            status=status.HTTP_403_FORBIDDEN)

        device = TOTPDevice.objects.filter(user=user, confirmed=False).first()
        if device is None:
            return Response({"detail": "ابتدا setup را صدا بزنید."},
                            status=status.HTTP_400_BAD_REQUEST)

        otp_token = (request.data.get("otp_token") or "").strip()
        if not device.verify_token(otp_token):
            return Response({"detail": "کد نادرست است."}, status=status.HTTP_400_BAD_REQUEST)

        device.confirmed = True
        device.save()
        # حذفِ دستگاه‌های تأییدنشده‌ی احتمالیِ باقی‌مانده
        TOTPDevice.objects.filter(user=user, confirmed=False).exclude(pk=device.pk).delete()
        return _issue_token(request, user)


class TOTPStatusView(APIView):
    """وضعیتِ TOTP کاربرِ لاگین‌کرده."""
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        return Response({
            "enabled": get_confirmed_device(request.user) is not None,
            "required": totp_required_for(request.user),
        }, status=status.HTTP_200_OK)
