from django.conf import settings
from django.db import models

from .managers import APIKeyManager


class APIKey(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="api_keys",
    )
    name = models.CharField(max_length=64)
    prefix = models.CharField(
        max_length=32,
        default="ca_",
        unique=True
    )
    hashed_key = models.CharField(
        max_length=64,
        unique=True
    )

    scopes = models.JSONField(
        default=list,
        blank=True
    )

    expires_at = models.DateTimeField(
        null=True,
        blank=True
    )
    revoked_at = models.DateTimeField(
        null=True,
        blank=True
    )
    last_used_at = models.DateTimeField(
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    objects = APIKeyManager()

    def __str__(self):
        return f"{self.name} ({self.prefix})"
