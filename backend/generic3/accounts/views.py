from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.conf import settings
from generic3.utils import send_2fa_code, verify_2fa_code, setup_totp
from users.serializers import UserSerializer

User = get_user_model()

JWT_SETTINGS = settings.SIMPLE_JWT
ACCESS_COOKIE = JWT_SETTINGS.get('AUTH_COOKIE', 'access')
REFRESH_COOKIE = JWT_SETTINGS.get('REFRESH_COOKIE', 'refresh')


def _set_jwt_cookies(response, refresh):
    access = str(refresh.access_token)
    response.set_cookie(
        ACCESS_COOKIE, access,
        httponly=True,
        samesite=JWT_SETTINGS.get('AUTH_COOKIE_SAMESITE', 'Lax'),
        max_age=int(JWT_SETTINGS['ACCESS_TOKEN_LIFETIME'].total_seconds()),
    )
    response.set_cookie(
        REFRESH_COOKIE, str(refresh),
        httponly=True,
        samesite=JWT_SETTINGS.get('AUTH_COOKIE_SAMESITE', 'Lax'),
        max_age=int(JWT_SETTINGS['REFRESH_TOKEN_LIFETIME'].total_seconds()),
    )


def _clear_jwt_cookies(response):
    response.delete_cookie(ACCESS_COOKIE)
    response.delete_cookie(REFRESH_COOKIE)


def _build_user_payload(user):
    return {'user': UserSerializer(user).data}


@api_view(['POST', 'DELETE'])
@permission_classes([AllowAny])
def sessions(request):
    if request.method == 'POST':
        email = request.data.get('email')
        password = request.data.get('password')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'detail': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.check_password(password):
            return Response({'detail': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_active:
            return Response({'detail': 'Account is disabled.'}, status=status.HTTP_403_FORBIDDEN)

        if user.is_2fa_enabled:
            send_2fa_code(user)
            return Response({'detail': '2FA code sent.', 'user_id': str(user.id), 'requires_2fa': True},
                            status=status.HTTP_200_OK)

        refresh = RefreshToken.for_user(user)
        payload = _build_user_payload(user)
        response = Response(payload, status=status.HTTP_200_OK)
        _set_jwt_cookies(response, refresh)
        return response

    # DELETE — logout
    response = Response({'detail': 'Logged out.'}, status=status.HTTP_200_OK)
    _clear_jwt_cookies(response)
    return response


@api_view(['POST'])
@permission_classes([AllowAny])
def token_refresh(request):
    refresh_token = request.COOKIES.get(REFRESH_COOKIE)
    if not refresh_token:
        return Response({'detail': 'Refresh token not found.'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        refresh = RefreshToken(refresh_token)
        response = Response({'detail': 'Token refreshed.'}, status=status.HTTP_200_OK)
        _set_jwt_cookies(response, refresh)
        return response
    except TokenError as e:
        return Response({'detail': str(e)}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([AllowAny])
def send_2fa(request):
    user_id = request.data.get('user_id')
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
    send_2fa_code(user)
    return Response({'detail': '2FA code sent.'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_2fa(request):
    user_id = request.data.get('user_id')
    code = request.data.get('code')
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

    if not verify_2fa_code(user, code):
        return Response({'detail': 'Invalid or expired code.'}, status=status.HTTP_400_BAD_REQUEST)

    refresh = RefreshToken.for_user(user)
    payload = _build_user_payload(user)
    response = Response(payload, status=status.HTTP_200_OK)
    _set_jwt_cookies(response, refresh)
    return response


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def change_password(request):
    user = request.user
    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')

    if not user.check_password(old_password):
        return Response({'detail': 'Wrong current password.'}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(new_password)
    user.save()
    return Response({'detail': 'Password changed.'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def totp_qr_code(request, user_id):
    if not request.user.is_staff and str(request.user.id) != str(user_id):
        return Response({'detail': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

    device = setup_totp(user)
    uri = device.config_url
    return Response({'otpauth_uri': uri}, status=status.HTTP_200_OK)
