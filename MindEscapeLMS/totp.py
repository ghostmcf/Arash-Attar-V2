"""منطقِ مشترکِ TOTP.

سیاست: احراز هویتِ دو‌مرحله‌ای فقط و فقط برای حساب‌های staff/superuser اجباری است؛
برای کاربران عادی (دانش‌آموزان) اصلاً اعمال نمی‌شود.
"""
from django_otp.plugins.otp_totp.models import TOTPDevice


def totp_required_for(user):
    """آیا این کاربر باید TOTP داشته باشد؟ (فقط staff/superuser)"""
    return bool(user and (user.is_staff or user.is_superuser))


def get_confirmed_device(user):
    """دستگاهِ TOTP تأییدشده‌ی کاربر (یا None)."""
    return TOTPDevice.objects.filter(user=user, confirmed=True).first()


def has_confirmed_device(user):
    return TOTPDevice.objects.filter(user=user, confirmed=True).exists()


def user_payload(user):
    """اطلاعاتِ کاربر که در پاسخِ لاگین/تأیید به فرانت برمی‌گردد."""
    return {
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_staff": user.is_staff,
        "is_superuser": user.is_superuser,
        "role": "superuser" if user.is_superuser else ("staff" if user.is_staff else "student"),
    }
