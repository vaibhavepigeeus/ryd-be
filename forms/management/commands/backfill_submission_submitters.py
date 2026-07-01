from django.core.management.base import BaseCommand, CommandError

from forms.models import FormPageSubmission
from users.models import Users


class Command(BaseCommand):
    help = (
        "Assign submitted_by on legacy submissions that were saved before "
        "identity tracking was added."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--user-id",
            type=int,
            required=True,
            help="User id to assign as the submitter.",
        )
        parser.add_argument(
            "--submission-ids",
            nargs="+",
            type=int,
            help="Specific submission ids to update.",
        )
        parser.add_argument(
            "--page-id",
            type=int,
            help="Update all submissions with no submitter on this page.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would change without saving.",
        )

    def handle(self, *args, **options):
        user_id = options["user_id"]
        submission_ids = options.get("submission_ids")
        page_id = options.get("page_id")
        dry_run = options["dry_run"]

        if not submission_ids and not page_id:
            raise CommandError("Provide --submission-ids and/or --page-id.")

        try:
            user = Users.objects.get(pk=user_id)
        except Users.DoesNotExist as exc:
            raise CommandError(f"User {user_id} not found.") from exc

        queryset = FormPageSubmission.objects.filter(submitted_by__isnull=True)

        if submission_ids:
            queryset = queryset.filter(id__in=submission_ids)
        if page_id:
            queryset = queryset.filter(page_id=page_id)

        submissions = list(queryset.order_by("id"))
        if not submissions:
            self.stdout.write(self.style.WARNING("No matching legacy submissions found."))
            return

        self.stdout.write(
            f"{'Would update' if dry_run else 'Updating'} {len(submissions)} "
            f"submission(s) -> {user.user_name} ({user.id})"
        )

        for submission in submissions:
            self.stdout.write(
                f"  #{submission.id} page={submission.page_id} "
                f"submitted_at={submission.submitted_at}"
            )

        if dry_run:
            return

        updated = queryset.update(submitted_by=user)
        self.stdout.write(self.style.SUCCESS(f"Updated {updated} submission(s)."))
