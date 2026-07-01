from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_coach_coachee_link'),
    ]

    operations = [
        migrations.AlterField(
            model_name='users',
            name='role',
            field=models.CharField(
                choices=[
                    ('admin', 'Admin'),
                    ('coach', 'Coach'),
                    ('coachee', 'Coachee'),
                ],
                max_length=100,
            ),
        ),
    ]
