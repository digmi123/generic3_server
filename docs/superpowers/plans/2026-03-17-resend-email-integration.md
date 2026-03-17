# Resend Email Integration Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate the Resend Python SDK to send welcome emails when patients/doctors are created, and provide a ready-to-wire forgot-password email function.

**Architecture:** A `services/email_service.py` module owns all Resend API calls. Views call it after `serializer.save()` as a fire-and-forget side effect. Email failures are logged but never surface to the HTTP layer.

**Tech Stack:** Django 4.2, Django REST Framework, `resend` Python SDK, `python-dotenv` (already installed)

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Modify | `requirements.txt` | Add `resend` dependency |
| Create | `backend/generic3/.env` | Store `RESEND_API_KEY` and `DEFAULT_FROM_EMAIL` |
| Modify | `generic3/settings.py` | Load `.env`, expose `RESEND_API_KEY`, update `DEFAULT_FROM_EMAIL` |
| Create | `services/__init__.py` | Make `services` a Python package |
| Create | `services/email_service.py` | All Resend API calls, two public functions |
| Create | `services/tests.py` | Unit tests for email service (mocking Resend SDK) |
| Modify | `users/views.py` | Import and call `send_welcome_email` after user creation |
| Create | `users/tests.py` | View-level integration tests asserting email is called |

---

## Task 1: Install resend and configure the environment

**Files:**
- Modify: `backend/generic3/requirements.txt`
- Create: `backend/generic3/.env`
- Modify: `backend/generic3/generic3/settings.py`

- [ ] **Step 1: Add `resend` to requirements.txt**

Open `backend/generic3/requirements.txt` and append:
```
resend
```

- [ ] **Step 2: Install it**

```bash
cd backend/generic3
pip install resend
```

Expected: resend installs without errors.

- [ ] **Step 3: Create the .env file**

Create `backend/generic3/.env` with this content (fill in your real key later):
```
RESEND_API_KEY=re_your_api_key_here
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

- [ ] **Step 4: Check .gitignore for .env**

```bash
grep -n "\.env" /Users/klutz/Desktop/generic3_server/.gitignore 2>/dev/null || echo "NOT FOUND"
```

If `.env` is not listed, add it to `.gitignore`:
```
.env
```

- [ ] **Step 5: Update settings.py**

Open `backend/generic3/generic3/settings.py`. The first four lines currently are:
```python
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent
```

Add the dotenv block **after line 4** (after the `BASE_DIR` assignment), so it reads:
```python
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

import os
from dotenv import load_dotenv
load_dotenv(BASE_DIR / ".env")
```

> `BASE_DIR / ".env"` is an absolute path — resolves to `backend/generic3/.env` regardless of where the server process is started from. The block must come after `BASE_DIR` is assigned or you will get a `NameError` at startup.

Then replace line 129 (the existing hard-coded value):
```python
DEFAULT_FROM_EMAIL = "noreply@generic3.com"
```
with:
```python
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "noreply@generic3.com")
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
```

- [ ] **Step 6: Verify Django still starts**

```bash
cd backend/generic3
python manage.py check
```

Expected: `System check identified no issues (0 silenced).`

- [ ] **Step 7: Commit**

```bash
git add requirements.txt generic3/settings.py
git commit -m "feat: add resend dependency and load RESEND_API_KEY from .env"
```

> Do NOT stage `.env` — it contains secrets.

---

## Task 2: Create the email service

**Files:**
- Create: `backend/generic3/services/__init__.py`
- Create: `backend/generic3/services/email_service.py`
- Create: `backend/generic3/services/tests.py`

- [ ] **Step 1: Create the services package**

```bash
touch backend/generic3/services/__init__.py
```

- [ ] **Step 2: Write the failing tests**

Create `backend/generic3/services/tests.py`:

```python
from unittest.mock import patch, MagicMock
from django.test import TestCase


