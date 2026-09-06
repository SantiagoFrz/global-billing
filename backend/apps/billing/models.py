from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from apps.common.models import FinancialRecord, TimeStampedUUIDModel, money_field


class ScheduledCharge(FinancialRecord):
    """Obligación de un periodo. Puede dividirse en varias cuotas sin duplicar ingreso."""

    contract = models.ForeignKey(
        "contracts.Contract", on_delete=models.PROTECT, related_name="scheduled_charges"
    )
    contract_version = models.ForeignKey(
        "contracts.ContractVersion", on_delete=models.PROTECT, related_name="scheduled_charges"
    )
    service_period_start = models.DateField(db_index=True)
    service_period_end = models.DateField()
    amount = money_field()
    waived_amount = money_field(default=0)
    cancelled_amount = money_field(default=0)
    legacy_source = models.BooleanField(default=False)

    class Meta:
        ordering = ("service_period_start",)
        constraints = [
            models.UniqueConstraint(
                fields=["contract", "service_period_start"],
                condition=Q(is_void=False),
                name="unique_active_charge_period",
            ),
            models.CheckConstraint(condition=Q(waived_amount__gte=0), name="charge_waived_non_negative"),
        ]

    @property
    def net_collectible(self) -> int:
        return max(0, self.amount - self.waived_amount - self.cancelled_amount)


class Installment(FinancialRecord):
    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Programado"
        DOCUMENT_PENDING = "document_pending", "Cuenta pendiente"
        DOCUMENT_DRAFT = "document_draft", "Cuenta generada"
        SENT = "sent", "Enviado"
        DUE_SOON = "due_soon", "Por vencer"
        OVERDUE = "overdue", "Vencido"
        PARTIAL = "partial", "Pagado parcialmente"
        PAID = "paid", "Pagado"
        WAIVED = "waived", "Condonado"
        CANCELLED = "cancelled", "Cancelado"

    charge = models.ForeignKey(ScheduledCharge, on_delete=models.PROTECT, related_name="installments")
    sequence = models.PositiveSmallIntegerField()
    due_date = models.DateField(db_index=True)
    amount = money_field()
    waived_amount = money_field(default=0)
    status_override = models.CharField(max_length=24, choices=Status.choices, blank=True)
    status_override_reason = models.TextField(blank=True)

    class Meta:
        ordering = ("due_date", "sequence")
        constraints = [
            models.UniqueConstraint(fields=["charge", "sequence"], name="unique_installment_sequence")
        ]

    @property
    def paid_amount(self) -> int:
        return sum(a.amount for a in self.payment_allocations.filter(payment__is_void=False))

    @property
    def balance(self) -> int:
        return max(0, self.amount - self.waived_amount - self.paid_amount)

    def calculated_status(self, on_date=None) -> str:
        from datetime import date, timedelta

        on_date = on_date or date.today()
        if self.status_override:
            return self.status_override
        if self.waived_amount >= self.amount:
            return self.Status.WAIVED
        if self.balance == 0:
            return self.Status.PAID
        if self.paid_amount:
            return self.Status.PARTIAL
        if self.due_date < on_date:
            return self.Status.OVERDUE
        if self.due_date <= on_date + timedelta(days=3):
            return self.Status.DUE_SOON
        if self.documents.filter(is_outdated=False).exists():
            return self.Status.DOCUMENT_DRAFT
        return self.Status.SCHEDULED


class Waiver(FinancialRecord):
    installment = models.ForeignKey(Installment, on_delete=models.PROTECT, related_name="waivers")
    amount = money_field()
    reason = models.TextField()
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="waivers_granted"
    )
    granted_at = models.DateTimeField()

    def clean(self) -> None:
        if self.amount > self.installment.balance:
            raise ValidationError({"amount": "La condonación supera el saldo pendiente."})


class BillingIssuer(TimeStampedUUIDModel):
    display_name = models.CharField(max_length=180)
    identification_type = models.CharField(max_length=30, blank=True)
    identification = models.CharField(max_length=80, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    address = models.TextField(blank=True)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)


class BillingSequence(TimeStampedUUIDModel):
    client = models.OneToOneField("clients.Client", on_delete=models.PROTECT, related_name="billing_sequence")
    last_number = models.PositiveIntegerField(default=0)


class ChargeDocument(FinancialRecord):
    class Status(models.TextChoices):
        REVIEW = "review", "Pendiente de revisión"
        APPROVED = "approved", "Aprobada"
        SENT = "sent", "Enviada"
        CANCELLED = "cancelled", "Cancelada"

    installment = models.ForeignKey(Installment, on_delete=models.PROTECT, related_name="documents")
    issuer = models.ForeignKey(BillingIssuer, on_delete=models.PROTECT, related_name="charge_documents")
    consecutive = models.CharField(max_length=50, unique=True)
    revision = models.PositiveSmallIntegerField(default=1)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.REVIEW, db_index=True)
    concept = models.TextField()
    amount = money_field()
    generated_at = models.DateTimeField(auto_now_add=True)
    is_outdated = models.BooleanField(default=False, db_index=True)
    pdf_file = models.FileField(upload_to="charge_documents/%Y/%m/", blank=True)
    source_fingerprint = models.CharField(max_length=64)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["installment", "revision"], name="unique_charge_document_revision"
            ),
            models.UniqueConstraint(
                fields=["installment"],
                condition=Q(is_outdated=False, is_void=False),
                name="one_current_charge_document",
            ),
        ]


class GeneratedMessage(TimeStampedUUIDModel):
    charge_document = models.ForeignKey(ChargeDocument, on_delete=models.CASCADE, related_name="messages")
    body = models.TextField()
    variant_key = models.CharField(max_length=40)
    edited_by_user = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT, related_name="generated_messages"
    )
