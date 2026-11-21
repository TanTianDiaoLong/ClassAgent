from datetime import timedelta

from django.db import models
from django.utils import timezone


class APIKeyManager(models.Manager):
    """APIKey 的数据库读写入口。"""

    def create_key(
        self,
        *,
        user,
        name,
        prefix,
        hashed_key,
        scopes,
        expires_at=None,
    ):
        return self.create(
            user=user,
            name=name,
            prefix=prefix,
            hashed_key=hashed_key,
            scopes=scopes,
            expires_at=expires_at,
        )

    def get_active_by_prefix(self, prefix):
        return (
            self.get_queryset()
            .select_related("user")
            .filter(
                prefix=prefix,
                revoked_at__isnull=True,
            )
            .first()
        )

    def revoke(self, key):
        if key.revoked_at is None:
            key.revoked_at = timezone.now()
            key.save(update_fields=["revoked_at"])

    def touch(self, key, *, threshold_minutes=5):
        now = timezone.now()

        if (
            key.last_used_at is None
            or now - key.last_used_at > timedelta(minutes=threshold_minutes)
        ):
            self.get_queryset().filter(pk=key.pk).update(last_used_at=now)
            key.last_used_at = now

    def for_user(self, user):
        return self.filter(user=user)
