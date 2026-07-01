from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

from .views import RegisterUserAPIView, LoginView, LogoutView, LogoutAllView
from .permissions import IsSuperUser
from . import totp_api
from StudentsInfo.views import ActiveSessionsView, RevokeSessionView


urlpatterns = [
    # Schema / Swagger / Redoc — فقط superuser
    path('api/schema/', SpectacularAPIView.as_view(permission_classes=[IsSuperUser]), name='schema'),
    path('swagger/', SpectacularSwaggerView.as_view(url_name='schema', permission_classes=[IsSuperUser]), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema', permission_classes=[IsSuperUser]), name='redoc'),

    # احراز هویت (Knox): login توکن می‌دهد، logout/logoutall توکن‌ها را باطل می‌کنند
    path('login', LoginView.as_view(), name='knox_login'),
    path('logout', LogoutView.as_view(), name='knox_logout'),
    path('logoutall', LogoutAllView.as_view(), name='knox_logoutall'),
    path('register', RegisterUserAPIView.as_view()),   # فقط ادمین

    # دستگاه‌های فعال: دیدن نشست‌های خودِ کاربر و لغوِ یک دستگاه
    path('sessions', ActiveSessionsView.as_view(), name='active-sessions'),
    path('sessions/<int:pk>', RevokeSessionView.as_view(), name='revoke-session'),

    # مدیریتِ TOTP (فقط JSON؛ فرانت UI را می‌سازد). اجباری برای staff/superuser.
    path('2fa/setup', totp_api.TOTPSetupView.as_view(), name='totp_setup'),
    path('2fa/confirm', totp_api.TOTPConfirmView.as_view(), name='totp_confirm'),
    path('2fa/status', totp_api.TOTPStatusView.as_view(), name='totp_status'),

    # پنل ادمین جنگو (تنها رابط گرافیکیِ مجاز — برای superuser)
    path('accounts/', admin.site.urls),

    path('exam-platform/', include('ExamsPlatform.urls')),
    path('assignment-platform/', include('AssignmentPlatform.urls')),
    path('student-panel/', include('StudentsInfo.urls')),
    path('classroom/', include('ClassroomsPlatform.urls')),
    path('management/', include('ManagementApp.urls')),
    path('', include('Frontend.urls'), name="dash"),
]

# سرو استاتیک/مدیا فقط در توسعه؛ در production وب‌سرور (cPanel) این کار را می‌کند
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
