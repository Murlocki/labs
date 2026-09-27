from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.utils import timezone

from .models import Analysis, AnalysisValue


class LoginForm(AuthenticationForm):
    error_messages = {
        "invalid_login": "Неверный логин или пароль.",
        "inactive": "Неверный логин или пароль.",
    }


class SignUpForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        fields = ("username",)


class AnalysisForm(forms.ModelForm):
    class Meta:
        model = Analysis
        fields = ("name", "unit", "description")
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields["unit"].empty_label = "— не указана —"

    def clean_name(self):
        name = self.cleaned_data["name"]
        duplicates = Analysis.objects.filter(user=self.user, name__iexact=name)
        if self.instance.pk:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise forms.ValidationError("Анализ с таким названием уже существует.")
        return name


class AnalysisValueForm(forms.ModelForm):
    DATETIME_FORMAT = "%Y-%m-%dT%H:%M"

    measured_at = forms.DateTimeField(
        label="Дата и время сдачи",
        input_formats=[DATETIME_FORMAT],
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}, format=DATETIME_FORMAT),
    )

    class Meta:
        model = AnalysisValue
        fields = ("analysis", "value", "measured_at", "note")

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["analysis"].queryset = Analysis.objects.filter(user=user).order_by("name")
        self.fields["analysis"].empty_label = "— выберите анализ —"
        if not self.instance.pk and "measured_at" not in self.initial:
            self.initial["measured_at"] = timezone.localtime().replace(second=0, microsecond=0)

    def clean_measured_at(self):
        measured_at = self.cleaned_data["measured_at"]
        if measured_at > timezone.now():
            raise forms.ValidationError("Дата сдачи не может быть в будущем.")
        return measured_at
