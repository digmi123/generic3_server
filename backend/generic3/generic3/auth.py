from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.exceptions import AuthenticationFailed


class CookieJWTAuthentication(JWTAuthentication):
    """Reads the JWT access token from the 'access' HTTP-only cookie."""

    def authenticate(self, request):
        raw_token = request.COOKIES.get('access')
        if raw_token is None:
            return None

        try:
            validated_token = self.get_validated_token(raw_token)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        try:
            user = self.get_user(validated_token)
        except AuthenticationFailed:
            return None

        return user, validated_token
