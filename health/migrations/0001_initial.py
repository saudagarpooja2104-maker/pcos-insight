# Generated for the initial PCOS Insight health schema.
import django.core.validators
import django.db.models.deletion
import health.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="HealthProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date_of_birth", models.DateField(blank=True, null=True)),
                ("consent_to_health_data", models.BooleanField(default=False)),
                ("consent_updated_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="health_profile", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="CycleEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("period_start", models.DateField()),
                ("period_end", models.DateField(blank=True, null=True)),
                ("flow", models.CharField(blank=True, choices=[("light", "Light"), ("medium", "Medium"), ("heavy", "Heavy")], max_length=10)),
                ("notes", models.CharField(blank=True, max_length=500)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="cycle_entries", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-period_start"]},
        ),
        migrations.CreateModel(
            name="LifestyleEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("recorded_on", models.DateField()),
                ("sleep_hours", models.DecimalField(blank=True, decimal_places=1, max_digits=3, null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(24)])),
                ("activity_minutes", models.PositiveSmallIntegerField(blank=True, null=True, validators=[django.core.validators.MaxValueValidator(1440)])),
                ("mood", models.CharField(blank=True, choices=[("low", "Low"), ("okay", "Okay"), ("good", "Good")], max_length=12)),
                ("notes", models.CharField(blank=True, max_length=500)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="lifestyle_entries", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-recorded_on"]},
        ),
        migrations.CreateModel(
            name="SymptomEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("recorded_on", models.DateField()),
                ("symptom", models.CharField(max_length=80)),
                ("severity", models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ("notes", models.CharField(blank=True, max_length=500)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="symptom_entries", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-recorded_on", "symptom"]},
        ),
        migrations.CreateModel(
            name="UltrasoundImage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("image", models.ImageField(upload_to=health.models.ultrasound_upload_path)),
                ("study_date", models.DateField(blank=True, null=True)),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="ultrasound_images", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-uploaded_at"]},
        ),
        migrations.AddConstraint(
            model_name="cycleentry",
            constraint=models.UniqueConstraint(fields=("user", "period_start"), name="unique_user_period_start"),
        ),
    ]
