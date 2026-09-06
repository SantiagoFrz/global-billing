from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.common.models import FinancialRecord, money_field


class Payment(FinancialRecord):
    client = models.ForeignKey("clients.Client", on_delete=models.PROTECT, related_name="payments")
    bank_account = models.ForeignKey(
        "treasury.BankAccount", on_delete=models.PROTECT, related_name="payments_received"
    )
    amount = money_field()
    received_at = models.DateTimeField(db_index=True)
    reference = models.CharField(max_length=120, blank=True)
    notes = models.TextField(blank=True)
    proof = models.FileField(upload_to="payment_proofs/%Y/%m/", blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="payments_recorded"
    )
    bank_transaction = models.OneToOneField(
        "treasury.BankTransaction",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="payment_record",
    )


class PaymentAllocation(FinancialRecord):
    payment = models.ForeignKey(Payment, on_delete=models.PROTECT, related_name="allocations")
    installment = models.ForeignKey(
        "billing.Installment", on_delete=models.PROTECT, related_name="payment_allocations"
    )
    amount = money_field()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["payment", "installment"],
                condition=Q(is_void=False),
                name="unique_active_payment_installment_allocation",
            )
        ]
