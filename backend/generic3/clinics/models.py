import uuid
from django.db import models


class Clinic(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    clinic_name = models.CharField(max_length=255, unique=True)
    clinic_url = models.URLField(unique=True)
    clinic_image_url = models.URLField(null=True, blank=True)
    is_research_clinic = models.BooleanField(default=False)

    def __str__(self):
        return self.clinic_name
