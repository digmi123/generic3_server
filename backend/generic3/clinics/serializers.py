from rest_framework import serializers
from .models import Clinic


class ClinicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clinic
        fields = ['id', 'clinic_name', 'clinic_url', 'clinic_image_url', 'is_research_clinic']
