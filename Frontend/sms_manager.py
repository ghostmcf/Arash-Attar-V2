"""
سرویس واحد پیامک (SMS.ir): کلاینت، helperها، و پنل ارسال نمره/پیام دلخواه.

- ارسال نمره: قالب تأییدشده، per-person (پارامترها شخصی‌اند) با send_verify_code.
- ارسال دلخواه: send_bulk_sms در تکه‌های حداکثر ۱۰۰ شماره در هر درخواست.
- انتخاب شماره: مادر/پدر/هردو با fallback به شماره‌ی موجود؛ آخرین مقصد در StudentUser
  ذخیره می‌شود (به‌جز پیام دلخواه که مقصد پیش‌فرض را تغییر نمی‌دهد).
"""
import logging
import re
from statistics import mean

import jdatetime
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from sms_ir import SmsIr

from ExamsPlatform.models import Exam, ExamScore, ExamScoreOffline
from AssignmentPlatform.models import Assignment, AssignmentScore
from StudentsInfo.models import StudentUser

# ====== تنظیمات SMS.ir (کلید از .env → settings.SMS_*) ======
API_KEY = settings.SMS_API_KEY
LINE_NUMBER = settings.SMS_LINE_NUMBER
TEMPLATE_ID_ASSIGNMENT = 782660   # قالب تکلیف
TEMPLATE_ID_EXAM       = 605360   # قالب امتحان
SMS_CHUNK = 100                   # سقف شماره در هر درخواست bulk

sms = SmsIr(API_KEY, LINE_NUMBER)
log = logging.getLogger('sms_manager')


# ====== Helpers ======
def jalali(d):
    d = d or timezone.now()
    if timezone.is_aware(d):
        d = timezone.localtime(d)
    return jdatetime.datetime.fromgregorian(datetime=d).strftime("%Y/%m/%d")


def valid_phone(p):
    return bool(p) and bool(re.fullmatch(r"09\d{9}", p.strip()))


def full_name(user: User):
    fn, ln = (user.first_name or "").strip(), (user.last_name or "").strip()
    return f"{fn} {ln}".strip() or user.username


_re_series = re.compile(r"سری\s*(\d+)", re.IGNORECASE)


def series_assignment(a: Assignment) -> int:
    if a.AssignmentName:
        m = _re_series.search(a.AssignmentName)
        if m:
            try:
                return int(m.group(1))
            except ValueError:
                pass
    ids = list(Assignment.objects
               .filter(assignment_group=a.assignment_group)
               .order_by('assignment_available_time_start', 'assignment_creation_time', 'assignment_id')
               .values_list('assignment_id', flat=True))
    return (ids.index(a.assignment_id) + 1) if a.assignment_id in ids else 1


def series_exam(e: Exam) -> int:
    if e.ExamName:
        m = _re_series.search(e.ExamName)
        if m:
            try:
                return int(m.group(1))
            except ValueError:
                pass
    ids = list(Exam.objects
               .filter(exam_group=e.exam_group)
               .order_by('exam_available_time_start', 'exam_creation_time', 'exam_id')
               .values_list('exam_id', flat=True))
    return (ids.index(e.exam_id) + 1) if e.exam_id in ids else 1


def _clean(p):
    return p.strip() if (p and valid_phone(p)) else None


def resolve_numbers(su, target):
    """su: StudentUser|None ، target: 'mother'|'father'|'both'.
    خروجی (numbers, used_target) با fallback به شماره‌ی موجود."""
    if not su:
        return [], None
    mother = _clean(su.mother_number)
    father = _clean(su.father_number)
    if target == 'father':
        if father: return [father], 'father'
        if mother: return [mother], 'mother'
    elif target == 'both':
        nums = [n for n in (mother, father) if n]
        used = 'both' if (mother and father) else ('mother' if mother else ('father' if father else None))
        return nums, used
    else:  # mother (پیش‌فرض)
        if mother: return [mother], 'mother'
        if father: return [father], 'father'
    return [], None


