# Resend Email Integration — Design Spec

**Date:** 2026-03-17
**Branch:** email_sender
**Status:** Approved

---

## Overview

Integrate the Resend Python SDK into the Django REST Framework backend to handle transactional emails. Email bodies are constructed as plain HTML strings directly in Python — no Django templates or `render_to_string`. A shared `services/email_service.py` module centralises all Resend API calls, keeping views and serializers free of email logic.

---

## 1. Configuration

### .env
Create `backend/generic3/.env` (file does not currently exist):
```
RESEND_API_KEY=re_...
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

### settings.py
At the top of `settings.py`, after the existing `from pathlib import Path` import block, add:
```python
import os
from dotenv import load_dotenv
load_dotenv(BASE_DIR / ".env")
```

Using `BASE_DIR / ".env"` (an absolute path) ensures the `.env` file is found regardless of which directory the server process is started from.

Then **replace** the existing hard-coded line:
```python
DEFAULT_FROM_EMAIL = "noreply@generic3.com"
```
with:
```python
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "noreply@generic3.com")
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
```

### requirements.txt
Add `resend` to the existing requirements file.

---

## 2. File Structure

New `services/` directory at the Django project root (alongside `users/`, `clinics/`, etc.):

```
backend/generic3/
├── generic3/
├── users/
├── clinics/
├── modules/
├── accounts/
├── services/              ← new
│   ├── __init__.py
│   └── email_service.py
└── manage.py
```

---

## 3. Email Service (`services/email_service.py`)

### Module-level SDK initialisation
At module level (top of the file, after imports), set the Resend API key once:
```python
import resend
from django.conf import settings

resend.api_key = settings.RESEND_API_KEY
```

If `settings.RESEND_API_KEY` is `None` (missing `.env` or missing key), the Resend SDK will raise an exception on the first `send()` call. This will be caught by the function's `try/except` block and logged at `ERROR` level with a clear message, making misconfiguration visible in the server logs.

### Responsibilities
- Set `resend.api_key` at module level as shown above
- Expose two public functions
- Use `settings.DEFAULT_FROM_EMAIL` as the `from` address for all emails
- Catch all exceptions (bare `Exception`) — intentionally broad to cover both `resend.exceptions.ResendError` (API-level) and network failures
- Log failures using `logging.getLogger("services.email_service")` at `ERROR` level
- Return `True`/`False` to callers; never raise to the HTTP layer

### Functions

#### `send_welcome_email(user_email, generated_password, user_role)`
- `user_role` must be one of `'Patient'`, `'Doctor'`, or `'Clinic Manager'` (title-cased display strings, not the model's role constants)
- **Subject:** `"Welcome to Generic3"` (same for all roles)
- **From:** `settings.DEFAULT_FROM_EMAIL`
- Constructs a role-specific HTML string:
  - **`'Patient'`:** greeting as a patient, portal access instructions, auto-generated password
  - **`'Doctor'`:** greeting as a doctor, clinical portal access instructions, auto-generated password
  - **`'Clinic Manager'`:** greeting as a clinic manager, management portal access instructions, auto-generated password
  - **Unrecognised role:** falls back to a generic welcome message that still includes the password
- Sends via `resend.Emails.send()`
- Returns `True` on success, `False` on failure

#### `send_forgot_password_email(user_email, new_password)`
- **Subject:** `"Your new Generic3 password"`
- **From:** `settings.DEFAULT_FROM_EMAIL`
- Constructs a simple HTML string containing the new password
- Sends via `resend.Emails.send()`
- Returns `True` on success, `False` on failure
- **Status:** Fully implemented and ready to use; the HTTP endpoint that calls it is deferred to a later sprint

### Error Handling
- Both functions wrapped in `try/except Exception`
- On failure: log with `logger.error(...)` including the exception message, then return `False`
- On success: return `True`
- Django's default logging propagates `services.email_service` to the root logger; no additional `LOGGING` config in `settings.py` is required

---

## 4. Serializer Change

**File:** `users/serializers.py`

`CreateDoctorSerializer` and `CreatePatientSerializer` already store `self.generated_password` before hashing the password. **This change is already in place** — no serializer modifications are required.

For reference, the existing pattern looks like:
```python
password = _generate_password()
self.generated_password = password
user = self._make_user(validated_data, role=..., password=password)
```

---

## 5. View Integration

**File:** `users/views.py`

Both creation views contain a stale placeholder comment (lines 123 and 204):
```python
# send_welcome_email(user.email, user.full_name, serializer.generated_password)
```
**This comment signature is wrong and must not be used as a reference.** It has the wrong argument order and includes `user.full_name` which is not part of the function signature. Replace it entirely.

Add to imports at top of `views.py`:
```python
from services.email_service import send_welcome_email
```

Replace the placeholder comment in each view:
```python
# clinic_patients_list — POST
serializer.save()
send_welcome_email(serializer.instance.email, serializer.generated_password, 'Patient')

# clinic_doctors_list — POST
serializer.save()
send_welcome_email(serializer.instance.email, serializer.generated_password, 'Doctor')
```

**Key behaviour:** Email is fire-and-forget. If `send_welcome_email` returns `False`, the user is still created and the HTTP 201 response is returned normally. Email failures are silent to the API consumer but logged server-side.

---

## 6. Out of Scope

- Forgot password HTTP endpoint — `send_forgot_password_email` is implemented but the endpoint wiring is deferred
- Research patient welcome emails — research patients have no password, so no welcome email applies
- HTML email templates or `render_to_string`
- SMTP configuration (Resend SDK only)
- Changes to the existing `send_2fa_code()` in `generic3/utils.py` — that function uses Django's `send_mail` and is unrelated to this integration
