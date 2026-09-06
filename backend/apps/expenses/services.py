from django.db import transaction

from apps.audit.services import audit_event

from .models import Expense, ExpenseAllocation


@transaction.atomic
def confirm_allocations(
    *, expense: Expense, lines: list[dict], method: str, snapshot: dict, user
) -> list[ExpenseAllocation]:
    expense = Expense.objects.select_for_update().get(pk=expense.pk)
    if expense.allocation_confirmed:
        raise ValueError(
            "Este gasto ya tiene una asignación confirmada. Usa recalcular para crear una nueva versión."
        )
    if sum(int(line["amount"]) for line in lines) != expense.amount:
        raise ValueError("Las asignaciones deben sumar exactamente el valor del gasto.")
    from django.utils import timezone

    allocations = [
        ExpenseAllocation.objects.create(
            expense=expense,
            client_id=line["client_id"],
            amount=int(line["amount"]),
            percentage_basis_points=line.get("percentage_basis_points"),
            method=method,
            calculation_snapshot=snapshot,
            confirmed_at=timezone.now(),
            confirmed_by=user,
        )
        for line in lines
    ]
    expense.allocation_confirmed = True
    expense.save(update_fields=["allocation_confirmed", "updated_at"])
    audit_event(
        user=user,
        action="expense.allocations.confirmed",
        instance=expense,
        after={"method": method, "total": expense.amount},
    )
    return allocations
