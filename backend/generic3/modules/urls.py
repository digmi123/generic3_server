from django.urls import path
from . import views

urlpatterns = [
    path('', views.modules_list, name='modules-list'),
    path('<uuid:module_id>/', views.module_detail, name='module-detail'),
]

# Included under api/v1/clinics/ in the main urls.py
clinic_urlpatterns = [
    path('<uuid:clinic_id>/modules/', views.clinic_modules_list, name='clinic-modules-list'),
    path('<uuid:clinic_id>/modules/<uuid:module_id>/', views.clinic_module_detail, name='clinic-module-detail'),
]
