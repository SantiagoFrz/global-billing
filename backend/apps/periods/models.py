from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedUUIDModel


class FinancialPeriod(TimeStampedUUIDModel):
    class Status(models.TextChoices):
        OPEN = "open", "Abierto"
        CLOSED = "closed", "Cerrado"
        REOPENED = "reopened", "Reabierto"

    year = models.PositiveSmallIntegerField()
    month = models.PositiveSmallIntegerField()
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.OPEN)

    class Meta:
        ordering = ("-year", "-month")
        constraints = [models.UniqueConstraint(fields=["year", "month"], name="unique_financial_period")]


class MonthlyClose(TimeStampedUUIDModel):
    period = models.ForeignKey(FinancialPeriod, on_delete=models.PROTECT, related_name="close_versions")
    version = models.PositiveIntegerField()
    snapshot = models.JSONField(default=dict)
    checklist = models.JSONField(default=dict)
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="monthly_closes"
    )
    confirmed_at = models.DateTimeField()
    superseded = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["period", "version"], name="unique_monthly_close_version")
        ]


class PeriodReopening(TimeStampedUUIDModel):
    period = models.ForeignKey(FinancialPeriod, on_delete=models.PROTECT, related_name="reopenings")
    reason = models.TextField()
    reopened_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="period_reopenings"
    )
    reopened_at = models.DateTimeField()
    previous_close = models.ForeignKey(
        MonthlyClose, on_delete=models.PROTECT, related_name="reopening_events"
    )
