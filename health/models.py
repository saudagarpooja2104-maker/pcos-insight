from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from uuid import uuid4


def ultrasound_upload_path(instance, filename):
    return f"ultrasound/{instance.user_id}/{uuid4().hex}.jpg"


class HealthProfile(models.Model):
    """Optional profile fields; only collect details the user chooses to provide."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="health_profile")
    date_of_birth = models.DateField(null=True, blank=True)
    consent_to_health_data = models.BooleanField(default=False)
    consent_updated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Health profile for user {self.user_id}"


class CycleEntry(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cycle_entries")
    period_start = models.DateField()
    period_end = models.DateField(null=True, blank=True)
    flow = models.CharField(max_length=10, choices=[("light", "Light"), ("medium", "Medium"), ("heavy", "Heavy")], blank=True)
    notes = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-period_start"]
        constraints = [models.UniqueConstraint(fields=["user", "period_start"], name="unique_user_period_start")]

    def __str__(self):
        return f"Cycle entry for user {self.user_id} on {self.period_start}"


class SymptomEntry(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="symptom_entries")
    recorded_on = models.DateField()
    symptom = models.CharField(max_length=80)
    severity = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    notes = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-recorded_on", "symptom"]

    def __str__(self):
        return f"{self.symptom} entry for user {self.user_id} on {self.recorded_on}"


class LifestyleEntry(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="lifestyle_entries")
    recorded_on = models.DateField()
    sleep_hours = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(24)])
    activity_minutes = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MaxValueValidator(1440)])
    mood = models.CharField(max_length=12, choices=[("low", "Low"), ("okay", "Okay"), ("good", "Good")], blank=True)
    notes = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-recorded_on"]

    def __str__(self):
        return f"Lifestyle entry for user {self.user_id} on {self.recorded_on}"


class UltrasoundImage(models.Model):
    """Private, metadata-stripped image intake; no diagnostic result is produced."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ultrasound_images")
    image = models.ImageField(upload_to=ultrasound_upload_path)
    study_date = models.DateField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"Ultrasound image for user {self.user_id}"


@receiver(post_delete, sender=UltrasoundImage)
def delete_ultrasound_file(sender, instance, **kwargs):
    if instance.image:
        instance.image.delete(save=False)
