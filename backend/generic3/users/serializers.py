from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, Staff, StaffClinic, Patient, PatientClinic, PatientDoctor
from clinics.serializers import ClinicSerializer


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
            "is_staff",
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
