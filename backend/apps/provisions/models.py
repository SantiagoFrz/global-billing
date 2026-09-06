from __future__ import annotations

from datetime import date

from django.conf import settings
from django.db import models
from django.db.models import Sum

from apps.common.models import FinancialRecord, TimeStampedUUIDModel, money_field


class ProvisionPlan(TimeStampedUUIDModel):
    class Owner(models.TextChoices):
        GLOBAL = "global", "Global Automate"
        CLIENT = "client", "Cliente"

    class Status(models.TextChoices):
        ACTIVE = "active", "Activa"
        DUE = "due", "Vencida"
        COMPLETED = "completed", "Completada"
        CANCELLED = "cancelled", "Cancelada"

    name = models.CharField(max_length=180)
    owner_type = models.CharField(max_length=10, choices=Owner.choices)
    client = models.ForeignKey(
        "clients.Client", null=True, blank=True, on_delete=models.PROTECT, related_name="provision_plans"
    )
    project = models.ForeignKey(
        "projects.Project", null=True, blank=True, on_delete=models.PROTECT, related_name="provision_plans"
    )
    category = models.ForeignKey(
        "expenses.ExpenseCategory", on_delete=models.PROTECT, related_name="provision_plans"
    )
    target_amount = money_field()
    due_date = models.DateField(db_index=True)
    contribution_start_date = models.DateField()
    frequency = models.CharField(max_length=20, default="monthly")
    expected_increase_basis_points = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE, db_index=True)
    carry_surplus = models.BooleanField(default=True)

    @property
    def reserved_balance(self) -> int:
        contributed = self.contributions.filter(is_void=False).aggregate(total=Sum("amount"))["total"] or 0
        consumed = self.consumptions.filter(is_void=False).aggregate(total=Sum("amount"))["total"] or 0
        return contributed - consumed

    @property
    def remaining_amount(self) -> int:
        return max(0, self.target_amount - self.reserved_balance)

    def periods_remaining(self, on_date: date | None = None) -> int:
        on_date = on_date or date.today()
        start = max(on_date, self.contribution_start_date)
        if start > self.due_date:
            return 0
        return max(1, (self.due_date.year - start.year) * 12 + self.due_date.month - start.month + 1)

    def suggested_contribution(self, on_date: date | None = None) -> int:
        periods = self.periods_remaining(on_date)
        if not periods:
            return self.remaining_amount
        return (self.remaining_amount + periods - 1) // periods


class ProvisionContribution(FinancialRecord):
    plan = models.ForeignKey(ProvisionPlan, on_delete=models.PROTECT, related_name="contributions")
    amount = money_field()
    contributed_at = models.DateTimeField(db_index=True)
    suggested_amount_snapshot = money_field()
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="provision_contributions_recorded"
    )
    note = models.TextField(blank=True)


class ProvisionConsumption(FinancialRecord):
    plan = models.ForeignKey(ProvisionPlan, on_delete=models.PROTECT, related_name="consumptions")
    expense = models.ForeignKey(
        "expenses.Expense", on_delete=models.PROTECT, related_name="provision_consumptions"
    )
    amount = money_field()
    consumed_at = models.DateTimeField(db_index=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="provision_consumptions_recorded"
    )
    result_snapshot = models.JSONField(default=dict)
