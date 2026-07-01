# Generated manually for submitted_by on FormPageSubmission

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('forms', '0004_formquestion_sequence_no'),
    ]

    operations = [
        migrations.AddField(
            model_name='formpagesubmission',
            name='submitted_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='form_submissions',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
