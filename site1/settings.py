import os
from pathlib import Path

import logging
import jdatetime
from datetime import datetime
from pytz import timezone as tz

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-(*x+aa&c41r1b28mgq3!ax6-)p!2r4-2ntu7a=%2^ez5tt+r+a'

# SECURITY WARNING: don't run with debug turned on in production!
# DEBUG = True
DEBUG = False

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    "ExamsPlatform.apps.ExamsplatformConfig",
    "StudentsInfo.apps.StudentsinfoConfig",
    "ClassroomsPlatform.apps.ClassroomsplatformConfig",
    "AssignmentPlatform.apps.AssignmentplatformConfig",
    "Frontend.apps.FrontendConfig",
    "ManagementApp.apps.ManagementappConfig",
    'jazzmin',
    'django_crontab',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders', 
    # 'drf_yasg',
    'drf_spectacular',
    'drf_spectacular_sidecar',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',  
]

ROOT_URLCONF = 'site1.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['./templates',],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'site1.wsgi.application'

REST_FRAMEWORK ={
    'DEFAULT_AUTHENTICATION_CLASSES':(
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES':(
        'rest_framework.permissions.IsAuthenticated',        
        # 'rest_framework.permissions.AllowAny',
    ),
    'DEFAULT_FILTER_BACKENDS':(
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    # 'DEFAULT_PAGINATION_CLASS':'rest_framework.pagination.LimitOffsetPagination','PAGE_SIZE':10
    'DEFAULT_PAGINATION_CLASS':'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE':10,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

### Normal DB Configs

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'arashat1_db',
        'USER': 'arashat1_me',
        'PASSWORD': 's89tqP~#T%M$M{-]',
        'HOST': '127.0.0.1',
        'PORT': '3306',
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET NAMES 'utf8mb4' COLLATE 'utf8mb4_unicode_ci', sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}



CRONJOBS = [
    ('*/0 * * * *', 'ExamsPlatform.exam_release')
]
# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    # {
    #     'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    # },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    # },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    # },
]

CORS_ORIGIN_WHITELIST = [
     'http://localhost:3000',
    #  'http://127.0.0.1:8000/'
]
CORS_ALLOWED_ORIGINS = [
    "https://www.arash-attar.com",
    "https://arash-attar.com",
    "https://api.arash-attar.com",
    'http://localhost:3000',
]
# CSRF_TRUSTED_ORIGINS = [
#     'https://arash-attar.com',
#     'https://www.arash-attar.com',
#     'https://api.arash-attar.com',
# ]

FTPS_HOST = '176.65.241.163'
FTPS_PORT = 21
FTPS_USER = 'arashat2'
FTPS_PASSWORD = 'k!!Fc005Em5PUx'
FTPS_BASE_URL = 'https://center.arash-attar.com'


           
JALALI_DATE_DEFAULTS = {
   'Strftime': {
        'date': '%y/%m/%d',
        'datetime': '%H:%M:%S _ %y/%m/%d',
    },
    'Static': {
        'js': [
            'admin/js/django_jalali.min.js',
        ],
        'css': {
            'all': [
                'admin/jquery.ui.datepicker.jalali/themes/base/jquery-ui.min.css',
            ]
        }
    },
}


# SWAGGER_SETTINGS = {
#         'SECURITY_DEFINITIONS': {
#             'api_key':{
#                 'type': 'apiKey',
#                 'in': 'header',
#                 'name': 'Authorization',
#             }
#         }
# }

SPECTACULAR_SETTINGS = {
    'TITLE': 'Snippets API',
    'VERSION': 'v1',
    # امنیت پیش‌فرض برای همه‌ی اندپوینت‌ها (همون API Key در هدر Authorization)
    'SECURITY': [{'apiKeyAuth': []}],
    'SECURITY_SCHEMES': {
        'apiKeyAuth': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
        }
    },
    # اگر UI فقط برای ادمین‌ها باشه:
    # 'SERVE_PERMISSIONS': ['rest_framework.permissions.IsAdminUser'],
    # اگر JSON اسکیما رو نمی‌خوای داخل UI نمایش بده:
    # 'SERVE_INCLUDE_SCHEMA': False,
}

LOGIN_REDIRECT_URL = '/accounts/'
# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Tehran'

USE_I18N = True

USE_TZ = True


## Security
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE =True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SECURE_SSL_REDIRECT = True
##
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_HSTS_SECONDS = 15768000
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = 'DENY'

##

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/



class JalaliFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        # زمان UTC رکورد
        dt = datetime.fromtimestamp(record.created)
        # تایم‌زون واقعی (مثلاً تهران)
        dt = dt.astimezone(tz("Asia/Tehran"))
        # تبدیل به جلالی
        jdt = jdatetime.datetime.fromgregorian(datetime=dt)
        return jdt.strftime("%Y-%m-%d %H:%M:%S")

class MaxLevelFilter(logging.Filter):
    """اجازه میده لاگ‌هایی که سطحشون <= level مشخصه رد بشن"""
    def __init__(self, level):
        self.level = level
    def filter(self, record):
        return record.levelno <= self.level


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'max_info': {
            '()': MaxLevelFilter,
            'level': logging.WARNING,  # یعنی INFO و WARNING رد میشن، ERROR نه
        },
    },
    'formatters': {
        'custom': {
            '()': JalaliFormatter,
            'format': '%(asctime)s | %(levelname)s | %(message)s',
        },
    },
    'handlers': {
        'upload_success': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'upload_success.log'),
            'formatter': 'custom',
            'encoding': 'utf-8',
            'filters': ['max_info'],  # فقط INFO و WARNING
        },
        'upload_error': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'upload_error.log'),
            'formatter': 'custom',
            'encoding': 'utf-8',
        },
        'cleanup_log': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'orphan_cleanup.log'),
            'formatter': 'custom',
            'encoding': 'utf-8',
        },
        'sms_log': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'sms.log'),
            'formatter': 'custom',
            'encoding': 'utf-8',
        },
        'admin_log': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'admin.log'),
            'formatter': 'custom',
            'encoding': 'utf-8',
        },
        'student_assignment_log': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'student_assignment.log'),
            'formatter': 'custom',
            'encoding': 'utf-8',
        },
        'management_log': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'management.log'),
            'formatter': 'custom',
            'encoding': 'utf-8',
        },
    },
    'loggers': {
        'upload_manager': {
            'handlers': ['upload_success', 'upload_error'],
            'level': 'INFO',
            'propagate': False,
        },
        'orphan_cleanup': {  
            'handlers': ['cleanup_log'],
            'level': 'INFO',
            'propagate': False,
        },
        'sms_manager': {
            'handlers': ['sms_log'],
            'level': 'INFO',
            'propagate': False,
        },
        'admins_manager': {
            'handlers': ['admin_log'],
            'level': 'INFO',
            'propagate': False,
        },
        'student_assignment': {
            'handlers': ['student_assignment_log'],
            'level': 'INFO',
            'propagate': False,
        },
        'management_logger': {
            'handlers': ['management_log'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}


DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 10 MB, adjust as needed
FILE_UPLOAD_MAX_MEMORY_SIZE = 52428800
# STATIC_URL = '/static/'
STATIC_URL = '/Collected/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'Storage/staticfiles')

MEDIA_ROOT = os.path.join(BASE_DIR, 'Storage')
MEDIA_URL = '/Storage/'

TEMP_UPLOAD_DIR = os.path.join(MEDIA_ROOT, 'uploads', 'tmp')

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
