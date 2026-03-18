import uuid
from django.db import models


class Medication(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    med_name = models.CharField(max_length=150)
    med_form = models.CharField(max_length=50)   # e.g. "Tablet", "Syrup", "Injection"
    med_unit = models.CharField(max_length=20)   # e.g. "mg", "ml", "mcg"

    def __str__(self):
        return f'{self.med_name} ({self.med_form}, {self.med_unit})'


class ClinicMedication(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    clinic = models.ForeignKey(
        'clinics.Clinic', on_delete=models.CASCADE, related_name='clinic_medications'
    )
    medication = models.ForeignKey(
        Medication, on_delete=models.CASCADE, related_name='clinic_medications'
    )

    class Meta:
        unique_together = ('clinic', 'medication')

    def __str__(self):
        return f'{self.clinic} — {self.medication}'


class PatientMedication(models.Model):
    FREQUENCY_CHOICES = [
        ('ONCE', 'Once'),
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly'),
    ]

    # Expected frequency_data shapes per frequency:
    #   ONCE    — {}  (no extra data needed)
    #   DAILY   — {"times_per_day": int, "time_slots": ["HH:MM", ...]}
    #   WEEKLY  — {"days_of_week": ["MON", "TUE", ...], "time": "HH:MM"}
    #   MONTHLY — {"day_of_month": int, "time": "HH:MM"}

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        'users.Patient', on_delete=models.CASCADE, related_name='patient_medications'
    )
    clinic = models.ForeignKey(
        'clinics.Clinic', on_delete=models.CASCADE, related_name='patient_medications'
    )
    doctor = models.ForeignKey(
        'users.Staff', on_delete=models.CASCADE, related_name='prescribed_medications'
    )
    medication = models.ForeignKey(
        Medication, on_delete=models.CASCADE, related_name='patient_medications'
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    dosage = models.CharField(max_length=50)        # e.g. "500mg"
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES)
    frequency_data = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f'{self.patient} — {self.medication} ({self.frequency})'


class MedicationLog(models.Model):
    STATUS_CHOICES = [
        ('TAKEN', 'Taken'),
        ('SKIPPED', 'Skipped'),
        ('DELAYED', 'Delayed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient_medication = models.ForeignKey(
        PatientMedication, on_delete=models.CASCADE, related_name='logs'
    )
    patient = models.ForeignKey(
        'users.Patient', on_delete=models.CASCADE, related_name='medication_logs'
    )
    taken_at = models.DateTimeField()
    dosage_taken = models.CharField(max_length=50)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)

    def __str__(self):
        return f'{self.patient} — {self.patient_medication.medication} [{self.status}] at {self.taken_at}'
