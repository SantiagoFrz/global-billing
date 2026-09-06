from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.common.models import FinancialRecord, TimeStampedUUIDModel, money_field


class BankAccount(TimeStampedUUIDModel):
    name = models.CharField(max_length=120)
    bank = models.CharField(max_length=120, blank=True)
    account_type = models.CharField(max_length=40, blank=True)
    last_digits = models.CharField(max_length=4, blank=True)
    opening_balance = money_field(default=0)
    currency = models.CharField(max_length=3, default="COP", editable=False)
    active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name


class BankTransaction(FinancialRecord):
    class Kind(models.TextChoices):
        PAYMENT = "payment", "Pago de cliente"
        EXPENSE = "expense", "Gasto"
        TRANSFER_OUT = "transfer_out", "Transferencia salida"
        TRANSFER_IN = "transfer_in", "Transferencia entrada"
        DISTRIBUTION = "distribution", "Distribución"
        ADJUSTMENT = "adjustment", "Ajuste"

    account = models.ForeignKey(BankAccount, on_delete=models.PROTECT, related_name="transactions")
    kind = models.CharField(max_length=20, choices=Kind.choices, db_index=True)
    amount = models.BigIntegerField(help_text="Entrada positiva, salida negativa.")
    occurred_at = models.DateTimeField(db_index=True)
    description = models.CharField(max_length=220)
    external_reference = models.CharField(max_length=120, blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="bank_transactions_recorded"
    )
    source_type = models.CharField(max_length=80, blank=True)
    source_id = models.CharField(max_length=80, blank=True)


class InternalTransfer(FinancialRecord):
    from_account = models.ForeignKey(BankAccount, on_delete=models.PROTECT, related_name="transfers_out")
    to_account = models.ForeignKey(BankAccount, on_delete=models.PROTECT, related_name="transfers_in")
    amount = money_field()
    occurred_at = models.DateTimeField()
    reason = models.CharField(max_length=220)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="internal_transfers_recorded"
    )
    out_transaction = models.OneToOneField(
        BankTransaction, null=True, blank=True, on_delete=models.PROTECT, related_name="transfer_out_record"
    )
    in_transaction = models.OneToOneField(
        BankTransaction, null=True, blank=True, on_delete=models.PROTECT, related_name="transfer_in_record"
    )

    def clean(self):
        if self.from_account_id == self.to_account_id:
            raise ValidationError("Las cuentas de origen y destino deben ser diferentes.")


class InternalFund(TimeStampedUUIDModel):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)


class FundMovement(FinancialRecord):
    fund = models.ForeignKey(InternalFund, on_delete=models.PROTECT, related_name="movements")
    amount = models.BigIntegerField(help_text="Aporte positivo, retiro negativo.")
    occurred_at = models.DateTimeField(db_index=True)
    reason = models.CharField(max_length=220)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="fund_movements_recorded"
    )
    destination_fund = models.ForeignKey(
        InternalFund, null=True, blank=True, on_delete=models.PROTECT, related_name="incoming_transfers"
    )
