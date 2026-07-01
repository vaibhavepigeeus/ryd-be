import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def add_created_by_if_missing(apps, schema_editor):
    table = "form_pages"
    column = "created_by_id"

    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = %s AND column_name = %s
            """,
            [table, column],
        )
        if cursor.fetchone():
            return

    FormPage = apps.get_model("forms", "FormPage")
    User = apps.get_model("users", "Users")
    field = models.ForeignKey(
        blank=True,
        null=True,
        on_delete=django.db.models.deletion.SET_NULL,
        related_name="created_form_pages",
        to=User,
    )
    field.set_attributes_from_name("created_by")
    schema_editor.add_field(FormPage, field)


def remove_created_by_if_present(apps, schema_editor):
    table = "form_pages"
    column = "created_by_id"

    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = %s AND column_name = %s
            """,
            [table, column],
        )
        if not cursor.fetchone():
            return

    FormPage = apps.get_model("forms", "FormPage")
    field = FormPage._meta.get_field("created_by")
    schema_editor.remove_field(FormPage, field)


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("forms", "0005_formpagesubmission_submitted_by"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name="formpage",
                    name="created_by",
                    field=models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_form_pages",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            database_operations=[
                migrations.RunPython(
                    add_created_by_if_missing,
                    remove_created_by_if_present,
                ),
            ],
        ),
    ]
