from django.db import transaction

from apps.audit.services import audit_event

from .models import DistributionLine, DistributionPolicy, DistributionRun


@transaction.atomic
def calculate_distribution(
    *, period, distributable_base: int, policy: DistributionPolicy, snapshot: dict, user
) -> DistributionRun:
    if distributable_base < 0:
        raise ValueError("La base distribuible no puede ser negativa.")
    participants = list(policy.participants.order_by("created_at"))
    if not participants or sum(p.percentage_basis_points for p in participants) != 10_000:
        raise ValueError("Los porcentajes de la política deben sumar exactamente 100%.")
    run = DistributionRun.objects.create(
        period=period,
        policy=policy,
        distributable_base=distributable_base,
        calculation_snapshot=snapshot,
        created_by=user,
    )
    allocated = 0
    lines = []
    for index, participant in enumerate(participants):
        amount = (
            distributable_base - allocated
            if index == len(participants) - 1
            else distributable_base * participant.percentage_basis_points // 10_000
        )
        allocated += amount
        lines.append(DistributionLine(run=run, participant=participant, amount=amount))
    DistributionLine.objects.bulk_create(lines)
    audit_event(
        user=user,
        action="distribution.calculated",
        instance=run,
        after={"base": distributable_base, "sum": allocated},
    )
    return run
