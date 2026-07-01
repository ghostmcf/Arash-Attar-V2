"""کلاسِ احراز هویتِ Knox با ردیابیِ نشست.

روی هر درخواستِ احرازشده، «آخرین استفاده»ی نشستِ متناظر با توکن را (به‌صورت
throttle‌شده) به‌روز می‌کند. ردیابی هرگز نباید احراز هویت را بشکند، پس در
try/except امن پیچیده شده است.
"""
from knox.auth import TokenAuthentication
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from drf_spectacular.plumbing import build_bearer_security_scheme_object


class SessionTrackingTokenAuthentication(TokenAuthentication):
    def authenticate(self, request):
        result = super().authenticate(request)
        if result is not None:
            _user, auth_token = result
            try:
                from StudentsInfo.session_tracking import touch_session
                touch_session(request, auth_token)
            except Exception:
                pass
        return result


class SessionTrackingKnoxScheme(OpenApiAuthenticationExtension):
    """drf-spectacular اسکیمای امنیتیِ زیرکلاسِ ما را نمی‌شناسد (extensionِ داخلی فقط
    خودِ knox.auth.TokenAuthentication را match می‌کند)؛ اینجا همان اسکیمای Knox را
    برای زیرکلاس ثبت می‌کنیم تا Swagger بدون warning تولید شود."""
    target_class = 'MindEscapeLMS.auth.SessionTrackingTokenAuthentication'
    name = 'knoxApiToken'

    def get_security_definition(self, auto_schema):
        return build_bearer_security_scheme_object(
            header_name='Authorization',
            token_prefix=self.target.authenticate_header(""),
        )
