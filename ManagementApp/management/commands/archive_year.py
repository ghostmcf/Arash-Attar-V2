"""
بایگانی پایان سال تحصیلی — فقط از خط فرمان (SSH)، نه HTTP.
قبل از هر آرشیو، یک بکاپ کاملِ دیتابیس (mysqldump) گرفته می‌شود؛ اگر بکاپ ناموفق باشد، آرشیو انجام نمی‌شود.

نمونه:
    python manage.py archive_year
    python manage.py archive_year --study-year 1403-1404
    python manage.py archive_year --yes            # بدون پرسش تعاملی
    python manage.py archive_year --backup-dir /home/arashat1/backups
"""
import os
import subprocess
from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from ManagementApp.services import archive_academic_year, current_study_year


CONFIRM_WORD = "ARCHIVE"


def backup_mysql(backup_dir=None, study_year=None):
    """بکاپ کاملِ دیتابیس با mysqldump. مسیر فایل را برمی‌گرداند؛ در صورت خطا CommandError."""
    db = settings.DATABASES['default']
    if 'mysql' not in db.get('ENGINE', ''):
        raise CommandError(f"بکاپ خودکار فقط برای MySQL پیاده شده است (engine: {db.get('ENGINE')}).")

    # پیش‌فرض: پوشه‌ی backups کنار پروژه (ساده و قابل‌دسترس)
    backup_dir = backup_dir or os.path.join(settings.BASE_DIR, 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    # اسم خوانا: backup_<سال>_<تاریخ-ساعت>.sql  مثل backup_1403-1404_2026-07-01_14-30.sql
    ts = datetime.now().strftime('%Y-%m-%d_%H-%M')
    year_tag = (study_year or 'year').replace('/', '-').replace(' ', '')
    out_path = os.path.join(backup_dir, f"backup_{year_tag}_{ts}.sql")

    # رمز از طریق MYSQL_PWD تا در لیست پروسه‌ها (argv) دیده نشود
    env = {**os.environ, 'MYSQL_PWD': db.get('PASSWORD', '')}
    cmd = [
        'mysqldump',
        '-h', str(db.get('HOST') or '127.0.0.1'),
        '-P', str(db.get('PORT') or 3306),
        '-u', db['USER'],
        '--single-transaction', '--quick', '--default-character-set=utf8mb4',
        db['NAME'],
    ]
    try:
        with open(out_path, 'wb') as f:
            proc = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, env=env)
    except FileNotFoundError:
        raise CommandError("mysqldump روی سرور یافت نشد؛ آرشیو انجام نشد. (نصبش کن یا مسیرش را در PATH بگذار)")

    if proc.returncode != 0:
        err = proc.stderr.decode(errors='replace')[:800]
        raise CommandError(f"بکاپ ناموفق بود (mysqldump)؛ آرشیو انجام نشد.\n{err}")
    if not os.path.exists(out_path) or os.path.getsize(out_path) == 0:
        raise CommandError("فایل بکاپ خالی است؛ آرشیو انجام نشد.")
    return out_path


class Command(BaseCommand):
    help = "بایگانی پایان سال تحصیلی (با بکاپ اجباری دیتابیس قبل از اجرا). فقط از SSH."

    def add_arguments(self, parser):
        parser.add_argument('--study-year', dest='study_year', default=None,
                            help="سال تحصیلی مثل 1403-1404 (پیش‌فرض: سال جلالی جاری)")
        parser.add_argument('--backup-dir', dest='backup_dir', default=None,
                            help="مسیر ذخیره‌ی بکاپ (پیش‌فرض: <project>/backups)")
        parser.add_argument('--yes', action='store_true',
                            help="بدون پرسش تعاملی ادامه بده")
        parser.add_argument('--skip-backup', action='store_true',
                            help="رد کردن بکاپ (فقط برای تست/محیط توسعه؛ روی production استفاده نکن)")

    def handle(self, *args, **opts):
        study_year = (opts.get('study_year') or '').strip() or current_study_year()

        self.stdout.write(self.style.WARNING(
            f"\n⚠️  این عملیات همه‌ی داده‌ی تحصیلیِ سالِ جاری را برای «{study_year}» بایگانی و سپس پاک می‌کند.\n"
            "    (همه‌ی امتحان‌ها/تکالیف/کلاس‌ها/گروه‌ها حذف و دانش‌آموزها غیرفعال می‌شوند.)\n"
        ))

        # تأیید تعاملی
        if not opts.get('yes'):
            answer = input(f"برای ادامه کلمه‌ی «{CONFIRM_WORD}» را دقیقاً تایپ کنید: ").strip()
            if answer != CONFIRM_WORD:
                raise CommandError("لغو شد (تأیید نادرست).")

        # بکاپ اجباری
        if opts.get('skip_backup'):
            self.stdout.write(self.style.ERROR("⏭️  بکاپ رد شد (--skip-backup). فقط برای محیط تست!"))
        else:
            self.stdout.write("در حال گرفتن بکاپ دیتابیس...")
            path = backup_mysql(opts.get('backup_dir'), study_year=study_year)
            size_mb = os.path.getsize(path) / (1024 * 1024)
            self.stdout.write(self.style.SUCCESS(f"✅ بکاپ گرفته شد: {path} ({size_mb:.1f} MB)"))

        # اجرای آرشیو
        self.stdout.write("در حال بایگانی...")
        result = archive_academic_year(study_year=study_year, actor='cli')
        self.stdout.write(self.style.SUCCESS(
            f"✅ بایگانی انجام شد — سال: {result['study_year']} | دانش‌آموز: {result['students_archived']}"
        ))
