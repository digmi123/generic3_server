import uuid
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "ADMIN")
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ("ADMIN", "Admin"),
        ("CLINIC_MANAGER", "Clinic Manager"),
        ("DOCTOR", "Doctor"),
        ("PATIENT", "Patient"),
        ("RESEARCH_PATIENT", "Research Patient"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="PATIENT")
    is_2fa_enabled = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = UserManager()

    def __str__(self):
        return f"{self.email} ({self.role})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()


class Staff(models.Model):
    STAFF_TYPE_CHOICES = [
        ("CLINIC_MANAGER", "Clinic Manager"),
        ("DOCTOR", "Doctor"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="staff")
    staff_type = models.CharField(max_length=20, choices=STAFF_TYPE_CHOICES)

    def __str__(self):
        return f"{self.staff_type}: {self.user.email}"


class StaffClinic(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    staff = models.ForeignKey(
        Staff, on_delete=models.CASCADE, related_name="staff_clinics"
    )
    clinic = models.ForeignKey(
        "clinics.Clinic", on_delete=models.CASCADE, related_name="staff_clinics"
    )

    class Meta:
        unique_together = ("staff", "clinic")

    def __str__(self):
        return f"{self.staff} @ {self.clinic}"


class Patient(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="patient")

    def __str__(self):
        return f"Patient: {self.user.email}"


class PatientClinic(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="patient_clinics"
    )
    clinic = models.ForeignKey(
        "clinics.Clinic", on_delete=models.CASCADE, related_name="patient_clinics"
    )

    class Meta:
        unique_together = ("patient", "clinic")

    def __str__(self):
        return f"{self.patient} @ {self.clinic}"


class PatientDoctor(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="patient_doctors"
    )
    doctor = models.ForeignKey(
        Staff, on_delete=models.CASCADE, related_name="doctor_patients"
    )
    clinic = models.ForeignKey(
        "clinics.Clinic",
        on_delete=models.CASCADE,
        null=True,
        related_name="patient_doctors",
    )

    class Meta:
        unique_together = ("patient", "doctor", "clinic")

    def __str__(self):
        return f"{self.patient} — Dr.{self.doctor} @ {self.clinic}"
