"""تست‌های ردیابیِ نشست + پاسخِ غنیِ لاگین + اعتبارسنجیِ رمزِ ادمین."""
import json

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.test import TestCase
from knox.models import AuthToken
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp.oath import totp

from StudentsInfo.models import TokenSession

_CHROME_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
             "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")


class SessionTrackingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="0011223344", password="pw-strong-xyz")

    def _login(self, ua=_CHROME_UA):
        return self.client.post(
            "/login",
            data=json.dumps({"username": "0011223344", "password": "pw-strong-xyz"}),
            content_type="application/json",
            HTTP_USER_AGENT=ua,
        )

    def test_login_enriched_response_and_session_created(self):
        resp = self._login()
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        # پاسخِ غنی‌شده
        self.assertIn("token", body)
        self.assertEqual(body["user"]["username"], "0011223344")
        self.assertEqual(body["user"]["role"], "student")
        # نشست با متادیتای دستگاه ساخته شد
        self.assertEqual(TokenSession.objects.filter(user=self.user).count(), 1)
        session = TokenSession.objects.get(user=self.user)
        self.assertEqual(session.device, "Desktop - Chrome")

    def test_active_sessions_lists_live_tokens(self):
        token = self._login().json()["token"]
        resp = self.client.get("/sessions", HTTP_AUTHORIZATION=f"Token {token}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data), 1)
        self.assertTrue(data[0]["current"])
        self.assertEqual(data[0]["device"], "Desktop - Chrome")

    def test_revoke_session_logs_out_that_device(self):
        # دو دستگاه (دو توکن)
        t1 = self._login(ua=_CHROME_UA).json()["token"]
        t2 = self._login(ua="Mozilla/5.0 (iPhone) Mobile Safari").json()["token"]
        self.assertEqual(AuthToken.objects.filter(user=self.user).count(), 2)

        # با t1 لیست بگیر، نشستِ «غیرِجاری» (t2) را پیدا و لغو کن
        listing = self.client.get("/sessions", HTTP_AUTHORIZATION=f"Token {t1}").json()
        other_id = next(s["id"] for s in listing if not s["current"])
        resp = self.client.delete(f"/sessions/{other_id}", HTTP_AUTHORIZATION=f"Token {t1}")
        self.assertEqual(resp.status_code, 200)

        # توکنِ آن دستگاه باطل شد؛ t1 هنوز کار می‌کند
        self.assertEqual(AuthToken.objects.filter(user=self.user).count(), 1)
        self.assertEqual(
            self.client.get("/sessions", HTTP_AUTHORIZATION=f"Token {t2}").status_code, 401
        )
        self.assertEqual(
            self.client.get("/sessions", HTTP_AUTHORIZATION=f"Token {t1}").status_code, 200
        )

    def test_cannot_revoke_another_users_session(self):
        other = User.objects.create_user(username="9988776655", password="pw-strong-xyz")
        TokenSession.objects.create(token_digest="x" * 128, user=other, device="Desktop")
        victim = TokenSession.objects.get(user=other)
        my_token = self._login().json()["token"]
        resp = self.client.delete(f"/sessions/{victim.id}", HTTP_AUTHORIZATION=f"Token {my_token}")
        self.assertEqual(resp.status_code, 404)   # نشستِ کاربرِ دیگر برای من پیدا نمی‌شود


class AdminPasswordValidatorTests(TestCase):
    def test_student_numeric_password_allowed(self):
        student = User.objects.create_user(username="0012345678", password="x")
        # کدملیِ ۱۰رقمی برای دانش‌آموز باید مجاز باشد (سخت‌گیریِ ادمین اعمال نمی‌شود)
        validate_password("0012345678", user=student)   # نباید استثنا بدهد

    def test_admin_numeric_password_rejected(self):
        admin = User.objects.create_user(
            username="teacher", password="x", is_staff=True, is_superuser=True
        )
        with self.assertRaises(ValidationError):
            validate_password("0012345678", user=admin)   # عددیِ صرف → رد

    def test_admin_strong_password_accepted(self):
        admin = User.objects.create_user(
            username="teacher", password="x", is_staff=True, is_superuser=True
        )
        validate_password("Zx9!qwerty-lms", user=admin)   # قوی → قبول


class TOTPApiTests(TestCase):
    """جریانِ API دو‌مرحله‌ایِ TOTP: اجباری برای staff/superuser، هرگز برای دانش‌آموز."""
    def setUp(self):
        self.staff = User.objects.create_user(
            username="boss", password="Zx9!qwerty-lms", is_staff=True, is_superuser=True
        )
        self.student = User.objects.create_user(username="0011223344", password="pw-strong-xyz")

    @staticmethod
    def _token(device):
        return f"{totp(device.bin_key, step=device.step, t0=device.t0, digits=device.digits):0{device.digits}d}"

    def _post(self, url, body):
        return self.client.post(url, data=json.dumps(body), content_type="application/json")

    # --- دانش‌آموز: هیچ TOTP ---
    def test_student_login_issues_token_without_totp(self):
        resp = self._post("/login", {"username": "0011223344", "password": "pw-strong-xyz"})
        self.assertEqual(resp.status_code, 200)
        self.assertIn("token", resp.json())

    def test_student_cannot_setup_totp(self):
        resp = self._post("/2fa/setup", {"username": "0011223344", "password": "pw-strong-xyz"})
        self.assertEqual(resp.status_code, 403)

    # --- staff: TOTP اجباری و دو‌مرحله‌ای ---
    def test_staff_login_without_device_requires_setup(self):
        resp = self._post("/login", {"username": "boss", "password": "Zx9!qwerty-lms"})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json().get("otp_setup_required"))
        self.assertNotIn("token", resp.json())

    def test_setup_then_confirm_issues_token(self):
        s = self._post("/2fa/setup", {"username": "boss", "password": "Zx9!qwerty-lms"})
        self.assertEqual(s.status_code, 200)
        self.assertIn("otpauth_url", s.json())
        self.assertIn("secret", s.json())
        device = TOTPDevice.objects.get(user=self.staff, confirmed=False)
        c = self._post("/2fa/confirm", {
            "username": "boss", "password": "Zx9!qwerty-lms", "otp_token": self._token(device)
        })
        self.assertEqual(c.status_code, 200)
        self.assertIn("token", c.json())
        device.refresh_from_db()
        self.assertTrue(device.confirmed)

    def test_staff_two_step_login(self):
        device = TOTPDevice.objects.create(user=self.staff, name='d', confirmed=True)
        step1 = self._post("/login", {"username": "boss", "password": "Zx9!qwerty-lms"})
        self.assertEqual(step1.status_code, 200)
        self.assertTrue(step1.json().get("otp_required"))
        self.assertNotIn("token", step1.json())
        step2 = self._post("/login", {
            "username": "boss", "password": "Zx9!qwerty-lms", "otp_token": self._token(device)
        })
        self.assertEqual(step2.status_code, 200)
        self.assertIn("token", step2.json())

    def test_staff_login_wrong_otp_rejected(self):
        TOTPDevice.objects.create(user=self.staff, name='d', confirmed=True)
        resp = self._post("/login", {
            "username": "boss", "password": "Zx9!qwerty-lms", "otp_token": "000000"
        })
        self.assertEqual(resp.status_code, 400)

    def test_status_endpoint(self):
        TOTPDevice.objects.create(user=self.staff, name='d', confirmed=True)
        token = AuthToken.objects.create(self.staff)[1]
        resp = self.client.get("/2fa/status", HTTP_AUTHORIZATION=f"Token {token}")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["enabled"])
        self.assertTrue(resp.json()["required"])
