from django.urls import path
from . import views

urlpatterns = [
    path("", views.medications_list, name="medications-list"),
    path("<uuid:medication_id>/", views.medication_detail, name="medication-detail"),
]

# Included under api/v1/clinics/ in the main urls.py
clinic_urlpatterns = [
    path(
        "<uuid:clinic_id>/medications/",
        views.clinic_medications_list,
        name="clinic-medications-list",
    ),
    path(
        "<uuid:clinic_id>/medications/<uuid:medication_id>/",
        views.clinic_medication_detail,
        name="clinic-medication-detail",
    ),
    path(
        "<uuid:clinic_id>/patients/<uuid:user_id>/medication-logs/",
        views.patient_all_medication_logs,
        name="patient-all-medication-logs",
    ),
    path(
        "<uuid:clinic_id>/patients/<uuid:user_id>/medications/",
        views.patient_medications_list,
        name="patient-medications-list",
    ),
    path(
        "<uuid:clinic_id>/patients/<uuid:user_id>/medications/<uuid:medication_record_id>/",
        views.patient_medication_detail,
        name="patient-medication-detail",
    ),
    path(
        "<uuid:clinic_id>/patients/<uuid:user_id>/medications/<uuid:medication_record_id>/logs/",
        views.medication_logs_list,
        name="medication-logs-list",
    ),
    path(
        "<uuid:clinic_id>/patients/<uuid:user_id>/medications/<uuid:medication_record_id>/logs/<uuid:log_id>/",
        views.medication_log_detail,
        name="medication-log-detail",
    ),
]
