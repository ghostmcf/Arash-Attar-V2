"""حذفِ توکن‌های Knox منقضی‌شده.

Knox فقط هنگام احراز هویتِ خودِ همان کاربر، توکن‌های منقضیِ او را پاک می‌کند؛ پس
توکن‌های کاربرانی که دیگر لاگین نمی‌کنند در دیتابیس می‌مانند. این دستور را با cron
به‌صورت دوره‌ای اجرا کنید تا جدولِ توکن‌ها تمیز بماند:

    python manage.py cleanup_tokens

توکن‌های بدونِ انقضا (expiry=NULL) دست‌نخورده می‌مانند.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from knox.models import AuthToken


class Command(BaseCommand):
    help = "حذف توکن‌های Knox منقضی‌شده (برای اجرای دوره‌ای با cron)."

    def handle(self, *args, **options):
        now = timezone.now()
        expired = AuthToken.objects.filter(expiry__lt=now)
        count = expired.count()
        expired.delete()

        # پاکسازیِ ردیف‌های یتیمِ نشست (توکنشان دیگر وجود ندارد: logout/انقضا/لغو)
        from StudentsInfo.models import TokenSession
        live_digests = AuthToken.objects.values_list('pk', flat=True)
        orphans = TokenSession.objects.exclude(token_digest__in=live_digests)
        orphan_count = orphans.count()
        orphans.delete()

        self.stdout.write(self.style.SUCCESS(
            f"{count} expired knox token(s) + {orphan_count} orphan session(s) deleted."
        ))
