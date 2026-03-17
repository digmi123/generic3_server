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
