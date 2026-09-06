from django.conf import settings
from django.db import models

from apps.common.models import FinancialRecord, TimeStampedUUIDModel, money_field


class ExpenseCategory(TimeStampedUUIDModel):
    name = models.CharField(max_length=120, unique=True)
    active = models.BooleanField(default=True)


class Expense(FinancialRecord):
    class Scope(models.TextChoices):
        GLOBAL = "global", "Global Automate"
        CLIENT = "client", "Cliente"
        SHARED = "shared", "Compartido"

    category = models.ForeignKey(ExpenseCategory, on_delete=models.PROTECT, related_name="expenses")
    scope = models.CharField(max_length=12, choices=Scope.choices, db_index=True)
    client = models.ForeignKey(
        "clients.Client", null=True, blank=True, on_delete=models.PROTECT, related_name="expenses"
    )
    project = models.ForeignKey(
        "projects.Project", null=True, blank=True, on_delete=models.PROTECT, related_name="expenses"
    )
    contract = models.ForeignKey(
        "contracts.Contract", null=True, blank=True, on_delete=models.PROTECT, related_name="expenses"
    )
    service = models.ForeignKey(
        "projects.Service", null=True, blank=True, on_delete=models.PROTECT, related_name="expenses"
    )
    bank_account = models.ForeignKey(
        "treasury.BankAccount", null=True, blank=True, on_delete=models.PROTECT, related_name="expenses"
    )
    concept = models.CharField(max_length=220)
    amount = money_field()
    incurred_at = models.DateTimeField(db_index=True)
    due_date = models.DateField(null=True, blank=True, db_index=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="expenses_recorded"
    )
    allocation_confirmed = models.BooleanField(default=False)
    receipt = models.FileField(upload_to="expense_receipts/%Y/%m/", blank=True)
    bank_transaction = models.OneToOneField(
        "treasury.BankTransaction",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="expense_record",
    )


class ExpenseAllocation(FinancialRecord):
    class Method(models.TextChoices):
        EQUAL = "equal", "Partes iguales"
        PERCENTAGE = "percentage", "Porcentaje manual"
        AMOUNT = "amount", "Monto manual"
        RECEIVED_REVENUE = "received_revenue", "Ingreso real recibido"

    expense = models.ForeignKey(Expense, on_delete=models.PROTECT, related_name="allocations")
    client = models.ForeignKey("clients.Client", on_delete=models.PROTECT, related_name="expense_allocations")
    amount = money_field()
    percentage_basis_points = models.PositiveIntegerField(null=True, blank=True)
    method = models.CharField(max_length=24, choices=Method.choices)
    calculation_snapshot = models.JSONField(default=dict)
    confirmed_at = models.DateTimeField()
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="expense_allocations_confirmed"
    )
