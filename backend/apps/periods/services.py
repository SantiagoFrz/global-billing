from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from apps.audit.services import audit_event

from .models import FinancialPeriod, MonthlyClose, PeriodReopening


@transaction.atomic
def close_period(*, period: FinancialPeriod, snapshot: dict, checklist: dict, user) -> MonthlyClose:
    period = FinancialPeriod.objects.select_for_update().get(pk=period.pk)
    if not all(checklist.get(str(step), False) for step in range(1, 11)):
        raise ValueError("Debes completar los diez pasos antes de confirmar el cierre.")
    period.close_versions.filter(superseded=False).update(superseded=True)
    version = (period.close_versions.aggregate(max=Max("version"))["max"] or 0) + 1
    close = MonthlyClose.objects.create(
        period=period,
        version=version,
        snapshot=snapshot,
        checklist=checklist,
        confirmed_by=user,
        confirmed_at=timezone.now(),
    )
    period.status = FinancialPeriod.Status.CLOSED
    period.save(update_fields=["status", "updated_at"])
    audit_event(
        user=user, action="period.closed", instance=close, after={"version": version, "snapshot": snapshot}
    )
    return close


@transaction.atomic
def reopen_period(*, period: FinancialPeriod, reason: str, user) -> PeriodReopening:
    period = FinancialPeriod.objects.select_for_update().get(pk=period.pk)
    close = period.close_versions.filter(superseded=False).order_by("-version").first()
    if not close or not reason.strip():
        raise ValueError("Se requiere un cierre vigente y un motivo para reabrir.")
    event = PeriodReopening.objects.create(
        period=period, reason=reason, reopened_by=user, reopened_at=timezone.now(), previous_close=close
    )
    period.status = FinancialPeriod.Status.REOPENED
    period.save(update_fields=["status", "updated_at"])
    audit_event(
        user=user,
        action="period.reopened",
        instance=event,
        before={"close_version": close.version},
        after={"reason": reason},
    )
    return event
