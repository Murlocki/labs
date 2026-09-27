from django.conf import settings
from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone


class Unit(models.Model):
    name = models.CharField("обозначение", max_length=32, unique=True)
    note = models.CharField("категория", max_length=64, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "единица измерения"
        verbose_name_plural = "единицы измерения"

    def __str__(self):
        return self.name


class Analysis(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="analyses",
        verbose_name="владелец",
    )
    name = models.CharField("название", max_length=128)
    unit = models.ForeignKey(
        Unit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="analyses",
        verbose_name="единица измерения",
    )
    description = models.TextField("описание", max_length=2000, blank=True)
    created_at = models.DateTimeField("создан", auto_now_add=True)
    updated_at = models.DateTimeField("изменён", auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "анализ"
        verbose_name_plural = "анализы"
        constraints = [
            models.UniqueConstraint(Lower("name"), "user", name="uq_analysis_user_name_ci"),
        ]
        indexes = [models.Index(fields=["user", "name"], name="idx_analysis_user_name")]

    def __str__(self):
        return self.name


class AnalysisValue(models.Model):
    analysis = models.ForeignKey(
        Analysis,
        on_delete=models.CASCADE,
        related_name="entries",
        verbose_name="анализ",
    )
    value = models.CharField("значение", max_length=64)
    measured_at = models.DateTimeField("дата и время сдачи", default=timezone.now)
    note = models.CharField("комментарий", max_length=255, blank=True)
    created_at = models.DateTimeField("внесено", auto_now_add=True)
    updated_at = models.DateTimeField("изменено", auto_now=True)

    class Meta:
        ordering = ["-measured_at"]
        verbose_name = "значение анализа"
        verbose_name_plural = "значения анализов"
        indexes = [models.Index(fields=["analysis", "-measured_at"], name="idx_value_analysis_measured")]

    def __str__(self):
        local = timezone.localtime(self.measured_at)
        return f"{self.value} ({local:%d.%m.%Y %H:%M})"
