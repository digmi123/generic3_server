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
