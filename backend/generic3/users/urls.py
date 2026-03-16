from django.urls import path
from . import views

urlpatterns = [
    path('', views.users_list, name='users-list'),
    path('me/', views.me, name='users-me'),
    path('clinic-managers/', views.clinic_managers_list, name='users-clinic-managers'),
    path('patients/', views.clinic_patients_list, name='users-clinic-patients'),
    path('patients/<uuid:user_id>/', views.patient_detail, name='users-patient-detail'),
    path('doctors/', views.clinic_doctors_list, name='users-clinic-doctors'),
    path('<uuid:user_id>/', views.user_detail, name='user-detail'),
]
