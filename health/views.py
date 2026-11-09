import calendar
from datetime import date, timedelta
from io import BytesIO
from statistics import mean

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.db.models import Avg, Count, Q
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from PIL import Image, ImageOps

from .forms import AccountDeleteForm, CycleEntryForm, HealthProfileForm, LifestyleEntryForm, RegistrationForm, ReportRangeForm, SymptomEntryForm, UltrasoundImageForm
from .models import CycleEntry, HealthProfile, LifestyleEntry, SymptomEntry, UltrasoundImage
from .reports import build_health_report
from .csv_exports import build_health_csv

ENTRY_TYPES = {
    "cycle": (CycleEntry, CycleEntryForm, "cycle entry"),
    "symptom": (SymptomEntry, SymptomEntryForm, "symptom entry"),
    "lifestyle": (LifestyleEntry, LifestyleEntryForm, "lifestyle note"),
}


def home(request):
    return render(request, "health/home.html")


def learning_hub(request):
    return render(request, "health/learn.html")


@login_required
@never_cache
def account_profile(request):
    profile, _ = HealthProfile.objects.get_or_create(user=request.user)
    form = HealthProfileForm(instance=profile)
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "save_profile":
            if not profile.consent_to_health_data:
                messages.error(request, "Turn on health-data consent before saving profile health information.")
            else:
                form = HealthProfileForm(request.POST, instance=profile)
                if form.is_valid():
                    form.save()
                    messages.success(request, "Your profile was updated.")
                    return redirect("account_profile")
        elif action == "withdraw_consent":
            profile.consent_to_health_data = False
            profile.consent_updated_at = timezone.now()
            profile.save(update_fields=["consent_to_health_data", "consent_updated_at", "updated_at"])
            messages.info(request, "Health-data consent is off. Existing records stay in your account until you delete them.")
            return redirect("account_profile")
        elif action == "restore_consent" and request.POST.get("health_data_consent") == "on":
            profile.consent_to_health_data = True
            profile.consent_updated_at = timezone.now()
            profile.save(update_fields=["consent_to_health_data", "consent_updated_at", "updated_at"])
            messages.success(request, "Health-data consent is on. You can choose to record new information.")
            return redirect("account_profile")
        elif action == "restore_consent":
            messages.error(request, "Select the consent box before continuing.")

    return render(request, "health/profile.html", {
        "profile": profile,
        "form": form,
        "cycle_count": CycleEntry.objects.filter(user=request.user).count(),
        "symptom_count": SymptomEntry.objects.filter(user=request.user).count(),
        "lifestyle_count": LifestyleEntry.objects.filter(user=request.user).count(),
        "ultrasound_count": UltrasoundImage.objects.filter(user=request.user).count(),
    })


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        HealthProfile.objects.create(
            user=user,
            consent_to_health_data=True,
            consent_updated_at=timezone.now(),
        )
        login(request, user)
        messages.success(request, "Your account is ready. You can now add health records when you choose.")
        return redirect("dashboard")
    return render(request, "health/register.html", {"form": form})