# ====== جمع‌آوری نمرات ======
def _exam_score_map(exam):
    """{user_id: {'score','present','user'}} از آنلاین + آفلاین."""
    out = {}
    for es in ExamScore.objects.filter(exam=exam).select_related('exam_average_reffer__user'):
        u = es.exam_average_reffer.user
        out[u.id] = {'score': es.score, 'present': es.exam_peresence, 'user': u}
    for eso in ExamScoreOffline.objects.filter(exam=exam).select_related('exam_average_reffer__user'):
        u = eso.exam_average_reffer.user
        out.setdefault(u.id, {'score': eso.score, 'present': eso.exam_peresence, 'user': u})
    return out


def _exam_group_avg(exam):
    scores = [float(es.score) for es in ExamScore.objects.filter(exam=exam, exam_peresence=True, countable=True) if es.score is not None]
    scores += [float(eso.score) for eso in ExamScoreOffline.objects.filter(exam=exam, exam_peresence=True, countable=True) if eso.score is not None]
    return round(mean(scores), 2) if scores else 0.0


def _assignment_score_map(assignment):
    out = {}
    for a in AssignmentScore.objects.filter(assignment=assignment).select_related('assignment_average_reffer__user'):
        u = a.assignment_average_reffer.user
        out[u.id] = {'score': a.score, 'present': a.assignment_presence, 'user': u}
    return out


def _assignment_group_avg(assignment):
    scores = [float(a.score) for a in AssignmentScore.objects.filter(assignment=assignment, assignment_presence=True) if a.score is not None]
    return round(mean(scores), 2) if scores else 0.0


def _recipient_rows(score_map):
    rows = []
    sus = {su.student_user_id: su for su in StudentUser.objects.filter(student_user_id__in=score_map.keys())}
    for uid, info in score_map.items():
        u = info['user']
        su = sus.get(uid)
        rows.append({
            'user_id': u.id, 'username': u.username, 'name': full_name(u),
            'score': float(info['score'] or 0), 'present': info['present'],
            'has_mother': bool(su and _clean(su.mother_number)),
            'has_father': bool(su and _clean(su.father_number)),
            'last_sms_target': su.last_sms_target if su else None,
        })
    rows.sort(key=lambda r: r['name'])
    return rows


def exam_recipients(exam):
    return {'sms_permission': exam.sms_permission, 'sms_sent': exam.sms_sent,
            'recipients': _recipient_rows(_exam_score_map(exam))}


def assignment_recipients(assignment):
    return {'sms_permission': assignment.sms_permission, 'sms_sent': assignment.sms_sent,
            'recipients': _recipient_rows(_assignment_score_map(assignment))}


# ====== ارسال نمره ======
def _select_targets(score_map, user_ids):
    if user_ids in (None, 'all', '') or not user_ids:
        return list(score_map.keys())
    out = []
    for uid in user_ids:
        try:
            uid = int(uid)
        except (TypeError, ValueError):
            continue
        if uid in score_map:
            out.append(uid)
    return out


def _send_scores(score_map, targets, template_id, build_params, sus_cache, target):
    sent, failed, skipped = 0, [], []
    for uid in targets:
        info = score_map[uid]
        u = info['user']
        su = sus_cache.get(uid)
        name = full_name(u)
        numbers, used = resolve_numbers(su, target)
        if not numbers:
            skipped.append({'user': u.username, 'name': name, 'reason': 'no_valid_number'})
            continue
        params = build_params(name, float(info['score'] or 0))
        ok_any = False
        for number in numbers:
            try:
                resp = sms.send_verify_code(number=number, template_id=template_id, parameters=params) or {}
                if int(resp.get('status', 0) or 0) == 1:
                    ok_any = True
                else:
                    failed.append({'user': u.username, 'number': number, 'msg': resp.get('message', '')})
            except Exception as e:
                failed.append({'user': u.username, 'number': number, 'msg': str(e)})
        if ok_any:
            sent += 1
            if su and used:
                su.last_sms_target = used
                su.save(update_fields=['last_sms_target'])
    return sent, failed, skipped


