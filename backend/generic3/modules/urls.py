from django.urls import path
from . import views

urlpatterns = [
    path('', views.modules_list, name='modules-list'),
    path('<uuid:module_id>/', views.module_detail, name='module-detail'),
]
