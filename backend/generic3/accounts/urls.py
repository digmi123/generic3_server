from django.urls import path
from . import views

urlpatterns = [
    path('sessions/', views.sessions, name='auth-sessions'),
    path('tokens/refresh/', views.token_refresh, name='auth-token-refresh'),
    path('2fa/', views.send_2fa, name='auth-2fa-send'),
    path('2fa/verify/', views.verify_2fa, name='auth-2fa-verify'),
    path('password/', views.change_password, name='auth-password'),
    path('users/<uuid:user_id>/qr-code/', views.totp_qr_code, name='auth-qr-code'),
]
