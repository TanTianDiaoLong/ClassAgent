from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .services import ApiAuthError, ApiService


class APIKeyAuthentication(BaseAuthentication):
    def authenticate(self, request):
        raw = self._get_raw_token(request)
        if raw is None:
            return None

        try:
            user = ApiService.verify(raw)
        except ApiAuthError as exc:
            raise AuthenticationFailed(str(exc)) from exc

        return user, None

    def authenticate_header(self, request):
        """
        请求头：
        Authorization: Bearer ca_180f...S5I

        """
        return "Bearer"

    def _get_raw_token(self, request) -> str | None:
        header = request.headers.get("Authorization", "")
        parts = header.split()

        if not parts:
            return None

        if parts[0].lower() != "bearer" or len(parts) != 2:
            raise AuthenticationFailed("Invalid authorization header")

        return parts[1]