class SendWelcomeEmailTests(TestCase):

    @patch("services.email_service.resend.Emails.send")
    def test_patient_welcome_returns_true_on_success(self, mock_send):
        mock_send.return_value = MagicMock()
        from services.email_service import send_welcome_email
        result = send_welcome_email("patient@example.com", "pass123!", "Patient")
        self.assertTrue(result)
        mock_send.assert_called_once()

    @patch("services.email_service.resend.Emails.send")
    def test_doctor_welcome_returns_true_on_success(self, mock_send):
        mock_send.return_value = MagicMock()
        from services.email_service import send_welcome_email
        result = send_welcome_email("doctor@example.com", "pass123!", "Doctor")
        self.assertTrue(result)

    @patch("services.email_service.resend.Emails.send")
    def test_clinic_manager_welcome_returns_true_on_success(self, mock_send):
        mock_send.return_value = MagicMock()
        from services.email_service import send_welcome_email
        result = send_welcome_email("manager@example.com", "pass123!", "Clinic Manager")
        self.assertTrue(result)

    @patch("services.email_service.resend.Emails.send")
    def test_unknown_role_falls_back_to_generic_and_returns_true(self, mock_send):
        mock_send.return_value = MagicMock()
        from services.email_service import send_welcome_email
        result = send_welcome_email("user@example.com", "pass123!", "Unknown")
        self.assertTrue(result)

    @patch("services.email_service.resend.Emails.send")
    def test_welcome_email_includes_password_in_payload(self, mock_send):
        mock_send.return_value = MagicMock()
        from services.email_service import send_welcome_email
        send_welcome_email("patient@example.com", "mySecret99!", "Patient")
        call_kwargs = mock_send.call_args[0][0]
        self.assertIn("mySecret99!", call_kwargs["html"])

    @patch("services.email_service.resend.Emails.send")
    def test_welcome_email_returns_false_on_exception(self, mock_send):
        mock_send.side_effect = Exception("API error")
        from services.email_service import send_welcome_email
        result = send_welcome_email("patient@example.com", "pass123!", "Patient")
        self.assertFalse(result)

    @patch("services.email_service.resend.Emails.send")
    def test_welcome_email_uses_correct_subject(self, mock_send):
        mock_send.return_value = MagicMock()
        from services.email_service import send_welcome_email
        send_welcome_email("patient@example.com", "pass123!", "Patient")
        call_kwargs = mock_send.call_args[0][0]
        self.assertEqual(call_kwargs["subject"], "Welcome to Generic3")


class SendForgotPasswordEmailTests(TestCase):

    @patch("services.email_service.resend.Emails.send")
    def test_forgot_password_returns_true_on_success(self, mock_send):
        mock_send.return_value = MagicMock()
        from services.email_service import send_forgot_password_email
        result = send_forgot_password_email("user@example.com", "newPass99!")
        self.assertTrue(result)
        mock_send.assert_called_once()

    @patch("services.email_service.resend.Emails.send")
    def test_forgot_password_includes_new_password_in_payload(self, mock_send):
        mock_send.return_value = MagicMock()
        from services.email_service import send_forgot_password_email
        send_forgot_password_email("user@example.com", "newPass99!")
        call_kwargs = mock_send.call_args[0][0]
        self.assertIn("newPass99!", call_kwargs["html"])

    @patch("services.email_service.resend.Emails.send")
    def test_forgot_password_returns_false_on_exception(self, mock_send):
        mock_send.side_effect = Exception("Network error")
        from services.email_service import send_forgot_password_email
        result = send_forgot_password_email("user@example.com", "newPass99!")
        self.assertFalse(result)

    @patch("services.email_service.resend.Emails.send")
    def test_forgot_password_uses_correct_subject(self, mock_send):
        mock_send.return_value = MagicMock()
        from services.email_service import send_forgot_password_email
        send_forgot_password_email("user@example.com", "newPass99!")
        call_kwargs = mock_send.call_args[0][0]
        self.assertEqual(call_kwargs["subject"], "Your new Generic3 password")
```

- [ ] **Step 3: Run tests to confirm they fail**

```bash
cd backend/generic3
python manage.py test services.tests -v 2
```

Expected: All tests FAIL with `ModuleNotFoundError: No module named 'services.email_service'`

- [ ] **Step 4: Create email_service.py**

Create `backend/generic3/services/email_service.py`:

```python
import logging

import resend
from django.conf import settings

resend.api_key = settings.RESEND_API_KEY

logger = logging.getLogger("services.email_service")


