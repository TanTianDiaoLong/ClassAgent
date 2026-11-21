from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from api.services import ApiService


class Command(BaseCommand):
    help = "Create an API key for a user"

    def add_arguments(self, parser):
        parser.add_argument("user_id")
        parser.add_argument("--name", default="default")
        parser.add_argument(
            "--scopes",
            nargs="*",
            default=list(ApiService.DEFAULT_SCOPES),
        )
        parser.add_argument(
            "--ttl-days",
            type=int,
            default=ApiService.DEFAULT_TTL_DAYS,
        )

    def handle(self, *args, **options):
        User = get_user_model()

        try:
            user = User.objects.get(user_id=options["user_id"])
        except User.DoesNotExist as exc:
            raise CommandError(
                f"User not found: {options['user_id']}"
            ) from exc

        issued = ApiService.issue(
            user=user,
            name=options["name"],
            scopes=options["scopes"],
            ttl_days=options["ttl_days"],
        )

        self.stdout.write(self.style.SUCCESS(issued.raw))
