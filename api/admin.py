from django.contrib import admin

from .models import APIKey


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "prefix",
        "user",
        "scopes",
        "expires_at",
        "revoked_at",
        "last_used_at",
        "created_at",
    )
    list_filter = ("revoked_at", "expires_at")
    search_fields = ("name", "prefix", "user__user_id")
    readonly_fields = ("prefix", "created_at", "last_used_at")
    exclude = ("hashed_key",)

    def has_add_permission(self, request):
        return False
