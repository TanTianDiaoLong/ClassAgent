from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import timedelta
from typing import TYPE_CHECKING, Iterable

from django.utils import timezone

from .models import APIKey

if TYPE_CHECKING:
    from user.models import User


class ApiAuthError(Exception):
    """API 认证异常基类。"""


class InvalidApiKey(ApiAuthError):
    pass


class ExpiredApiKey(ApiAuthError):
    pass


class InactiveApiUser(ApiAuthError):
    pass


@dataclass(frozen=True)
class IssuedApiKey:
    raw: str
    key: APIKey


class ApiService:
    TOKEN_PREFIX = "ca_"
    DEFAULT_SCOPES = ("classroom:read",)
    DEFAULT_TTL_DAYS = 30

    @classmethod
    def issue(
        cls,
        *,
        user: User,
        name: str = "default",
        scopes: Iterable[str] | None = None,
        ttl_days: int | None = DEFAULT_TTL_DAYS,
    ) -> IssuedApiKey:
        """签发API密钥"""

        # format:
        prefix = f"{cls.TOKEN_PREFIX}{secrets.token_hex(8)}"
        secret = secrets.token_urlsafe(32)
        raw = f"{prefix}.{secret}"

        expires_at = None
        if ttl_days is not None:
            expires_at = timezone.now() + timedelta(days=ttl_days)

        key = APIKey.objects.create_key(
            user=user,
            name=name,
            prefix=prefix,
            hashed_key=cls._hash(secret),
            scopes=list(scopes or cls.DEFAULT_SCOPES),
            expires_at=expires_at,
        )
        return IssuedApiKey(raw=raw, key=key)

    @classmethod
    def verify(cls, raw: str) -> User:
        prefix, sep, secret = raw.partition(".")
        if not sep or not prefix or not secret:
            raise InvalidApiKey("Malformed API key")

        key = APIKey.objects.get_active_by_prefix(prefix)
        if key is None:
            raise InvalidApiKey("Unknown API key")

        if not secrets.compare_digest(key.hashed_key, cls._hash(secret)):
            raise InvalidApiKey("Invalid API key")

        if key.expires_at and key.expires_at <= timezone.now():
            raise ExpiredApiKey("API key expired")

        if not key.user.is_active:
            raise InactiveApiUser("User is inactive")

        APIKey.objects.touch(key)
        return key.user

    @classmethod
    def revoke(cls, key: APIKey) -> None:
        APIKey.objects.revoke(key)

    @classmethod
    def _hash(cls, secret: str) -> str:
        return hashlib.sha256(secret.encode()).hexdigest()
