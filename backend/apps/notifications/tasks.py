from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from apps.accounts.models import User
from apps.billing.models import Installment
from apps.contracts.models import Contract
from apps.provisions.models import ProvisionPlan

from .models import Notification


@shared_task
def generate_financial_notifications() -> int:
    today = timezone.localdate()
    users = User.objects.filter(is_active=True, is_admin=True)
    events = []
    for installment in Installment.objects.filter(
        is_void=False, due_date__lte=today + timedelta(days=1)
    ).select_related("charge__contract__client"):
        if installment.balance:
            days = (today - installment.due_date).days
            title = (
                f"{installment.charge.contract.client.name} paga mañana"
                if days == -1
                else f"Pago vencido de {installment.charge.contract.client.name}"
            )
            events.append(
                (
                    f"installment:{installment.pk}:{today}",
                    title,
                    f"Saldo pendiente: ${installment.balance:,.0f}",
                    "/billing",
                )
            )
    for plan in ProvisionPlan.objects.filter(
        status=ProvisionPlan.Status.ACTIVE, due_date__lte=today + timedelta(days=30)
    ):
        events.append(
            (
                f"provision:{plan.pk}:30d",
                f"{plan.name} vence pronto",
                f"Faltan ${plan.remaining_amount:,.0f} para cubrir la obligación.",
                f"/provisions/{plan.pk}",
            )
        )
    for contract in Contract.objects.filter(
        status=Contract.Status.ACTIVE, end_date__lte=today + timedelta(days=30), end_date__gte=today
    ):
        events.append(
            (
                f"contract:{contract.pk}:30d",
                f"Contrato por vencer: {contract.name}",
                f"Finaliza el {contract.end_date:%d/%m/%Y}.",
                f"/contracts/{contract.pk}",
            )
        )
    created = 0
    for user in users:
        for key, title, body, url in events:
            _, was_created = Notification.objects.get_or_create(
                recipient=user,
                event_key=key,
                defaults={
                    "title": title,
                    "body": body,
                    "severity": Notification.Severity.WARNING,
                    "action_url": url,
                },
            )
            created += int(was_created)
    return created
