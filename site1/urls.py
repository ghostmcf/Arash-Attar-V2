from django.contrib import admin
from django.urls import path , include, re_path, reverse
from rest_framework.authtoken import views as authtoken 
# from drf_yasg.views import get_schema_view
# from drf_yasg import openapi
from .views import RegisterUserAPIView
from django.conf import settings
from django.conf.urls.static import static
# from onetimelink import urls as onetimelink_urls
from . import views
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView


# from onetimelink import presettings



# schema_view = get_schema_view(
#    openapi.Info(
#       title="Snippets API",
#       default_version='v1',
#       description="Test description",
#       terms_of_service="https://www.google.com/policies/terms/",
#       contact=openapi.Contact(email="contact@snippets.local"),
#       license=openapi.License(name="BSD License"),
#    ),
#    public=True,
#    permission_classes=[permissions.AllowAny],
# )

def get_success_url(self):
    return reverse('profile')

urlpatterns = [
    # re_path('swagger(?P<format>\.json|\.yaml)', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    # re_path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    # re_path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    path('register',RegisterUserAPIView.as_view()),
    path('token-auth', authtoken.obtain_auth_token),
    path('auth', include('rest_framework.urls') ),
    path('accounts/', admin.site.urls),
    path('authentication/', include('django.contrib.auth.urls') ),
    path('exam-platform/', include('ExamsPlatform.urls') ),
    path('assignment-platform/', include('AssignmentPlatform.urls') ),
    path('student-panel/', include('StudentsInfo.urls') ),
    path('classroom/', include('ClassroomsPlatform.urls') ),
    path('', include('Frontend.urls') , name="dash"),
    path('management/',include('ManagementApp.urls')),

    
]

urlpatterns +=  static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns +=  static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# handler404 = 'site1.handler404'