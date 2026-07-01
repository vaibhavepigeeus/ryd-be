from django.core.management.base import BaseCommand
from django.utils import timezone

from users.auth_helpers import find_user_by_email
from users.constants import UserRole
from users.models import Users


class Command(BaseCommand):
    help = "Create an admin user account"

    def add_arguments(self, parser):
        parser.add_argument("--email", required=True, help="Admin email address")
        parser.add_argument("--name", required=True, help="Admin display name")
        parser.add_argument("--password", required=True, help="Admin password")

    def handle(self, *args, **options):
        email = options["email"].lower().strip()
        user_name = options["name"].strip()
        password = options["password"]

        if find_user_by_email(email, require_active=False):
            self.stderr.write(self.style.ERROR(f"A user with email {email} already exists."))
            return

        Users.objects.create_user(
            email=email,
            password=password,
            user_name=user_name,
            role=UserRole.ADMIN,
            status="Active",
            user_start_date=timezone.now(),
        )
        self.stdout.write(self.style.SUCCESS(f"Admin user '{user_name}' created successfully."))