@login_required
@never_cache
def dashboard(request):
    user = request.user
    profile, _ = HealthProfile.objects.get_or_create(user=user)
    cycle_form = CycleEntryForm(prefix="cycle")
    symptom_form = SymptomEntryForm(prefix="symptom")
    lifestyle_form = LifestyleEntryForm(prefix="lifestyle")

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "withdraw_consent":
            profile.consent_to_health_data = False
            profile.consent_updated_at = timezone.now()
            profile.save(update_fields=["consent_to_health_data", "consent_updated_at", "updated_at"])
            messages.info(request, "Health-data storage consent is off. Existing records remain in your account.")
            return redirect("dashboard")

        if action == "restore_consent":
            if request.POST.get("health_data_consent") == "on":
                profile.consent_to_health_data = True
                profile.consent_updated_at = timezone.now()
                profile.save(update_fields=["consent_to_health_data", "consent_updated_at", "updated_at"])
                messages.success(request, "Health-data consent is on. You can now choose to add new records.")
            else:
                messages.error(request, "Select the consent box before continuing.")
            return redirect("dashboard")

        if not profile.consent_to_health_data:
            messages.error(request, "Health-data consent is off. Review the notice below before recording more information.")
            return redirect("dashboard")

        form_map = {
            "cycle": (CycleEntryForm, "cycle_form"),
            "symptom": (SymptomEntryForm, "symptom_form"),
            "lifestyle": (LifestyleEntryForm, "lifestyle_form"),
        }
        if action in form_map:
            form_class, context_key = form_map[action]
            form_kwargs = {"prefix": action}
            if action == "cycle":
                form_kwargs["user"] = user
            form = form_class(request.POST, **form_kwargs)
            if form.is_valid():
                entry = form.save(commit=False)
                entry.user = user
                entry.save()
                messages.success(request, "Your entry has been saved to your account.")
                return redirect("dashboard")
            if context_key == "cycle_form":
                cycle_form = form
            elif context_key == "symptom_form":
                symptom_form = form
            else:
                lifestyle_form = form

    recent_cycles = list(CycleEntry.objects.filter(user=user)[:8])
    ordered_cycles = list(reversed(recent_cycles))
    cycle_intervals = [
        {
            "label": f"{ordered_cycles[index - 1].period_start:%d %b} to {ordered_cycles[index].period_start:%d %b}",
            "days": (ordered_cycles[index].period_start - ordered_cycles[index - 1].period_start).days,
        }
        for index in range(1, len(ordered_cycles))
    ]
    recent_symptoms = list(SymptomEntry.objects.filter(user=user)[:6])
    symptom_chart = [
        {
            "label": f"{entry.recorded_on:%d %b} · {entry.symptom}",
            "severity": entry.severity,
        }
        for entry in reversed(recent_symptoms)
    ]
    cycle_interval_summary = None
    if cycle_intervals:
        interval_values = [item["days"] for item in cycle_intervals]
        cycle_interval_summary = {
            "count": len(interval_values),
            "average": round(mean(interval_values), 1),
            "shortest": min(interval_values),
            "longest": max(interval_values),
        }
    symptom_summary_start = timezone.localdate() - timedelta(days=29)
    symptom_summary = SymptomEntry.objects.filter(
        user=user,
        recorded_on__range=(symptom_summary_start, timezone.localdate()),
    ).values("symptom").annotate(
        count=Count("id"), average_severity=Avg("severity"),
    ).order_by("-count", "symptom")[:5]

    return render(request, "health/dashboard.html", {
        "profile": profile,
        "cycle_form": cycle_form,
        "symptom_form": symptom_form,
        "lifestyle_form": lifestyle_form,
        "cycle_entries": recent_cycles,
        "cycle_intervals": cycle_intervals,
        "cycle_interval_summary": cycle_interval_summary,
        "symptom_chart": symptom_chart,
        "symptom_summary": symptom_summary,
        "symptom_summary_start": symptom_summary_start,
        "symptom_entries": recent_symptoms,
        "lifestyle_entries": LifestyleEntry.objects.filter(user=user)[:6],
    })


@login_required
@never_cache
def cycle_calendar(request):
    today = timezone.localdate()
    month_value = request.GET.get("month", "")
    try:
        month_start = date.fromisoformat(f"{month_value}-01")
        if month_start.strftime("%Y-%m") != month_value or not 1900 <= month_start.year <= 2100:
            raise ValueError
    except (TypeError, ValueError):
        month_start = today.replace(day=1)

    month_end = month_start.replace(day=calendar.monthrange(month_start.year, month_start.month)[1])
    month_entries = list(CycleEntry.objects.filter(user=request.user, period_start__lte=month_end).filter(
        Q(period_end__gte=month_start) | Q(period_start__gte=month_start)
    ))
    day_entries = {}
    for entry in month_entries:
        period_day = max(entry.period_start, month_start)
        last_day = min(entry.period_end or entry.period_start, month_end)
        while period_day <= last_day:
            day_entries.setdefault(period_day, []).append({
                "is_start": period_day == entry.period_start,
                "is_end": entry.period_end is not None and period_day == entry.period_end,
            })
            period_day += timedelta(days=1)

    weeks = [
        [{"date": day, "in_month": day.month == month_start.month, "events": day_entries.get(day, [])} for day in week]
        for week in calendar.Calendar(firstweekday=0).monthdatescalendar(month_start.year, month_start.month)
    ]
    previous_month = (
        date(month_start.year - 1, 12, 1) if month_start.month == 1 and month_start.year > 1
        else date(month_start.year, month_start.month - 1, 1) if month_start.month > 1
        else None
    )
    next_month = (
        date(month_start.year + 1, 1, 1) if month_start.month == 12 and month_start.year < 9999
        else date(month_start.year, month_start.month + 1, 1) if month_start.month < 12
        else None
    )
    return render(request, "health/cycle_calendar.html", {
        "month_start": month_start,
        "month_label": f"{calendar.month_name[month_start.month]} {month_start.year}",
        "weekdays": list(calendar.day_name),
        "weeks": weeks,
        "month_entries": month_entries,
        "previous_month": previous_month.strftime("%Y-%m") if previous_month else None,
        "next_month": next_month.strftime("%Y-%m") if next_month else None,
        "current_month": today.strftime("%Y-%m"),
    })


