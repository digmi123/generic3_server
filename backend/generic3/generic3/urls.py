from django.contrib import admin
from django.urls import path, include
from modules.urls import clinic_urlpatterns as module_clinic_urlpatterns
from medications.urls import clinic_urlpatterns as medication_clinic_urlpatterns

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('accounts.urls')),
    path('api/v1/users/', include('users.urls')),
    path('api/v1/clinics/', include('clinics.urls')),
    path('api/v1/modules/', include('modules.urls')),
    path('api/v1/clinics/', include(module_clinic_urlpatterns)),
    path('api/v1/medications/', include('medications.urls')),
    path('api/v1/clinics/', include(medication_clinic_urlpatterns)),
]
