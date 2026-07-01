import os
from pathlib import Path

import logging
import jdatetime
from datetime import datetime, timedelta
from pytz import timezone as tz
# from decouple import config
from decouple import Config, RepositoryEnv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

default_env = BASE_DIR / ".env"
server_env = Path.home() / ".env"

if default_env.exists():
    config = Config(RepositoryEnv(default_env))
elif server_env.exists():
    config = Config(RepositoryEnv(server_env))
else:
    raise FileNotFoundError(".env file not found")


# SECURITY WARNING: keep the secret key used in production secret!
# از فایل .env خوانده می‌شود (در گیت نیست). نمونه: .env.example
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

# دامنه‌ی اصلی و همه‌ی ساب‌دامین‌ها (نقطه‌ی ابتدایی یعنی wildcard ساب‌دامین) + توسعه‌ی محلی
ALLOWED_HOSTS = ['.arash-attar.com', 'localhost', '127.0.0.1']


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
    'knox',
    'axes',
    'corsheaders',
    # 'drf_yasg',
    'drf_spectacular',
    'drf_spectacular_sidecar',
    # TOTP دو‌مرحله‌ای (فقط API؛ اجباری برای staff/superuser) — هر اپ Authenticator
    'django_otp',
    'django_otp.plugins.otp_totp',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # CorsMiddleware باید تا حد امکان بالا و قبل از CommonMiddleware باشد
    'corsheaders.middleware.CorsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # AxesMiddleware باید آخر باشد (بعد از AuthenticationMiddleware)
    'axes.middleware.AxesMiddleware',
]

# ضدِ brute-force (django-axes) — هم لاگین ادمین جنگو (/accounts/) هم لاگین API
AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',          # باید اول باشد
    'django.contrib.auth.backends.ModelBackend',
]
AXES_FAILURE_LIMIT = 5                                # بعد از ۵ تلاش ناموفق
AXES_COOLOFF_TIME = 1                                 # قفل به مدت ۱ ساعت
AXES_RESET_ON_SUCCESS = True                          # ورود موفق شمارنده را صفر می‌کند
# قفل بر اساس ترکیب (نام‌کاربری + IP) تا دانش‌آموزانِ پشتِ یک IP مشترک (وای‌فای مرکز)
# به‌خاطر اشتباه یک نفر قفل نشوند، ولی حمله‌ی brute-force روی یک حساب مسدود شود.
AXES_LOCKOUT_PARAMETERS = [["username", "ip_address"]]
AXES_LOCKOUT_TEMPLATE = None                          # پاسخ پیش‌فرض ۴۲۹/۴۰۳
# IP کاربر را django-ipware از X-Forwarded-For می‌خواند (سازگار با پراکسی cPanel).

ROOT_URLCONF = 'MindEscapeLMS.urls'

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

WSGI_APPLICATION = 'MindEscapeLMS.wsgi.application'

REST_FRAMEWORK ={
    'DEFAULT_AUTHENTICATION_CLASSES':(
        # Knox + ردیابیِ نشست (زیرکلاسِ knox.auth.TokenAuthentication که «آخرین استفاده»
        # را برای پنلِ دستگاه‌های فعال آپدیت می‌کند). توکن منقضی‌شونده و هش‌شده در DB.
        'MindEscapeLMS.auth.SessionTrackingTokenAuthentication',
        # 'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES':(
        'rest_framework.permissions.IsAuthenticated',
        # 'rest_framework.permissions.AllowAny',
    ),
    # فقط JSON — رابط گرافیکیِ Browsable API حذف می‌شود (برای هیچ‌کس، حتی لاگین‌کرده).
    # پنل ادمین جنگو (/accounts) و Swagger (فقط superuser) جدا هستند و تحت تأثیر نیستند.
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
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
    # محدودیت نرخ درخواست: جلوگیری از brute-force روی لاگین/ثبت‌نام و سوءاستفاده از پیامک
    'DEFAULT_THROTTLE_CLASSES': (
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ),
    'DEFAULT_THROTTLE_RATES': {
        # ناشناس: محدودیت ضد brute-force روی لاگین/توکن/ثبت‌نام.
        # کلید بر اساس IP است؛ مقدار کمی بالاتر گرفته شده چون گاهی چند دانش‌آموز
        # از یک IP مشترک (وای‌فای مرکز) هم‌زمان وارد می‌شوند.
        'anon': '40/min',
        'user': '600/min',     # کاربر لاگین‌کرده (با حاشیه‌ی امن برای پولینگ حین آزمون)
        'sms': '30/hour',      # اسکوپ اختصاصی اندپوینت‌های ارسال پیامک (هزینه‌بر)
    },
}

# تنظیمات Knox (احراز هویت توکنی امن)
REST_KNOX = {
    # توکن بعد از ۱۲ ساعت منقضی می‌شود؛ با AUTO_REFRESH هر درخواست انقضا را تمدید می‌کند
    # پس کاربر فعال (مثلاً وسط آزمون) قطع نمی‌شود ولی سشن بی‌استفاده می‌میرد.
    'TOKEN_TTL': timedelta(hours=12),
    'AUTO_REFRESH': True,
    'MIN_REFRESH_INTERVAL': 60,
    # None = نامحدود؛ برای محدودکردن تعداد دستگاه فعال هر کاربر عددی بگذارید.
    'TOKEN_LIMIT_PER_USER': None,
    # هدر مثل قبل: Authorization: Token <token>  (سازگاری با فرانت فعلی)
    'AUTH_HEADER_PREFIX': 'Token',
}

