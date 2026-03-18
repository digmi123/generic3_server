from rest_framework import serializers
from .models import Medication, ClinicMedication, PatientMedication, MedicationLog


class MedicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medication
        fields = ['id', 'med_name', 'med_form', 'med_unit']


class ClinicMedicationSerializer(serializers.ModelSerializer):
    med_name = serializers.CharField(source='medication.med_name', read_only=True)
    med_form = serializers.CharField(source='medication.med_form', read_only=True)
    med_unit = serializers.CharField(source='medication.med_unit', read_only=True)

    class Meta:
        model = ClinicMedication
        fields = ['id', 'clinic', 'medication', 'med_name', 'med_form', 'med_unit']
        read_only_fields = ['id', 'clinic']


class PatientMedicationSerializer(serializers.ModelSerializer):
    med_name = serializers.CharField(source='medication.med_name', read_only=True)
    med_form = serializers.CharField(source='medication.med_form', read_only=True)
    med_unit = serializers.CharField(source='medication.med_unit', read_only=True)

    class Meta:
        model = PatientMedication
        fields = [
            'id', 'patient', 'clinic', 'doctor', 'medication',
            'med_name', 'med_form', 'med_unit',
            'start_date', 'end_date', 'dosage', 'frequency', 'frequency_data',
        ]
        read_only_fields = ['id', 'patient', 'clinic']


class MedicationLogSerializer(serializers.ModelSerializer):
    med_name = serializers.CharField(source='patient_medication.medication.med_name', read_only=True)

    class Meta:
        model = MedicationLog
        fields = ['id', 'patient_medication', 'patient', 'med_name', 'taken_at', 'dosage_taken', 'status']
        read_only_fields = ['id', 'patient']
