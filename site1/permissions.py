from rest_framework.permissions import BasePermission


class IsSuperUser(BasePermission):
    """
    فقط ابرکاربر (is_superuser).
    برای اندپوینت‌های بسیار حساس که حتی staff (ادمین معمولی) هم نباید دسترسی داشته باشد:
    بایگانی سال، تغییر رمز حساب‌های ویژه، ساخت اکانت staff، و schema/Swagger.
    """
    message = "Only superusers are allowed to perform this action."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)
