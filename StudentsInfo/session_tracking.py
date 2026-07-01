"""کمک‌تابع‌های ردیابیِ نشستِ توکن (پنل «دستگاه‌های فعال»).

هیچ‌کدام از این توابع نباید احراز هویت یا لاگین را بشکنند؛ فراخوان‌ها باید در
try/except امن پیچیده شوند (در MindEscapeLMS/auth.py و LoginView این کار انجام شده).
"""
from datetime import timedelta

from django.utils import timezone

# آپدیتِ «آخرین استفاده» حداکثر هر ۶۰ ثانیه یک‌بار تا هر درخواستِ API یک write نزند
_TOUCH_THROTTLE = timedelta(seconds=60)


def get_client_ip(request):
    """IP واقعی پشت پراکسیِ cPanel از X-Forwarded-For (اولین IP) وگرنه REMOTE_ADDR."""
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def parse_device(user_agent):
    """تشخیصِ سبکِ نوعِ دستگاه + مرورگر از روی User-Agent (بدون وابستگیِ خارجی)."""
    ua = (user_agent or '').lower()
    if not ua:
        return 'Unknown'
    if 'iphone' in ua or 'android' in ua or 'mobile' in ua:
        device = 'Mobile'
    elif 'ipad' in ua or 'tablet' in ua:
        device = 'Tablet'
    else:
        device = 'Desktop'
    # ترتیب مهم است (Edg/Chrome قبل از Safari چون UA سافاری هم Safari دارد)
    if 'edg' in ua:
        browser = 'Edge'
    elif 'opr' in ua or 'opera' in ua:
        browser = 'Opera'
    elif 'chrome' in ua or 'crios' in ua:
        browser = 'Chrome'
    elif 'firefox' in ua or 'fxios' in ua:
        browser = 'Firefox'
    elif 'safari' in ua:
        browser = 'Safari'
    else:
        browser = ''
    return f"{device} - {browser}" if browser else device


def lookup_country(ip):
    """کشور به‌صورت best-effort. اگر GeoIP2 (کتابخانه + دیتابیس mmdb) روی سرور تنظیم
    نشده باشد رشته‌ی خالی برمی‌گرداند؛ هیچ وابستگیِ سختی تحمیل نمی‌شود."""
    if not ip:
        return ''
    try:
        from django.contrib.gis.geoip2 import GeoIP2
        return GeoIP2().country(ip).get('country_name') or ''
    except Exception:
        return ''


def record_login(request, auth_token):
    """هنگام لاگین: ساخت/به‌روزرسانیِ نشست برای توکنِ تازه‌ساخته‌شده."""
    from .models import TokenSession
    ip = get_client_ip(request)
    ua = (request.META.get('HTTP_USER_AGENT') or '')[:2000]
    now = timezone.now()
    TokenSession.objects.update_or_create(
        token_digest=auth_token.pk,
        defaults={
            'user': auth_token.user,
            'token_key': auth_token.token_key,
            'ip_address': ip,
            'user_agent': ua,
            'device': parse_device(ua),
            'country': lookup_country(ip),
            'created': now,
            'last_used': now,
        },
    )


def touch_session(request, auth_token):
    """هر درخواستِ احرازشده: آپدیتِ throttle‌شده‌ی «آخرین استفاده» + IP (یک UPDATE، غالباً no-op)."""
    from .models import TokenSession
    now = timezone.now()
    TokenSession.objects.filter(
        token_digest=auth_token.pk, last_used__lt=now - _TOUCH_THROTTLE
    ).update(last_used=now, ip_address=get_client_ip(request))
