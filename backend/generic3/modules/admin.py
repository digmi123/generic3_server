from django.contrib import admin
from .models import Module, ClinicModule, PatientModule

admin.site.register(Module)
admin.site.register(ClinicModule)
admin.site.register(PatientModule)
