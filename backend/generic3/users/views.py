from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination

from .models import Staff, StaffClinic, Patient, PatientClinic
from .serializers import (
    UserSerializer,
    CreateDoctorSerializer,
    CreatePatientSerializer,
    CreateResearchPatientSerializer,
)

User = get_user_model()


def _is_admin(user):
    return user.role == "ADMIN" or user.is_staff


def _get_clinic_id(request):
    return request.query_params.get("clinic_id") or request.data.get("clinic_id")


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def users_list(request):
    user = request.user
    if _is_admin(user):
        qs = User.objects.all().order_by("email")
    elif user.role in ("CLINIC_MANAGER", "DOCTOR"):
        try:
            clinic_ids = list(
                user.staff.staff_clinics.values_list("clinic_id", flat=True)
            )
        except Exception:
            clinic_ids = []
        patient_ids = PatientClinic.objects.filter(
            clinic_id__in=clinic_ids
        ).values_list("patient__user_id", flat=True)
        staff_ids = StaffClinic.objects.filter(clinic_id__in=clinic_ids).values_list(
            "staff__user_id", flat=True
        )
        qs = User.objects.filter(id__in=list(patient_ids) + list(staff_ids)).order_by(
            "email"
        )
    else:
        return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)

    paginator = PageNumberPagination()
    paginator.page_size = 20
    page = paginator.paginate_queryset(qs, request)
    serializer = UserSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def clinic_managers_list(request):
    """Admin only — returns all clinic managers across all clinics."""
    if not _is_admin(request.user):
        return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)

    qs = User.objects.filter(role="CLINIC_MANAGER").order_by("email")
    paginator = PageNumberPagination()
    paginator.page_size = 20
    page = paginator.paginate_queryset(qs, request)
    serializer = UserSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def clinic_patients_list(request):
    if request.method == "GET":
        if request.user.role not in ("DOCTOR", "CLINIC_MANAGER"):
            return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)

        clinic_id = request.auth.get("active_clinic_id") if request.auth else None
        if not clinic_id:
            return Response(
                {"detail": "No active clinic in session."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        qs = (
            User.objects.filter(
                role="PATIENT",
                patient__patient_clinics__clinic_id=clinic_id,
            )
            .distinct()
            .order_by("email")
        )
        paginator = PageNumberPagination()
        paginator.page_size = 20
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(UserSerializer(page, many=True).data)

    # POST — create patient (clinic manager only)
    if request.user.role != "CLINIC_MANAGER":
        return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)

    clinic_id = request.auth.get("active_clinic_id") if request.auth else None
    if not clinic_id:
        return Response(
            {"detail": "No active clinic in session."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    data = request.data.copy()
    data["clinic_id"] = clinic_id

    serializer = CreatePatientSerializer(data=data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        user = serializer.save()

    # send_welcome_email(user.email, user.full_name, serializer.generated_password)

    return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def patient_detail(request, user_id):
    """Admin, Clinic Manager, or Doctor — view a patient's details if in the same clinic."""
    try:
        target = User.objects.get(id=user_id, role__in=("PATIENT", "RESEARCH_PATIENT"))
    except User.DoesNotExist:
        return Response(
            {"detail": "Patient not found."}, status=status.HTTP_404_NOT_FOUND
        )

    requester = request.user

    if _is_admin(requester):
        return Response(UserSerializer(target).data)

    if requester.role in ("CLINIC_MANAGER", "DOCTOR"):
        shared_clinic = PatientClinic.objects.filter(
            patient__user=target,
            clinic__staff_clinics__staff__user=requester,
        ).exists()
        if not shared_clinic:
            return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)
        return Response(UserSerializer(target).data)

    return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def clinic_doctors_list(request):
    if request.method == "GET":
        if request.user.role != "CLINIC_MANAGER":
            return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)

        clinic_id = request.auth.get("active_clinic_id") if request.auth else None
        if not clinic_id:
            return Response(
                {"detail": "No active clinic in session."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        qs = (
            User.objects.filter(
                staff__staff_type="DOCTOR",
                staff__staff_clinics__clinic_id=clinic_id,
            )
            .distinct()
            .order_by("email")
        )
        paginator = PageNumberPagination()
        paginator.page_size = 20
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(UserSerializer(page, many=True).data)

    # POST — create doctor (clinic manager only)
    if request.user.role != "CLINIC_MANAGER":
        return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)

    clinic_id = request.auth.get("active_clinic_id") if request.auth else None
    if not clinic_id:
        return Response(
            {"detail": "No active clinic in session."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    data = request.data.copy()
    data["clinic_id"] = clinic_id

    serializer = CreateDoctorSerializer(data=data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        user = serializer.save()

    # send_welcome_email(user.email, user.full_name, serializer.generated_password)

    return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def research_patients_list(request):
    if request.method == "GET":
        if request.user.role not in ("DOCTOR", "CLINIC_MANAGER"):
            return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)

        clinic_id = request.auth.get("active_clinic_id") if request.auth else None
        if not clinic_id:
            return Response(
                {"detail": "No active clinic in session."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        qs = (
            User.objects.filter(
                role="RESEARCH_PATIENT",
                patient__patient_clinics__clinic_id=clinic_id,
            )
            .distinct()
            .order_by("email")
        )
        paginator = PageNumberPagination()
        paginator.page_size = 20
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(UserSerializer(page, many=True).data)

    # POST — create research patient (clinic manager only)
    if request.user.role != "CLINIC_MANAGER":
        return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)

    clinic_id = request.auth.get("active_clinic_id") if request.auth else None
    if not clinic_id:
        return Response(
            {"detail": "No active clinic in session."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    data = request.data.copy()
    data["clinic_id"] = clinic_id

    serializer = CreateResearchPatientSerializer(data=data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        user = serializer.save()

    return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    return Response(UserSerializer(request.user).data)


@api_view(["GET", "PUT", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def user_detail(request, user_id):
    try:
        target = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

    requester = request.user
    is_self = str(requester.id) == str(user_id)
    is_admin = _is_admin(requester)

    if not is_self and not is_admin:
        return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)

    if request.method == "GET":
        return Response(UserSerializer(target).data)

    if request.method in ("PUT", "PATCH"):
        partial = request.method == "PATCH"
        serializer = UserSerializer(target, data=request.data, partial=partial)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data)

    # DELETE
    if is_admin:
        target.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    else:
        # Non-admin: remove from clinic only
        clinic_id = _get_clinic_id(request)
        if clinic_id and target.role in ("PATIENT", "RESEARCH_PATIENT"):
            try:
                patient = target.patient
                PatientClinic.objects.filter(
                    patient=patient, clinic_id=clinic_id
                ).delete()
            except Exception:
                pass
        elif clinic_id and target.role in ("CLINIC_MANAGER", "DOCTOR"):
            try:
                staff = target.staff
                StaffClinic.objects.filter(staff=staff, clinic_id=clinic_id).delete()
            except Exception:
                pass
        return Response({"detail": "Removed from clinic."}, status=status.HTTP_200_OK)