### Normal DB Configs

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='127.0.0.1'),
        'PORT': config('DB_PORT', default='3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET NAMES 'utf8mb4' COLLATE 'utf8mb4_unicode_ci', sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    # رمزِ قوی فقط برای حساب‌های staff/superuser الزامی می‌شود (کدملیِ دانش‌آموزان دست‌نخورده).
    {
        'NAME': 'MindEscapeLMS.validators.AdminStrongPasswordValidator',
        'OPTIONS': {'min_length': 10},
    },
]

CORS_ALLOWED_ORIGINS = [
    "https://www.arash-attar.com",
    "https://arash-attar.com",
    "https://api.arash-attar.com",
    'http://localhost:3000',
]
# احراز هویت توکنیِ Knox در هدر Authorization انجام می‌شود (نه کوکی)؛ چون SessionAuthentication
# غیرفعال است، ارسال credentials در درخواست‌های cross-origin لازم نیست و بستنش امن‌تر است.
# (پنل ادمین /accounts/ same-origin است و به CORS ربطی ندارد.)
CORS_ALLOW_CREDENTIALS = False

CSRF_TRUSTED_ORIGINS = [
    'https://arash-attar.com',
    'https://www.arash-attar.com',
    'https://api.arash-attar.com',
]

FTPS_HOST = config('FTPS_HOST')
FTPS_PORT = config('FTPS_PORT', default=21, cast=int)
FTPS_USER = config('FTPS_USER')
FTPS_PASSWORD = config('FTPS_PASSWORD')
FTPS_BASE_URL = config('FTPS_BASE_URL', default='https://center.arash-attar.com')

# SMS.ir (از .env؛ موقع production کلید واقعی را در .env بگذار)
SMS_API_KEY = config('SMS_API_KEY')
SMS_LINE_NUMBER = config('SMS_LINE_NUMBER', default='3000773247')


           
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
    # schema فقط برای superuser سرو شود (دفاع لایه‌ای در کنار permission_classes روی urlها)
    'SERVE_PERMISSIONS': ['MindEscapeLMS.permissions.IsSuperUser'],
    # رفع تداخل نام enumها (جنسیت/پایه در چند مدل choices یکسان دارند → یک نام واحد)
    'ENUM_NAME_OVERRIDES': {
        'StudentGenderEnum': [('پسر', 'پسر'), ('دختر', 'دختر')],
        'StudentGradeEnum': [('دهم', 'دهم'), ('یازدهم', 'یازدهم'), ('دوازدهم', 'دوازدهم')],
    },
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


# ## Security
# تنظیماتی که در هر حالتی امن‌اند (سازگار با dev و prod)
SECURE_CONTENT_TYPE_NOSNIFF = True          # جلوگیری از MIME sniffing
X_FRAME_OPTIONS = 'DENY'                     # جلوگیری از clickjacking
SESSION_COOKIE_HTTPONLY = True              # کوکی سشن از دسترس جاوااسکریپت خارج
SESSION_EXPIRE_AT_BROWSER_CLOSE = True      # پایان سشن با بستن مرورگر
SECURE_REFERRER_POLICY = 'same-origin'

# تنظیمات مخصوص production (فقط وقتی DEBUG=False) تا توسعه‌ی محلی روی HTTP نشکند
if not DEBUG:
    SECURE_SSL_REDIRECT = True               # ریدایرکت اجباری به HTTPS
    SESSION_COOKIE_SECURE = True             # کوکی سشن فقط روی HTTPS
    CSRF_COOKIE_SECURE = True                # کوکی CSRF فقط روی HTTPS
    SECURE_HSTS_SECONDS = 31536000           # یک سال HSTS
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    # چون پشت پراکسی/پسنجر هستیم، هدر فوروارد پروتکل را به Django می‌شناسانیم
    # (نیازمند ست‌شدن X-Forwarded-Proto توسط وب‌سرور؛ در صورت نبود این هدر، این خط را غیرفعال کنید)
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

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


# کرون‌ها (django_crontab). روی سرور با `python manage.py crontab add` فعال می‌شوند.
# هر شب ساعت ۳:۳۰ توکن‌های Knox منقضی‌شده پاک می‌شوند.
CRONJOBS = [
    ('30 3 * * *', 'django.core.management.call_command', ['cleanup_tokens']),
]


JAZZMIN_SETTINGS = {
    "site_title": "By MindEscape",
    "site_header": "Attar LMS Control Panel",
    "show_ui_builder": True,
    "copyright": "<a href='https://mindescape.co'>MindEscape</a> & Amir Hadizade",
    "site_logo": "branding/mlogo.png",
    "site_logo_classes": "img-square",
    "site_icon": "branding/fav-ico.png", 
}

JAZZMIN_UI_TWEAKS = {
    "theme": "simplex",
    "dark_mode_theme": "darkly",
    "navbar_small_text": True,
    "footer_small_text": True,
    "body_small_text": False,
    "brand_small_text": True,
}


DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50 MB, adjust as needed
FILE_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50 MB
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


# از فونت 
# branding\font\IRANSansWeb_Medium.ttf
# استفاده میکنم

# اینا هم تنظیمات داخل setting پروژه 
# STATIC_URL = '/Collected/static/'
# STATIC_ROOT = os.path.join(BASE_DIR, 'Storage/staticfiles')

# MEDIA_ROOT = os.path.join(BASE_DIR, 'Storage')
# MEDIA_URL = '/Storage/'
# همچنین DEBUG=False