def send_exam_scores(exam, user_ids, target):
    score_map = _exam_score_map(exam)
    targets = _select_targets(score_map, user_ids)
    sus_cache = {su.student_user_id: su for su in StudentUser.objects.filter(student_user_id__in=score_map.keys())}
    avg = _exam_group_avg(exam)
    serie = series_exam(exam)
    date_str = jalali(exam.exam_available_time_end or exam.exam_creation_time)

    def build(name, score):
        return [
            {"name": "ESERIE", "value": str(serie)},
            {"name": "USERNAME", "value": name},
            {"name": "ESCORE", "value": f"{score:.2f}"},
            {"name": "DATE", "value": date_str},
            {"name": "EAVG", "value": f"{avg:.2f}"},
        ]

    sent, failed, skipped = _send_scores(score_map, targets, TEMPLATE_ID_EXAM, build, sus_cache, target)
    exam.sms_sent = True
    exam.sms_sent_at = timezone.now()
    exam.save(update_fields=['sms_sent', 'sms_sent_at'])
    log.info(f"[SMS][EXAM] id={exam.exam_id} sent={sent} skipped={len(skipped)} failed={len(failed)}")
    return {'sent': sent, 'skipped': skipped, 'failed': failed}


def send_assignment_scores(assignment, user_ids, target):
    score_map = _assignment_score_map(assignment)
    targets = _select_targets(score_map, user_ids)
    sus_cache = {su.student_user_id: su for su in StudentUser.objects.filter(student_user_id__in=score_map.keys())}
    avg = _assignment_group_avg(assignment)
    serie = series_assignment(assignment)
    date_str = jalali(assignment.assignment_available_time_end or assignment.assignment_creation_time)

    def build(name, score):
        return [
            {"name": "ASERIE", "value": str(serie)},
            {"name": "USERNAME", "value": name},
            {"name": "ASCORE", "value": f"{score:.2f}"},
            {"name": "DATE", "value": date_str},
            {"name": "AAVG", "value": f"{avg:.2f}"},
        ]

    sent, failed, skipped = _send_scores(score_map, targets, TEMPLATE_ID_ASSIGNMENT, build, sus_cache, target)
    assignment.sms_sent = True
    assignment.sms_sent_at = timezone.now()
    assignment.save(update_fields=['sms_sent', 'sms_sent_at'])
    log.info(f"[SMS][ASSIGNMENT] id={assignment.assignment_id} sent={sent} skipped={len(skipped)} failed={len(failed)}")
    return {'sent': sent, 'skipped': skipped, 'failed': failed}


# ====== پیام دلخواه ======
def send_custom(group_ids, user_ids, message, target):
    """به اعضای چند گروه و/یا چند فرد پیام دلخواه می‌فرستد.
    last_sms_target را تغییر نمی‌دهد (طبق نیاز)."""
    users = {}
    if group_ids:
        for u in User.objects.filter(groups__in=group_ids, is_staff=False).distinct():
            users[u.id] = u
    if user_ids:
        for u in User.objects.filter(id__in=user_ids):
            users[u.id] = u

    sus = {su.student_user_id: su for su in StudentUser.objects.filter(student_user_id__in=users.keys())}
    numbers = []
    for uid in users:
        nums, _ = resolve_numbers(sus.get(uid), target)
        numbers.extend(nums)
    numbers = list(dict.fromkeys(numbers))   # حذف تکراری با حفظ ترتیب

    if not numbers:
        return {'sent': 0, 'total_numbers': 0, 'failed': ['no_valid_numbers']}

    sent, failed = 0, []
    for i in range(0, len(numbers), SMS_CHUNK):
        chunk = numbers[i:i + SMS_CHUNK]
        try:
            sms.send_bulk_sms(chunk, message, LINE_NUMBER)
            sent += len(chunk)
        except Exception as e:
            failed.append(str(e))
    log.info(f"[SMS][CUSTOM] recipients={len(users)} numbers={len(numbers)} sent={sent} failed={len(failed)}")
    return {'sent': sent, 'total_numbers': len(numbers), 'failed': failed}
