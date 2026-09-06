from __future__ import annotations

import pytest
from django.utils import timezone

from apps.clients.models import Client
from apps.expenses.models import Expense, ExpenseCategory
from apps.expenses.services import confirm_allocations


@pytest.mark.django_db
def test_shared_expense_allocation_must_sum_exactly(admin):
    category = ExpenseCategory.objects.create(name="VPS")
    clients = [Client.objects.create(name=f"Cliente {index}", billing_prefix=f"C{index}") for index in range(3)]
    expense = Expense.objects.create(
        category=category,
        scope=Expense.Scope.SHARED,
        concept="Servidor compartido",
        amount=150_000,
        incurred_at=timezone.now(),
        recorded_by=admin,
    )

    allocations = confirm_allocations(
        expense=expense,
        method="equal",
        lines=[{"client_id": client.pk, "amount": 50_000} for client in clients],
        snapshot={"active_clients": [str(client.pk) for client in clients]},
        user=admin,
    )
    assert sum(line.amount for line in allocations) == 150_000
    assert all(line.calculation_snapshot["active_clients"] for line in allocations)


@pytest.mark.django_db
def test_shared_expense_rejects_unbalanced_allocation(admin, client):
    category = ExpenseCategory.objects.create(name="Infraestructura compartida")
    expense = Expense.objects.create(
        category=category,
        scope=Expense.Scope.SHARED,
        concept="Servidor",
        amount=150_000,
        incurred_at=timezone.now(),
        recorded_by=admin,
    )
    with pytest.raises(ValueError, match="sumar exactamente"):
        confirm_allocations(
            expense=expense,
            method="amount",
            lines=[{"client_id": client.pk, "amount": 149_999}],
            snapshot={},
            user=admin,
        )
