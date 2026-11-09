from io import BytesIO
import warnings
from uuid import uuid4

from django import forms
from django.core.files.base import ContentFile
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone
from PIL import Image, ImageOps, UnidentifiedImageError

from .models import CycleEntry, HealthProfile, LifestyleEntry, SymptomEntry, UltrasoundImage


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    health_data_consent = forms.BooleanField(
        required=True,
        label="I agree to store the health information I choose to record in my private account.",
        error_messages={"required": "Please review and accept health-data storage consent to create an account."},
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email address already exists.")
        return email


class DateInput(forms.DateInput):
    input_type = "date"


class ReportRangeForm(forms.Form):
    start_date = forms.DateField(widget=DateInput(), label="From")
    end_date = forms.DateField(widget=DateInput(), label="Through")

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("start_date")
        end = cleaned_data.get("end_date")
        if start and end and end < start:
            self.add_error("end_date", "The end date must be on or after the start date.")
        return cleaned_data


class UltrasoundImageForm(forms.ModelForm):
    storage_consent = forms.BooleanField(
        required=True,
        label="I have permission to store this image and understand this prototype does not analyze or diagnose it.",
    )

    class Meta:
        model = UltrasoundImage
        fields = ("study_date", "image")
        widgets = {
            "study_date": DateInput(),
            "image": forms.ClearableFileInput(attrs={"accept": "image/jpeg,image/png,image/webp"}),
        }

    def clean_image(self):
        uploaded = self.cleaned_data["image"]
        if uploaded.size > 8 * 1024 * 1024:
            raise forms.ValidationError("Choose an image smaller than 8 MB.")
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                uploaded.seek(0)
                with Image.open(uploaded) as source:
                    if source.format not in {"JPEG", "PNG", "WEBP"}:
                        raise forms.ValidationError("Upload a JPEG, PNG, or WebP image.")
                    if getattr(source, "n_frames", 1) != 1:
                        raise forms.ValidationError("Animated images are not supported.")
                    if source.width * source.height > 20_000_000:
                        raise forms.ValidationError("Choose an image with no more than 20 megapixels.")
                    source.verify()
                uploaded.seek(0)
                with Image.open(uploaded) as source:
                    image = ImageOps.exif_transpose(source).convert("RGB")
                    image.thumbnail((2048, 2048), Image.Resampling.LANCZOS)
                    normalized = BytesIO()
                    image.save(normalized, format="JPEG", quality=90, optimize=True, exif=b"")
        except (UnidentifiedImageError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning):
            raise forms.ValidationError("The selected file could not be safely read as an image.")
        return ContentFile(normalized.getvalue(), name=f"{uuid4().hex}.jpg")


class HealthProfileForm(forms.ModelForm):
    class Meta:
        model = HealthProfile
        fields = ("date_of_birth",)
        labels = {"date_of_birth": "Date of birth (optional)"}
        widgets = {"date_of_birth": DateInput()}

    def clean_date_of_birth(self):
        value = self.cleaned_data.get("date_of_birth")
        if value and value > timezone.localdate():
            raise forms.ValidationError("Date of birth cannot be in the future.")
        return value


class CycleEntryForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    class Meta:
        model = CycleEntry
        fields = ("period_start", "period_end", "flow", "notes")
        widgets = {"period_start": DateInput(), "period_end": DateInput()}

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("period_start")
        end = cleaned_data.get("period_end")
        if start and end and end < start:
            self.add_error("period_end", "The period end date must be on or after the start date.")
        duplicate = CycleEntry.objects.filter(user=self.user, period_start=start) if start and self.user else None
        if duplicate is not None and self.instance.pk:
            duplicate = duplicate.exclude(pk=self.instance.pk)
        if duplicate is not None and duplicate.exists():
            self.add_error("period_start", "You already have a cycle entry for this start date.")
        return cleaned_data


class SymptomEntryForm(forms.ModelForm):
    class Meta:
        model = SymptomEntry
        fields = ("recorded_on", "symptom", "severity", "notes")
        widgets = {"recorded_on": DateInput()}


class LifestyleEntryForm(forms.ModelForm):
    class Meta:
        model = LifestyleEntry
        fields = ("recorded_on", "sleep_hours", "activity_minutes", "mood", "notes")
        widgets = {"recorded_on": DateInput()}


class AccountDeleteForm(forms.Form):
    confirmation = forms.CharField(label='Type "DELETE" to confirm')
    password = forms.CharField(widget=forms.PasswordInput, label="Your current password")

    def clean_confirmation(self):
        value = self.cleaned_data["confirmation"].strip()
        if value != "DELETE":
            raise forms.ValidationError('Enter DELETE exactly to confirm account deletion.')
        return value
