from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from .models import BillingIssuer, Installment
from .services import generate_charge_document


@shared_task
def generate_due_charge_documents() -> int:
    today = timezone.localdate()
    issuer = BillingIssuer.objects.filter(is_default=True, is_active=True).first()
    if not issuer:
        return 0
    generated = 0
    for installment in Installment.objects.filter(
        is_void=False, due_date__gte=today, due_date__lte=today + timedelta(days=14)
    ).select_related("charge__contract__billing_rule"):
        if (
            installment.due_date
            - timedelta(days=installment.charge.contract.billing_rule.generate_days_before)
            <= today
        ):
            before = installment.documents.filter(is_outdated=False, is_void=False).count()
            generate_charge_document(installment=installment, issuer=issuer)
            generated += int(before == 0)
    return generated


@shared_task
def refresh_installment_statuses() -> int:
    # Status is derived at read time. This task exists to trigger cache/notification refreshes.
    return Installment.objects.filter(is_void=False).count()
