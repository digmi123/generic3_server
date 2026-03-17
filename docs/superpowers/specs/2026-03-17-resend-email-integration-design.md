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
Add to `backend/generic3/.env` (create file if absent):
```
RESEND_API_KEY=re_...
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

### settings.py
Load environment variables using `python-dotenv` (already installed):
```python
from dotenv import load_dotenv
load_dotenv()

RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "noreply@generic3.com")
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

### Responsibilities
- Configure the Resend SDK with `settings.RESEND_API_KEY`
- Expose two public functions
- Catch all Resend API exceptions; log errors; return `True`/`False` to callers

### Functions

#### `send_welcome_email(user_email, generated_password, user_role)`
- `user_role` is one of `'Patient'`, `'Doctor'`, or `'Clinic Manager'`
- Constructs a role-specific HTML string (no template files)
- Sends via `resend.Emails.send()`
- Returns `True` on success, `False` on failure

#### `send_forgot_password_email(user_email, new_password)`
- Constructs a simple HTML string containing the new password
- Sends via `resend.Emails.send()`
- Returns `True` on success, `False` on failure

### Error Handling
- Wrapped in `try/except Exception`
- Failures are logged via Python's `logging` module
- Callers receive `True`/`False` — email failure never raises to the HTTP layer

---

## 4. Serializer Change

**File:** `users/serializers.py`

`CreateDoctorSerializer` and `CreatePatientSerializer` both call `_generate_password()` internally. Add one line to each `create()` method to expose the plain-text password before it is hashed:

```python
password = _generate_password()
self.generated_password = password  # expose for view
user = self._make_user(validated_data, password)
```

No other serializer changes required.

---

## 5. View Integration

**File:** `users/views.py`

Both creation views already contain a `# send welcome email` comment placeholder.

```python
# clinic_patients_list — POST
serializer.save()
send_welcome_email(serializer.instance.email, serializer.generated_password, 'Patient')

# clinic_doctors_list — POST
serializer.save()
send_welcome_email(serializer.instance.email, serializer.generated_password, 'Doctor')
```

**Key behaviour:** Email is fire-and-forget. If `send_welcome_email` returns `False`, the user has already been created and the HTTP 201 response is returned normally. Email failures are silent to the API consumer but logged server-side.

---

## 6. Out of Scope

- Forgot password HTTP endpoint — the `send_forgot_password_email` function will be written but the endpoint wiring is deferred
- Research patient welcome emails — research patients have no password, so no welcome email
- HTML email templates or `render_to_string`
- SMTP configuration (Resend SDK only)
