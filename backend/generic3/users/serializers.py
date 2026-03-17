import secrets
import string

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, Staff, StaffClinic, Patient, PatientClinic, PatientDoctor
from clinics.models import Clinic
from clinics.serializers import ClinicSerializer


def _generate_password(length=12):
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(secrets.choice(alphabet) for _ in range(length))


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=False, validators=[validate_password]
    )
    clinics = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "phone_number",
            "first_name",
            "last_name",
            "role",
            "is_2fa_enabled",
            "is_active",
            "created_at",
            "password",
            "clinics",
        ]
        read_only_fields = ["id", "created_at"]

    def get_clinics(self, obj):
        role = obj.role
        if role in ("CLINIC_MANAGER", "DOCTOR"):
            try:
                clinics = [
                    sc.clinic
                    for sc in obj.staff.staff_clinics.select_related("clinic").all()
                ]
                return ClinicSerializer(clinics, many=True).data
            except Exception:
                return []
        if role in ("PATIENT", "RESEARCH_PATIENT"):
            try:
                clinics = [
                    pc.clinic
                    for pc in obj.patient.patient_clinics.select_related("clinic").all()
                ]
                return ClinicSerializer(clinics, many=True).data
            except Exception:
                return []
        return []

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class StaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = Staff
        fields = ["id", "user", "staff_type"]


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ["id", "user"]


class PatientDoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientDoctor
        fields = ["id", "patient", "doctor", "clinic"]


class _BaseCreateUserSerializer(serializers.ModelSerializer):
    """Shared base for the dedicated create serializers. Not used directly."""
    password = serializers.CharField(
        write_only=True, required=False, validators=[validate_password]
    )
    clinic_id = serializers.UUIDField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ["email", "phone_number", "first_name", "last_name", "password", "clinic_id"]

    def _make_user(self, validated_data, role, password=None):
        clinic_id = validated_data.pop("clinic_id", None)
        validated_data.pop("password", None)  # discard if frontend sent one
        user = User(role=role, **validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user, clinic_id

    def _link_clinic_to_staff(self, staff, clinic_id):
        if clinic_id:
            try:
                StaffClinic.objects.create(staff=staff, clinic=Clinic.objects.get(id=clinic_id))
            except Clinic.DoesNotExist:
                pass

    def _link_clinic_to_patient(self, patient, clinic_id):
        if clinic_id:
            try:
                PatientClinic.objects.create(patient=patient, clinic=Clinic.objects.get(id=clinic_id))
            except Clinic.DoesNotExist:
                pass


class CreateDoctorSerializer(_BaseCreateUserSerializer):
    def create(self, validated_data):
        self.generated_password = _generate_password()
        user, clinic_id = self._make_user(validated_data, role="DOCTOR", password=self.generated_password)
        staff = Staff.objects.create(user=user, staff_type="DOCTOR")
        self._link_clinic_to_staff(staff, clinic_id)
        return user


class CreatePatientSerializer(_BaseCreateUserSerializer):
    def create(self, validated_data):
        self.generated_password = _generate_password()
        user, clinic_id = self._make_user(validated_data, role="PATIENT", password=self.generated_password)
        patient = Patient.objects.create(user=user)
        self._link_clinic_to_patient(patient, clinic_id)
        return user


class CreateResearchPatientSerializer(_BaseCreateUserSerializer):
    def create(self, validated_data):
        # Research patients have no password — they use a different access flow
        user, clinic_id = self._make_user(validated_data, role="RESEARCH_PATIENT")
        patient = Patient.objects.create(user=user)
        self._link_clinic_to_patient(patient, clinic_id)
        return user
