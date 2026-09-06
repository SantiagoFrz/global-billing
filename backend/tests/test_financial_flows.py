from datetime import date

import pytest
from django.utils import timezone

from apps.billing.models import Installment, ScheduledCharge
from apps.billing.services import generate_contract_schedule, grant_waiver
from apps.contracts.models import BillingRule, Contract, ContractVersion
from apps.distributions.models import DistributionParticipant, DistributionPolicy
from apps.distributions.services import calculate_distribution
from apps.expenses.models import ExpenseCategory
from apps.payments.models import Payment
from apps.payments.services import allocate_payment, record_payment
from apps.periods.models import FinancialPeriod
from apps.provisions.models import ProvisionPlan
from apps.provisions.services import contribute


@pytest.mark.django_db
def test_monthly_obligation_split_11_26_is_not_doubled(admin, client):
    contract = Contract.objects.create(
        client=client,
        name="Mensualidad",
        start_date=date(2026, 9, 1),
        end_date=date(2026, 9, 30),
        status=Contract.Status.ACTIVE,
    )
    ContractVersion.objects.create(
        contract=contract,
        version_number=1,
        effective_from=date(2026, 9, 1),
        effective_until=date(2026, 9, 30),
        period_amount=550_000,
        change_reason="Inicio",
        created_by=admin,
    )
    BillingRule.objects.create(
        contract=contract,
        frequency=BillingRule.Frequency.MONTHLY,
        due_days=[11, 26],
        split_percentages=[50, 50],
    )

    created = generate_contract_schedule(contract)

    assert len(created) == 1
    charge = ScheduledCharge.objects.get()
    assert charge.amount == 550_000
    assert list(charge.installments.values_list("amount", flat=True)) == [275_000, 275_000]
    assert sum(charge.installments.values_list("amount", flat=True)) == 550_000


@pytest.mark.django_db
def test_waiver_resolves_installment_without_bank_movement(admin, client):
    contract = Contract.objects.create(
        client=client, name="Mensualidad", start_date=date(2026, 9, 1), end_date=date(2026, 9, 30)
    )
    version = ContractVersion.objects.create(
        contract=contract,
        version_number=1,
        effective_from=date(2026, 9, 1),
        period_amount=550_000,
        change_reason="Inicio",
        created_by=admin,
    )
    charge = ScheduledCharge.objects.create(
        contract=contract,
        contract_version=version,
        service_period_start=date(2026, 9, 1),
        service_period_end=date(2026, 9, 30),
        amount=550_000,
    )
    installment = Installment.objects.create(
        charge=charge, sequence=1, due_date=date(2026, 9, 11), amount=275_000
    )

    grant_waiver(installment=installment, amount=275_000, reason="Apoyo extraordinario", user=admin)

    installment.refresh_from_db()
    charge.refresh_from_db()
    assert installment.balance == 0
    assert installment.calculated_status(date(2026, 9, 12)) == Installment.Status.WAIVED
    assert charge.amount == 550_000
    assert charge.waived_amount == 275_000
    assert charge.net_collectible == 275_000


@pytest.mark.django_db
def test_partial_and_advance_payment_allocations(admin, client, account):
    contract = Contract.objects.create(
        client=client, name="Plan", start_date=date(2026, 9, 1), end_date=date(2026, 10, 31)
    )
    version = ContractVersion.objects.create(
        contract=contract,
        version_number=1,
        effective_from=date(2026, 9, 1),
        period_amount=500_000,
        change_reason="Inicio",
        created_by=admin,
    )
    first_charge = ScheduledCharge.objects.create(
        contract=contract,
        contract_version=version,
        service_period_start=date(2026, 9, 1),
        service_period_end=date(2026, 9, 30),
        amount=500_000,
    )
    second_charge = ScheduledCharge.objects.create(
        contract=contract,
        contract_version=version,
        service_period_start=date(2026, 10, 1),
        service_period_end=date(2026, 10, 31),
        amount=500_000,
    )
    first = Installment.objects.create(
        charge=first_charge, sequence=1, due_date=date(2026, 9, 15), amount=500_000
    )
    second = Installment.objects.create(
        charge=second_charge, sequence=1, due_date=date(2026, 10, 15), amount=500_000
    )
    payment = Payment.objects.create(
        client=client, bank_account=account, amount=800_000, received_at=timezone.now(), recorded_by=admin
    )
    record_payment(payment=payment, user=admin)

    allocate_payment(
        payment=payment,
        allocations=[
            {"installment_id": first.pk, "amount": 500_000},
            {"installment_id": second.pk, "amount": 300_000},
        ],
        user=admin,
    )

    assert Installment.objects.get(pk=first.pk).balance == 0
    assert Installment.objects.get(pk=second.pk).balance == 200_000
    assert payment.allocations.count() == 2
    payment.refresh_from_db()
    assert payment.bank_transaction.amount == 800_000


@pytest.mark.django_db
def test_payment_allocation_cannot_exceed_payment(admin, client, account):
    contract = Contract.objects.create(client=client, name="Plan", start_date=date(2026, 9, 1))
    version = ContractVersion.objects.create(
        contract=contract,
        version_number=1,
        effective_from=date(2026, 9, 1),
        period_amount=500_000,
        change_reason="Inicio",
        created_by=admin,
    )
    charge = ScheduledCharge.objects.create(
        contract=contract,
        contract_version=version,
        service_period_start=date(2026, 9, 1),
        service_period_end=date(2026, 9, 30),
        amount=500_000,
    )
    installment = Installment.objects.create(
        charge=charge, sequence=1, due_date=date(2026, 9, 15), amount=500_000
    )
    payment = Payment.objects.create(
        client=client, bank_account=account, amount=300_000, received_at=timezone.now(), recorded_by=admin
    )
    with pytest.raises(ValueError, match="supera el valor disponible"):
        allocate_payment(
            payment=payment, allocations=[{"installment_id": installment.pk, "amount": 400_000}], user=admin
        )


@pytest.mark.django_db
def test_provision_recalculates_after_extra_contribution(admin, client):
    category = ExpenseCategory.objects.create(name="Infraestructura")
    plan = ProvisionPlan.objects.create(
        name="Renovación",
        owner_type=ProvisionPlan.Owner.CLIENT,
        client=client,
        category=category,
        target_amount=240_000,
        contribution_start_date=date(2026, 9, 1),
        due_date=date(2026, 11, 30),
    )
    assert plan.suggested_contribution(date(2026, 9, 1)) == 80_000
    contribution = contribute(plan=plan, amount=100_000, user=admin)
    plan.refresh_from_db()
    assert contribution.suggested_amount_snapshot == 80_000
    assert plan.reserved_balance == 100_000
    assert plan.remaining_amount == 140_000


@pytest.mark.django_db
def test_distribution_25_each_sums_exactly(admin):
    period = FinancialPeriod.objects.create(year=2026, month=9)
    policy = DistributionPolicy.objects.create(
        name="Política actual", effective_from=date(2026, 9, 1), reason="Política inicial"
    )
    for name, kind in [
        ("Global Automate", "global"),
        ("Santiago", "user"),
        ("Cubillos", "user"),
        ("Johan", "user"),
    ]:
        DistributionParticipant.objects.create(
            policy=policy,
            kind=kind,
            display_name=name,
            percentage_basis_points=2500,
            user=admin if name == "Santiago" else None,
        )

    run = calculate_distribution(
        period=period, distributable_base=1_000_000, policy=policy, snapshot={}, user=admin
    )

    assert list(run.lines.values_list("amount", flat=True)) == [250_000] * 4
    assert sum(run.lines.values_list("amount", flat=True)) == 1_000_000
