from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Medication, ClinicMedication, PatientMedication, MedicationLog
from .serializers import (
    MedicationSerializer,
    ClinicMedicationSerializer,
    PatientMedicationSerializer,
    MedicationLogSerializer,
)
from clinics.models import Clinic
from users.models import Patient, Staff


def _is_admin(user):
    return user.role == "ADMIN" or user.is_staff


def _is_staff(user):
    return user.role in ("ADMIN", "CLINIC_MANAGER", "DOCTOR") or user.is_staff


# ── Global medications ──────────────────────────────────────────────────────────


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def medications_list(request):
    if request.method == "GET":
        if not _is_staff(request.user):
            return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)
        qs = Medication.objects.all().order_by("med_name")
        return Response(MedicationSerializer(qs, many=True).data)

    if not _is_admin(request.user):
        return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)
    serializer = MedicationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def medication_detail(request, medication_id):
    try:
        medication = Medication.objects.get(id=medication_id)
    except Medication.DoesNotExist:
        return Response(
            {"detail": "Medication not found."}, status=status.HTTP_404_NOT_FOUND
        )

    if not _is_staff(request.user):
        return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)

    if request.method == "GET":
        return Response(MedicationSerializer(medication).data)

    if not _is_admin(request.user):
        return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)

    if request.method in ("PUT", "PATCH"):
        serializer = MedicationSerializer(
            medication, data=request.data, partial=(request.method == "PATCH")
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data)

    medication.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# ── Clinic medications ──────────────────────────────────────────────────────────


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def clinic_medications_list(request, clinic_id):
    try:
        clinic = Clinic.objects.get(id=clinic_id)
    except Clinic.DoesNotExist:
        return Response(
            {"detail": "Clinic not found."}, status=status.HTTP_404_NOT_FOUND
        )

    if request.method == "GET":
        qs = ClinicMedication.objects.filter(clinic=clinic).select_related("medication")
        return Response(ClinicMedicationSerializer(qs, many=True).data)

    if request.user.role != "CLINIC_MANAGER":
        return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)

    medication_id = request.data.get("medication_id")
    try:
        medication = Medication.objects.get(id=medication_id)
    except Medication.DoesNotExist:
        return Response(
            {"detail": "Medication not found."}, status=status.HTTP_404_NOT_FOUND
        )

    cm, created = ClinicMedication.objects.get_or_create(
        clinic=clinic, medication=medication
    )
    return Response(
        ClinicMedicationSerializer(cm).data,
        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
    )


@api_view(["GET", "DELETE"])
@permission_classes([IsAuthenticated])
def clinic_medication_detail(request, clinic_id, medication_id):
    try:
        cm = ClinicMedication.objects.get(
            clinic_id=clinic_id, medication_id=medication_id
        )
    except ClinicMedication.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        return Response(ClinicMedicationSerializer(cm).data)

    if request.user.role != "CLINIC_MANAGER":
        return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)

    cm.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# ── Patient medications ─────────────────────────────────────────────────────────


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def patient_medications_list(request, clinic_id, user_id):
    try:
        clinic = Clinic.objects.get(id=clinic_id)
        patient = Patient.objects.get(user_id=user_id)
    except (Clinic.DoesNotExist, Patient.DoesNotExist):
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        qs = PatientMedication.objects.filter(
            patient=patient, clinic=clinic
        ).select_related("medication")
        return Response(PatientMedicationSerializer(qs, many=True).data)

    if not _is_staff(request.user):
        return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)

    medication_id = request.data.get("medication_id")
    try:
        medication = Medication.objects.get(id=medication_id)
    except Medication.DoesNotExist:
        return Response(
            {"detail": "Medication not found."}, status=status.HTTP_404_NOT_FOUND
        )

    if not ClinicMedication.objects.filter(
        clinic=clinic, medication=medication
    ).exists():
        return Response(
            {"detail": "Medication not available in this clinic."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    doctor_user_id = request.data.get("doctor_user_id")
    doctor = Staff.objects.get(user_id=doctor_user_id)
    print("Doctor:", doctor)
    serializer = PatientMedicationSerializer(
        data={
            **request.data,
            "patient": str(patient.id),
            "clinic": str(clinic.id),
            "doctor": doctor.id,
            "medication": medication_id,
        }
    )
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save(patient=patient, clinic=clinic)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def patient_medication_detail(request, clinic_id, user_id, medication_record_id):
    try:
        patient = Patient.objects.get(user_id=user_id)
        pm = PatientMedication.objects.get(
            id=medication_record_id, patient_id=patient.id, clinic_id=clinic_id
        )
    except PatientMedication.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        return Response(PatientMedicationSerializer(pm).data)

    if not _is_staff(request.user):
        return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)

    if request.method == "PATCH":
        serializer = PatientMedicationSerializer(pm, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data)

    pm.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# ── Medication logs ─────────────────────────────────────────────────────────────


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def medication_logs_list(request, clinic_id, patient_id, medication_record_id):
    try:
        pm = PatientMedication.objects.get(
            id=medication_record_id, patient__id=patient_id, clinic_id=clinic_id
        )
    except PatientMedication.DoesNotExist:
        return Response(
            {"detail": "Prescription not found."}, status=status.HTTP_404_NOT_FOUND
        )

    if request.method == "GET":
        qs = MedicationLog.objects.filter(patient_medication=pm).order_by("-taken_at")
        return Response(MedicationLogSerializer(qs, many=True).data)

    serializer = MedicationLogSerializer(
        data={
            **request.data,
            "patient_medication": str(pm.id),
            "patient": str(pm.patient.id),
            "dosage_taken": request.data.get("dosage_taken", pm.dosage),
        }
    )
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save(patient=pm.patient, patient_medication=pm)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["GET", "DELETE"])
@permission_classes([IsAuthenticated])
def medication_log_detail(request, clinic_id, patient_id, medication_record_id, log_id):
    try:
        log = MedicationLog.objects.get(
            id=log_id,
            patient_medication_id=medication_record_id,
            patient__id=patient_id,
        )
    except MedicationLog.DoesNotExist:
        return Response({"detail": "Log not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        return Response(MedicationLogSerializer(log).data)

    if not _is_staff(request.user):
        return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)

    log.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def patient_all_medication_logs(request, clinic_id, user_id):
    patient = Patient.objects.get(user_id=user_id)
    qs = MedicationLog.objects.filter(
        patient=patient,
        patient_medication__clinic_id=clinic_id,
    ).select_related("patient_medication__medication")

    med_name = request.query_params.get("med_name")
    if med_name:
        qs = qs.filter(patient_medication__medication__med_name__iexact=med_name)

    start_date = request.query_params.get("start_date")
    if start_date:
        qs = qs.filter(taken_at__date__gte=start_date)

    qs = qs.order_by("-taken_at")
    return Response(MedicationLogSerializer(qs, many=True).data)
