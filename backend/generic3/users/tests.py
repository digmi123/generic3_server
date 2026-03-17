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

    @patch("users.views.send_welcome_email")
    def test_user_created_even_if_email_fails_for_doctor(self, mock_send_email):
        mock_send_email.return_value = False  # email failure
        manager = _make_clinic_manager("manager4@test.com")
        clinic = _make_clinic()
        _link_manager_to_clinic(manager, clinic)
        client = _auth_client(manager, clinic.id)

        response = client.post(
            "/api/v1/users/doctors/",
            {"email": "doctor2@test.com", "first_name": "Another", "last_name": "Doctor"},
            format="json",
        )

        # HTTP 201 even though email returned False
        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.filter(email="doctor2@test.com").exists())
