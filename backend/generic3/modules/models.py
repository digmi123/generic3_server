import uuid
from django.db import models


class Module(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module_name = models.CharField(max_length=150)
    module_description = models.TextField()

    def __str__(self):
        return self.module_name


class ClinicModule(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    clinic = models.ForeignKey('clinics.Clinic', on_delete=models.CASCADE, related_name='clinic_modules')
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='clinic_modules')
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('clinic', 'module')

    def __str__(self):
        return f'{self.clinic} — {self.module}'


