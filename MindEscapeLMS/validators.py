"""اعتبارسنجی رمزِ اختصاصیِ حساب‌های مدیریتی.

دانش‌آموزان طبق قرارداد از کدملی به‌عنوان نام‌کاربری/رمز استفاده می‌کنند و نباید
تحت سخت‌گیریِ رمز قوی قرار بگیرند؛ ولی هر حساب staff/superuser (که به پنل ادمین و
داده‌ی حساس دسترسی دارد) باید رمزِ قوی داشته باشد. این ولیدیتور در لیست سراسریِ
AUTH_PASSWORD_VALIDATORS قرار می‌گیرد ولی فقط برای حساب‌های مدیریتی فعال می‌شود،
بنابراین همه‌ی مسیرها (پنل ادمین جنگو، createsuperuser، تغییر رمز API) پوشش داده
می‌شوند بدون اینکه جریانِ رمزِ دانش‌آموزان بشکند.
"""
from django.contrib.auth.password_validation import (
    CommonPasswordValidator,
    MinimumLengthValidator,
    NumericPasswordValidator,
    UserAttributeSimilarityValidator,
)


class AdminStrongPasswordValidator:
    def __init__(self, min_length=10):
        self.min_length = min_length
        self._checks = [
            MinimumLengthValidator(min_length=min_length),
            CommonPasswordValidator(),
            NumericPasswordValidator(),
            UserAttributeSimilarityValidator(),
        ]

    @staticmethod
    def _is_admin(user):
        return bool(user is not None and (
            getattr(user, "is_staff", False) or getattr(user, "is_superuser", False)
        ))

    def validate(self, password, user=None):
        # فقط حساب‌های مدیریتی؛ کاربر عادی/دانش‌آموز → بدون سخت‌گیری
        if not self._is_admin(user):
            return
        for check in self._checks:
            check.validate(password, user)

    def get_help_text(self):
        return (
            "رمز حساب‌های مدیریتی باید حداقل %d کاراکتر، غیرعددیِ صرف، غیرِرایج و "
            "نامرتبط با نام‌کاربری باشد." % self.min_length
        )
