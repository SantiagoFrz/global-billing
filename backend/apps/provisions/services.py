from django.db import transaction
from django.utils import timezone

from apps.audit.services import audit_event

from .models import ProvisionConsumption, ProvisionContribution, ProvisionPlan


@transaction.atomic
def contribute(*, plan: ProvisionPlan, amount: int, user, note: str = "") -> ProvisionContribution:
    plan = ProvisionPlan.objects.select_for_update().get(pk=plan.pk)
    if amount <= 0:
        raise ValueError("El aporte debe ser mayor que cero.")
    contribution = ProvisionContribution.objects.create(
        plan=plan,
        amount=amount,
        contributed_at=timezone.now(),
        suggested_amount_snapshot=plan.suggested_contribution(),
        recorded_by=user,
        note=note,
    )
    audit_event(
        user=user,
        action="provision.contribution.created",
        instance=contribution,
        after={"amount": amount, "remaining": plan.remaining_amount},
    )
    return contribution


@transaction.atomic
def consume(*, plan: ProvisionPlan, expense, amount: int, user) -> ProvisionConsumption:
    plan = ProvisionPlan.objects.select_for_update().get(pk=plan.pk)
    if amount <= 0 or amount > plan.reserved_balance:
        raise ValueError("El consumo supera el saldo reservado disponible.")
    consumption = ProvisionConsumption.objects.create(
        plan=plan,
        expense=expense,
        amount=amount,
        consumed_at=timezone.now(),
        recorded_by=user,
        result_snapshot={
            "reserved_before": plan.reserved_balance,
            "expense_amount": expense.amount,
            "deficit": max(0, expense.amount - amount),
            "surplus": max(0, amount - expense.amount),
        },
    )
    audit_event(
        user=user, action="provision.consumed", instance=consumption, after=consumption.result_snapshot
    )
    return consumption
