from django.contrib import admin
from django.urls import path, include
from modules import views as module_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('accounts.urls')),
    path('api/v1/users/', include('users.urls')),
    path('api/v1/clinics/', include('clinics.urls')),
    path('api/v1/modules/', include('modules.urls')),
    # Nested clinic modules
    path('api/v1/clinics/<uuid:clinic_id>/modules/',
         module_views.clinic_modules_list, name='clinic-modules-list'),
    path('api/v1/clinics/<uuid:clinic_id>/modules/<uuid:module_id>/',
         module_views.clinic_module_detail, name='clinic-module-detail'),
    # Nested patient modules
    path('api/v1/clinics/<uuid:clinic_id>/patients/<uuid:patient_id>/modules/',
         module_views.patient_modules_list, name='patient-modules-list'),
    path('api/v1/clinics/<uuid:clinic_id>/patients/<uuid:patient_id>/modules/<uuid:module_id>/',
         module_views.patient_module_detail, name='patient-module-detail'),
]