def _build_welcome_html(generated_password: str, user_role: str) -> str:
    role_messages = {
        "Patient": (
            "You have been registered as a <strong>Patient</strong> on Generic3. "
            "You can now log in to your patient portal to view your health information."
        ),
        "Doctor": (
            "You have been registered as a <strong>Doctor</strong> on Generic3. "
            "You can now log in to the clinical portal to manage your patients."
        ),
        "Clinic Manager": (
            "You have been registered as a <strong>Clinic Manager</strong> on Generic3. "
            "You can now log in to the management portal to administer your clinic."
        ),
    }
    role_message = role_messages.get(
        user_role,
        "You have been registered on Generic3. You can now log in to your portal.",
    )
    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2>Welcome to Generic3</h2>
        <p>{role_message}</p>
        <p>Your temporary password is:</p>
        <p style="font-size: 18px; font-weight: bold; background: #f4f4f4;
                  padding: 10px; border-radius: 4px; display: inline-block;">
            {generated_password}
        </p>
        <p>Please log in and change your password as soon as possible.</p>
        <p>The Generic3 Team</p>
    </div>
    """


def _build_forgot_password_html(new_password: str) -> str:
    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2>Your New Generic3 Password</h2>
        <p>A new password has been generated for your account:</p>
        <p style="font-size: 18px; font-weight: bold; background: #f4f4f4;
                  padding: 10px; border-radius: 4px; display: inline-block;">
            {new_password}
        </p>
        <p>Please log in and change your password as soon as possible.</p>
        <p>The Generic3 Team</p>
    </div>
    """


def send_welcome_email(user_email: str, generated_password: str, user_role: str) -> bool:
    try:
        resend.Emails.send({
            "from": settings.DEFAULT_FROM_EMAIL,
            "to": [user_email],
            "subject": "Welcome to Generic3",
            "html": _build_welcome_html(generated_password, user_role),
        })
        return True
    except Exception as e:
        logger.error("Failed to send welcome email to %s: %s", user_email, e)
        return False


def send_forgot_password_email(user_email: str, new_password: str) -> bool:
    try:
        resend.Emails.send({
            "from": settings.DEFAULT_FROM_EMAIL,
            "to": [user_email],
            "subject": "Your new Generic3 password",
            "html": _build_forgot_password_html(new_password),
        })
        return True
    except Exception as e:
        logger.error("Failed to send forgot-password email to %s: %s", user_email, e)
        return False
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd backend/generic3
python manage.py test services.tests -v 2
```

Expected: All 11 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add services/__init__.py services/email_service.py services/tests.py
git commit -m "feat: add email service with send_welcome_email and send_forgot_password_email"
```

---

## Task 3: Wire up view integration

**Files:**
- Modify: `backend/generic3/users/views.py`
- Create: `backend/generic3/users/tests.py`

- [ ] **Step 1: Add the import to views.py (without the call yet)**

Open `backend/generic3/users/views.py`. After the existing imports block (after line 15), add:
```python
from services.email_service import send_welcome_email
```

Do NOT add the `send_welcome_email(...)` call yet — just the import. This makes the import patchable in the next step's tests.

- [ ] **Step 2: Write failing integration tests**

Create `backend/generic3/users/tests.py`:

