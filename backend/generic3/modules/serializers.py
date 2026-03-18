from rest_framework import serializers
from .models import Module, ClinicModule


class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = ['id', 'module_name', 'module_description']


class ClinicModuleSerializer(serializers.ModelSerializer):
    module_name = serializers.CharField(source='module.module_name', read_only=True)
    module_description = serializers.CharField(source='module.module_description', read_only=True)

    class Meta:
        model = ClinicModule
        fields = ['id', 'clinic', 'module', 'module_name', 'module_description', 'is_active']
        read_only_fields = ['id', 'clinic']
