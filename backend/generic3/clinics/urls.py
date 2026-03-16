from django.urls import path
from . import views

urlpatterns = [
    path('', views.clinics_list, name='clinics-list'),
    path('<uuid:clinic_id>/', views.clinic_detail, name='clinic-detail'),
]
