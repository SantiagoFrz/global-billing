from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.common.models import TimeStampedUUIDModel, money_field


class Contract(TimeStampedUUIDModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Borrador"
        ACTIVE = "active", "Activo"
        SUSPENDED = "suspended", "Suspendido"
        COMPLETED = "completed", "Completado"
        CANCELLED = "cancelled", "Cancelado"
        EXPIRED = "expired", "Vencido"
        RENEWAL_PENDING = "renewal_pending", "Renovación pendiente"

    client = models.ForeignKey("clients.Client", on_delete=models.PROTECT, related_name="contracts")
    project = models.ForeignKey(
        "projects.Project", null=True, blank=True, on_delete=models.PROTECT, related_name="contracts"
    )
    name = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.DRAFT, db_index=True)
    billing_periodicity = models.CharField(max_length=24, default="monthly")
    renewal_mode = models.CharField(max_length=24, default="manual")
    conditions = models.TextField(blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)

    class Meta:
        indexes = [models.Index(fields=["status", "end_date"]), models.Index(fields=["client", "status"])]

    def __str__(self) -> str:
        return self.name


class ContractVersion(TimeStampedUUIDModel):
    contract = models.ForeignKey(Contract, on_delete=models.PROTECT, related_name="versions")
    version_number = models.PositiveIntegerField()
    effective_from = models.DateField()
    effective_until = models.DateField(null=True, blank=True)
    period_amount = money_field()
    currency = models.CharField(max_length=3, default="COP", editable=False)
    change_reason = models.TextField()
    conditions_snapshot = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.PROTECT,
        related_name="contract_versions_created",
    )

    class Meta:
        ordering = ("contract", "version_number")
        constraints = [
            models.UniqueConstraint(
                fields=["contract", "version_number"], name="unique_contract_version_number"
            ),
        ]

    def clean(self) -> None:
        if self.effective_until and self.effective_until < self.effective_from:
            raise ValidationError(
                {"effective_until": "La vigencia final no puede ser anterior a la inicial."}
            )


class ContractService(TimeStampedUUIDModel):
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name="contract_services")
    service = models.ForeignKey(
        "projects.Service", on_delete=models.PROTECT, related_name="contract_services"
    )
    description = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["contract", "service"], name="unique_service_per_contract")
        ]


class BillingRule(TimeStampedUUIDModel):
    class Frequency(models.TextChoices):
        ONCE = "once", "Único"
        MONTHLY = "monthly", "Mensual"
        BIMONTHLY = "bimonthly", "Cada 2 meses"
        QUARTERLY = "quarterly", "Trimestral"
        CUSTOM = "custom", "Personalizado"

    contract = models.OneToOneField(Contract, on_delete=models.CASCADE, related_name="billing_rule")
    frequency = models.CharField(max_length=16, choices=Frequency.choices, default=Frequency.MONTHLY)
    due_days = models.JSONField(default=list, help_text="Días del mes; p. ej. [11, 26].")
    split_percentages = models.JSONField(default=list, help_text="Porcentajes enteros que suman 100.")
    custom_schedule = models.JSONField(default=list, blank=True)
    generate_days_before = models.PositiveSmallIntegerField(default=2)

    def clean(self) -> None:
        if self.frequency != self.Frequency.CUSTOM:
            if not self.due_days:
                raise ValidationError({"due_days": "Debes indicar al menos un día de pago."})
            if self.split_percentages and sum(self.split_percentages) != 100:
                raise ValidationError({"split_percentages": "Los porcentajes deben sumar exactamente 100%."})
            if self.split_percentages and len(self.split_percentages) != len(self.due_days):
                raise ValidationError({"split_percentages": "Debe existir un porcentaje por cada fecha."})