@login_required
@never_cache
def health_report(request):
    form = ReportRangeForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        start = form.cleaned_data["start_date"]
        end = form.cleaned_data["end_date"]
        cycle_entries = CycleEntry.objects.filter(user=request.user, period_start__range=(start, end))
        symptom_entries = SymptomEntry.objects.filter(user=request.user, recorded_on__range=(start, end))
        lifestyle_entries = LifestyleEntry.objects.filter(user=request.user, recorded_on__range=(start, end))
        if request.POST.get("export_format") == "csv":
            csv_text = build_health_csv(cycle_entries, symptom_entries, lifestyle_entries)
            response = HttpResponse(csv_text, content_type="text/csv; charset=utf-8")
            response["Content-Disposition"] = f'attachment; filename="pcos-insight-records-{start:%Y%m%d}-{end:%Y%m%d}.csv"'
            response["Cache-Control"] = "private, no-store"
            response["X-Content-Type-Options"] = "nosniff"
            return response
        pdf = build_health_report(start, end, cycle_entries, symptom_entries, lifestyle_entries)
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="pcos-insight-report-{start:%Y%m%d}-{end:%Y%m%d}.pdf"'
        response["Cache-Control"] = "private, no-store"
        response["X-Content-Type-Options"] = "nosniff"
        return response
    return render(request, "health/report.html", {"form": form})


@login_required
@never_cache
def ultrasound_intake(request):
    profile, _ = HealthProfile.objects.get_or_create(user=request.user)
    form = UltrasoundImageForm(request.POST or None, request.FILES or None)
    if request.method == "POST":
        if not profile.consent_to_health_data:
            messages.error(request, "Turn on health-data consent before storing an ultrasound image.")
            return redirect("ultrasound_intake")
        if form.is_valid():
            image_record = form.save(commit=False)
            image_record.user = request.user
            image_record.save()
            messages.success(request, "Your image was stored as a private record. No analysis was performed.")
            return redirect("ultrasound_intake")
    return render(request, "health/ultrasound.html", {
        "form": form,
        "profile": profile,
        "images": UltrasoundImage.objects.filter(user=request.user),
    })


@login_required
@never_cache
def view_ultrasound_image(request, image_id):
    image_record = get_object_or_404(UltrasoundImage, pk=image_id, user=request.user)
    response = FileResponse(image_record.image.open("rb"), content_type="image/jpeg")
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    response["Content-Disposition"] = 'inline; filename="ultrasound.jpg"'
    response["Referrer-Policy"] = "no-referrer"
    return response


@login_required
@never_cache
def preprocess_ultrasound_image(request, image_id):
    image_record = get_object_or_404(UltrasoundImage, pk=image_id, user=request.user)
    with Image.open(image_record.image.open("rb")) as source:
        preview = ImageOps.autocontrast(source.convert("L"))
        preview.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
        output = BytesIO()
        preview.save(output, format="PNG", optimize=True)
    response = FileResponse(BytesIO(output.getvalue()), content_type="image/png")
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    response["Content-Disposition"] = 'inline; filename="ultrasound-preview.png"'
    response["Referrer-Policy"] = "no-referrer"
    return response


@login_required
@never_cache
@require_POST
def delete_ultrasound_image(request, image_id):
    image_record = get_object_or_404(UltrasoundImage, pk=image_id, user=request.user)
    image_record.delete()
    messages.success(request, "Your ultrasound image and its stored file were deleted.")
    return redirect("ultrasound_intake")


@login_required
@never_cache
def edit_entry(request, entry_type, entry_id):
    if entry_type not in ENTRY_TYPES:
        raise Http404
    model, form_class, label = ENTRY_TYPES[entry_type]
    entry = get_object_or_404(model, pk=entry_id, user=request.user)
    profile, _ = HealthProfile.objects.get_or_create(user=request.user)
    if not profile.consent_to_health_data:
        messages.error(request, "Health-data consent is off, so existing entries cannot be changed. You can still delete them.")
        return redirect("dashboard")

    form_kwargs = {"instance": entry}
    if entry_type == "cycle":
        form_kwargs["user"] = request.user
    form = form_class(request.POST or None, **form_kwargs)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"Your {label} was updated.")
        return redirect("dashboard")
    return render(request, "health/edit_entry.html", {"form": form, "label": label})


@login_required
@never_cache
def delete_entry(request, entry_type, entry_id):
    if entry_type not in ENTRY_TYPES:
        raise Http404
    model, _form_class, label = ENTRY_TYPES[entry_type]
    entry = get_object_or_404(model, pk=entry_id, user=request.user)
    if request.method == "POST":
        entry.delete()
        messages.success(request, f"Your {label} was deleted.")
        return redirect("dashboard")
    return render(request, "health/delete_entry.html", {"entry": entry, "label": label})


@login_required
@never_cache
def delete_account(request):
    form = AccountDeleteForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        if not request.user.check_password(form.cleaned_data["password"]):
            form.add_error("password", "The password was not recognised.")
        else:
            user = request.user
            logout(request)
            user.delete()
            messages.success(request, "Your account and associated health records were deleted.")
            return redirect("home")
    return render(request, "health/delete_account.html", {"form": form})
