from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination

from .models import Clinic
from .serializers import ClinicSerializer


def _is_admin(user):
    return user.role == 'ADMIN' or user.is_staff


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def clinics_list(request):
    if request.method == 'GET':
        user = request.user
        if _is_admin(user):
            qs = Clinic.objects.all().order_by('clinic_name')
        elif user.role in ('CLINIC_MANAGER', 'DOCTOR'):
            try:
                clinic_ids = list(user.staff.staff_clinics.values_list('clinic_id', flat=True))
            except Exception:
                clinic_ids = []
            qs = Clinic.objects.filter(id__in=clinic_ids).order_by('clinic_name')
        elif user.role in ('PATIENT', 'RESEARCH_PATIENT'):
            try:
                clinic_ids = list(user.patient.patient_clinics.values_list('clinic_id', flat=True))
            except Exception:
                clinic_ids = []
            qs = Clinic.objects.filter(id__in=clinic_ids).order_by('clinic_name')
        else:
            return Response({'detail': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)

        paginator = PageNumberPagination()
        paginator.page_size = 20
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(ClinicSerializer(page, many=True).data)

    # POST
    if not _is_admin(request.user):
        return Response({'detail': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)

    serializer = ClinicSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def clinic_detail(request, clinic_id):
    try:
        clinic = Clinic.objects.get(id=clinic_id)
    except Clinic.DoesNotExist:
        return Response({'detail': 'Clinic not found.'}, status=status.HTTP_404_NOT_FOUND)

    user = request.user
    is_admin = _is_admin(user)

    # Check access for non-admin
    if not is_admin:
        if user.role in ('CLINIC_MANAGER', 'DOCTOR'):
            try:
                clinic_ids = list(user.staff.staff_clinics.values_list('clinic_id', flat=True))
            except Exception:
                clinic_ids = []
            if str(clinic.id) not in [str(c) for c in clinic_ids]:
                return Response({'detail': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)
        elif user.role in ('PATIENT', 'RESEARCH_PATIENT'):
            try:
                clinic_ids = list(user.patient.patient_clinics.values_list('clinic_id', flat=True))
            except Exception:
                clinic_ids = []
            if str(clinic.id) not in [str(c) for c in clinic_ids]:
                return Response({'detail': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        return Response(ClinicSerializer(clinic).data)

    if not is_admin:
        return Response({'detail': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'PUT':
        serializer = ClinicSerializer(clinic, data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data)

    # DELETE
    clinic.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
