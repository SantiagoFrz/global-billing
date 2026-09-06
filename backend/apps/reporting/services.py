from __future__ import annotations

from datetime import date

from django.db.models import Sum
from django.utils import timezone

from apps.billing.models import Installment
from apps.distributions.models import DistributionLine, DistributionRun
from apps.expenses.models import Expense
from apps.payments.models import Payment
from apps.provisions.models import ProvisionPlan
from apps.treasury.models import BankAccount, BankTransaction, FundMovement


def financial_breakdown(*, on_date: date | None = None) -> dict:
    on_date = on_date or timezone.localdate()
    bank_opening = (
        BankAccount.objects.filter(active=True).aggregate(total=Sum("opening_balance"))["total"] or 0
    )
    bank_movement = (
        BankTransaction.objects.filter(is_void=False, account__active=True).aggregate(total=Sum("amount"))[
            "total"
        ]
        or 0
    )
    bank_balance = bank_opening + bank_movement
    provision_reserved = sum(
        plan.reserved_balance for plan in ProvisionPlan.objects.filter(status=ProvisionPlan.Status.ACTIVE)
    )
    fund_reserved = max(
        0, FundMovement.objects.filter(is_void=False).aggregate(total=Sum("amount"))["total"] or 0
    )
    reserved = provision_reserved + fund_reserved
    pending_expenses = (
        Expense.objects.filter(is_void=False, paid_at__isnull=True).aggregate(total=Sum("amount"))["total"]
        or 0
    )
    pending_distributions = (
        DistributionLine.objects.filter(
            is_void=False,
            bank_transaction__isnull=True,
            run__status__in=[DistributionRun.Status.APPROVED, DistributionRun.Status.PARTIAL],
        ).aggregate(total=Sum("amount"))["total"]
        or 0
    )
    committed = pending_expenses + pending_distributions
    available = bank_balance - reserved - committed
    month_installments = Installment.objects.filter(
        is_void=False, due_date__year=on_date.year, due_date__month=on_date.month
    )
    receivable = sum(item.balance for item in month_installments)
    overdue_qs = Installment.objects.filter(is_void=False, due_date__lt=on_date)
    overdue = sum(item.balance for item in overdue_qs)
    income_month = (
        Payment.objects.filter(
            is_void=False, received_at__year=on_date.year, received_at__month=on_date.month
        ).aggregate(total=Sum("amount"))["total"]
        or 0
    )
    expenses_month = (
        Expense.objects.filter(
            is_void=False, paid_at__year=on_date.year, paid_at__month=on_date.month
        ).aggregate(total=Sum("amount"))["total"]
        or 0
    )
    return {
        "asOf": on_date.isoformat(),
        "currency": "COP",
        "bankBalance": bank_balance,
        "reserved": reserved,
        "committed": committed,
        "available": available,
        "distributable": max(0, available),
        "receivableThisMonth": receivable,
        "overdue": overdue,
        "expensesDue": pending_expenses,
        "monthResult": income_month - expenses_month,
        "breakdowns": {
            "available": [
                {
                    "label": "Saldo en cuentas",
                    "amount": bank_balance,
                    "operator": "+",
                    "href": "/treasury/accounts",
                },
                {"label": "Reservas y fondos", "amount": reserved, "operator": "-", "href": "/provisions"},
                {
                    "label": "Compromisos pendientes",
                    "amount": committed,
                    "operator": "-",
                    "href": "/expenses?status=pending",
                },
            ],
            "reserved": [
                {
                    "label": "Provisiones específicas",
                    "amount": provision_reserved,
                    "operator": "+",
                    "href": "/provisions",
                },
                {"label": "Fondos internos", "amount": fund_reserved, "operator": "+", "href": "/funds"},
            ],
            "committed": [
                {
                    "label": "Gastos pendientes",
                    "amount": pending_expenses,
                    "operator": "+",
                    "href": "/expenses?status=pending",
                },
                {
                    "label": "Distribuciones aprobadas",
                    "amount": pending_distributions,
                    "operator": "+",
                    "href": "/distributions",
                },
            ],
        },
    }
