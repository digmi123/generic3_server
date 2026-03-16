import random
import string
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings


def _make_cache_key(user_id: str) -> str:
    return f'2fa_code_{user_id}'


def send_2fa_code(user) -> str:
    """Generate a 6-digit code, store in cache for 5 min, email it to the user."""
    code = ''.join(random.choices(string.digits, k=6))
    cache.set(_make_cache_key(str(user.id)), code, timeout=300)
    send_mail(
        subject='Your verification code',
        message=f'Your 2FA code is: {code}',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )
    return code


def verify_2fa_code(user, code: str) -> bool:
    """Return True if code matches what is in cache, then delete it."""
    stored = cache.get(_make_cache_key(str(user.id)))
    if stored and stored == code:
        cache.delete(_make_cache_key(str(user.id)))
        return True
    return False


def setup_totp(user):
    """Return (or create) a TOTP device for the user and the provisioning URI."""
    from django_otp.plugins.otp_totp.models import TOTPDevice
    device, _ = TOTPDevice.objects.get_or_create(user=user, name='default')
    return device


def get_clinic_ids_for_user(user):
    """Return the list of clinic UUIDs associated with a user based on role."""
    role = user.role
    if role in ('CLINIC_MANAGER', 'DOCTOR'):
        from users.models import StaffClinic
        try:
            staff = user.staff
        except Exception:
            return []
        return list(StaffClinic.objects.filter(staff=staff).values_list('clinic_id', flat=True))
    if role in ('PATIENT', 'RESEARCH_PATIENT'):
        from users.models import PatientClinic
        try:
            patient = user.patient
        except Exception:
            return []
        return list(PatientClinic.objects.filter(patient=patient).values_list('clinic_id', flat=True))
    return []