```python
from unittest.mock import patch
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model
from clinics.models import Clinic
from users.models import Staff, StaffClinic

User = get_user_model()


def _make_clinic_manager(email="manager@test.com"):
    user = User(email=email, role="CLINIC_MANAGER", first_name="Test", last_name="Manager")
    user.set_password("TestPass99!")
    user.save()
    Staff.objects.create(user=user, staff_type="CLINIC_MANAGER")
    return user


def _make_clinic():
    return Clinic.objects.create(
        clinic_name="Test Clinic",
        clinic_url="https://test.example.com",
    )


def _link_manager_to_clinic(manager, clinic):
    StaffClinic.objects.create(staff=manager.staff, clinic=clinic)


def _auth_client(user, clinic_id):
    """Return an APIClient authenticated as `user` with `clinic_id` in the JWT payload."""
    token = AccessToken.for_user(user)
    token["active_clinic_id"] = str(clinic_id)
    client = APIClient()
    client.cookies["access"] = str(token)
    return client


class CreatePatientSendsWelcomeEmailTest(TestCase):

    @patch("users.views.send_welcome_email")
    def test_welcome_email_sent_with_correct_args_on_patient_creation(self, mock_send_email):
        mock_send_email.return_value = True
        manager = _make_clinic_manager()
        clinic = _make_clinic()
        _link_manager_to_clinic(manager, clinic)
        client = _auth_client(manager, clinic.id)

        response = client.post(
            "/api/v1/users/patients/",
            {"email": "newpatient@test.com", "first_name": "New", "last_name": "Patient"},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        mock_send_email.assert_called_once()
        email_arg, password_arg, role_arg = mock_send_email.call_args[0]
        self.assertEqual(email_arg, "newpatient@test.com")
        self.assertIsNotNone(password_arg)
        self.assertEqual(role_arg, "Patient")

    @patch("users.views.send_welcome_email")
    def test_user_created_even_if_email_fails(self, mock_send_email):
        mock_send_email.return_value = False  # email failure
        manager = _make_clinic_manager("manager2@test.com")
        clinic = _make_clinic()
        _link_manager_to_clinic(manager, clinic)
        client = _auth_client(manager, clinic.id)

        response = client.post(
            "/api/v1/users/patients/",
            {"email": "patient2@test.com", "first_name": "Another", "last_name": "Patient"},
            format="json",
        )

        # HTTP 201 even though email returned False
        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.filter(email="patient2@test.com").exists())


class CreateDoctorSendsWelcomeEmailTest(TestCase):

    @patch("users.views.send_welcome_email")
    def test_welcome_email_sent_with_correct_args_on_doctor_creation(self, mock_send_email):
        mock_send_email.return_value = True
        manager = _make_clinic_manager("manager3@test.com")
        clinic = _make_clinic()
        _link_manager_to_clinic(manager, clinic)
        client = _auth_client(manager, clinic.id)

        response = client.post(
            "/api/v1/users/doctors/",
            {"email": "newdoctor@test.com", "first_name": "New", "last_name": "Doctor"},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        mock_send_email.assert_called_once()
        email_arg, password_arg, role_arg = mock_send_email.call_args[0]
        self.assertEqual(email_arg, "newdoctor@test.com")
        self.assertIsNotNone(password_arg)
        self.assertEqual(role_arg, "Doctor")
```

- [ ] **Step 3: Run tests to confirm they fail**

```bash
cd backend/generic3
python manage.py test users.tests -v 2
```

Expected: Tests FAIL — `mock_send_email.assert_called_once()` fails because the view has the import but no call yet.

- [ ] **Step 4: Add the email calls to both views**

Open `backend/generic3/users/views.py`.

In `clinic_patients_list`, replace the stale comment on line 123:
```python
    # send_welcome_email(user.email, user.full_name, serializer.generated_password)
```
with:
```python
    send_welcome_email(serializer.instance.email, serializer.generated_password, 'Patient')
```

In `clinic_doctors_list`, replace the stale comment on line 204:
```python
    # send_welcome_email(user.email, user.full_name, serializer.generated_password)
```
with:
```python
    send_welcome_email(serializer.instance.email, serializer.generated_password, 'Doctor')
```

> The existing placeholder comments have the wrong argument order (`user.full_name` is not part of the function signature). Replace the entire comment line — do not adapt it.

- [ ] **Step 5: Run all tests**

```bash
cd backend/generic3
python manage.py test services.tests users.tests -v 2
```

Expected: All tests PASS.

- [ ] **Step 6: Run Django system check**

```bash
python manage.py check
```

Expected: `System check identified no issues (0 silenced).`

- [ ] **Step 7: Commit**

```bash
git add users/views.py users/tests.py
git commit -m "feat: call send_welcome_email from patient and doctor creation views"
```

---

## Done

At this point:
- `resend` is installed and configured via `.env`
- `services/email_service.py` sends welcome emails (role-specific) and has a ready-to-use `send_forgot_password_email`
- Both creation views send a welcome email after saving the user
- All logic is tested: 11 service unit tests + 3 view integration tests
- Email failure never breaks the HTTP response
