from django.conf import settings
from django.db import models

from apps.common.models import FinancialRecord, TimeStampedUUIDModel, money_field


class DistributionPolicy(TimeStampedUUIDModel):
    name = models.CharField(max_length=160)
    effective_from = models.DateField(db_index=True)
    effective_until = models.DateField(null=True, blank=True, db_index=True)
    reason = models.TextField()
    active = models.BooleanField(default=True)


class DistributionParticipant(TimeStampedUUIDModel):
    class Kind(models.TextChoices):
        GLOBAL = "global", "Global Automate"
        USER = "user", "Socio"
        LEGACY = "legacy", "Parte histórica"

    policy = models.ForeignKey(DistributionPolicy, on_delete=models.PROTECT, related_name="participants")
    kind = models.CharField(max_length=12, choices=Kind.choices)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="distribution_participations",
    )
    display_name = models.CharField(max_length=160)
    percentage_basis_points = models.PositiveIntegerField()


class DistributionRun(FinancialRecord):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendiente"
        APPROVED = "approved", "Aprobada"
        PARTIAL = "partial", "Parcialmente pagada"
        PAID = "paid", "Pagada"
        CANCELLED = "cancelled", "Cancelada"

    period = models.ForeignKey(
        "periods.FinancialPeriod", on_delete=models.PROTECT, related_name="distribution_runs"
    )
    policy = models.ForeignKey(DistributionPolicy, on_delete=models.PROTECT, related_name="runs")
    distributable_base = money_field()
    calculation_snapshot = models.JSONField(default=dict)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="distribution_runs_created"
    )


class DistributionLine(FinancialRecord):
    run = models.ForeignKey(DistributionRun, on_delete=models.PROTECT, related_name="lines")
    participant = models.ForeignKey(DistributionParticipant, on_delete=models.PROTECT, related_name="lines")
    amount = money_field()
    paid_at = models.DateTimeField(null=True, blank=True)
    bank_transaction = models.OneToOneField(
        "treasury.BankTransaction",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="distribution_line",
    )


class LegacyDistributionParty(TimeStampedUUIDModel):
    label = models.CharField(max_length=160, unique=True)
    mapped_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="legacy_distribution_aliases",
    )
    mapping_confirmed = models.BooleanField(default=False)
