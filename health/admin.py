from django.contrib import admin

from .models import CycleEntry, HealthProfile, LifestyleEntry, SymptomEntry


@admin.register(HealthProfile)
class HealthProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "consent_to_health_data", "consent_updated_at")
    search_fields = ("user__username", "user__email")


@admin.register(CycleEntry)
class CycleEntryAdmin(admin.ModelAdmin):
    list_display = ("user", "period_start", "period_end", "flow")
    list_filter = ("flow",)
    search_fields = ("user__username",)


@admin.register(SymptomEntry)
class SymptomEntryAdmin(admin.ModelAdmin):
    list_display = ("user", "recorded_on", "symptom", "severity")
    list_filter = ("symptom", "severity")


@admin.register(LifestyleEntry)
class LifestyleEntryAdmin(admin.ModelAdmin):
    list_display = ("user", "recorded_on", "sleep_hours", "activity_minutes", "mood")
    list_filter = ("mood",)
