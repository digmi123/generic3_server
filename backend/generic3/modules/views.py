from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Module, ClinicModule
from .serializers import ModuleSerializer, ClinicModuleSerializer
from clinics.models import Clinic


def _is_admin(user):
    return user.role == 'ADMIN' or user.is_staff


def _is_staff(user):
    return user.role in ('ADMIN', 'CLINIC_MANAGER', 'DOCTOR') or user.is_staff


# ── Global modules ─────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def modules_list(request):
    if request.method == 'GET':
        if not _is_staff(request.user):
            return Response({'detail': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)
        qs = Module.objects.all().order_by('module_name')
        return Response(ModuleSerializer(qs, many=True).data)

    if not _is_admin(request.user):
        return Response({'detail': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)
    serializer = ModuleSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def module_detail(request, module_id):
    try:
        module = Module.objects.get(id=module_id)
    except Module.DoesNotExist:
        return Response({'detail': 'Module not found.'}, status=status.HTTP_404_NOT_FOUND)

    if not _is_staff(request.user):
        return Response({'detail': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        return Response(ModuleSerializer(module).data)

    if not _is_admin(request.user):
        return Response({'detail': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)

    if request.method in ('PUT', 'PATCH'):
        serializer = ModuleSerializer(module, data=request.data, partial=(request.method == 'PATCH'))
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data)

    module.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# ── Clinic modules ─────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def clinic_modules_list(request, clinic_id):
    try:
        clinic = Clinic.objects.get(id=clinic_id)
    except Clinic.DoesNotExist:
        return Response({'detail': 'Clinic not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        qs = ClinicModule.objects.filter(clinic=clinic).select_related('module')
        return Response(ClinicModuleSerializer(qs, many=True).data)

    if not _is_admin(request.user):
        return Response({'detail': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)

    module_id = request.data.get('module_id')
    try:
        module = Module.objects.get(id=module_id)
    except Module.DoesNotExist:
        return Response({'detail': 'Module not found.'}, status=status.HTTP_404_NOT_FOUND)

    cm, created = ClinicModule.objects.get_or_create(clinic=clinic, module=module)
    return Response(ClinicModuleSerializer(cm).data,
                    status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def clinic_module_detail(request, clinic_id, module_id):
    try:
        cm = ClinicModule.objects.get(clinic_id=clinic_id, module_id=module_id)
    except ClinicModule.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(ClinicModuleSerializer(cm).data)

    if not _is_admin(request.user):
        return Response({'detail': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'PATCH':
        is_active = request.data.get('is_active')
        if is_active is not None:
            cm.is_active = is_active
            cm.save()
        return Response(ClinicModuleSerializer(cm).data)

    cm.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


