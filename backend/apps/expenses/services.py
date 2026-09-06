from django.db import transaction

from apps.audit.services import audit_event
from apps.treasury.models import BankTransaction

from .models import Expense, ExpenseAllocation


@transaction.atomic
def record_expense_payment(*, expense: Expense, user) -> Expense:
    expense = Expense.objects.select_for_update().get(pk=expense.pk)
    if expense.bank_transaction_id:
        return expense
    if not expense.paid_at or not expense.bank_account_id:
        raise ValueError("Para registrar la salida debes indicar cuenta bancaria y fecha de pago.")
    transaction_record = BankTransaction.objects.create(
        account=expense.bank_account,
        kind=BankTransaction.Kind.EXPENSE,
        amount=-expense.amount,
        occurred_at=expense.paid_at,
        description=expense.concept,
        recorded_by=user,
        source_type="expense",
        source_id=str(expense.pk),
    )
    expense.bank_transaction = transaction_record
    expense.save(update_fields=["bank_transaction", "updated_at"])
    audit_event(
        user=user,
        action="expense.paid",
        instance=expense,
        after={"amount": expense.amount, "bank_transaction": str(transaction_record.pk)},
    )
    return expense


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
