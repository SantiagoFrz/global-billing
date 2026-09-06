from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.billing.models import BillingIssuer
from apps.billing.services import generate_contract_schedule
from apps.clients.models import Client
from apps.contracts.models import BillingRule, Contract, ContractVersion
from apps.distributions.models import DistributionParticipant, DistributionPolicy
from apps.expenses.models import Expense, ExpenseCategory
from apps.payments.models import Payment
from apps.payments.services import allocate_payment, record_payment
from apps.periods.models import FinancialPeriod
from apps.provisions.models import ProvisionPlan
from apps.provisions.services import contribute
from apps.treasury.models import BankAccount, FundMovement, InternalFund


class Command(BaseCommand):
    help = "Crea datos falsos e idempotentes para desarrollo. Nunca debe ejecutarse en producción."

    @transaction.atomic
    def handle(self, *args, **options):
        user, created = User.objects.get_or_create(
            email="demo@global.test", defaults={"full_name": "Admin Demo", "is_admin": True, "is_staff": True}
        )
        if created:
            user.set_password("Demo-Only-Password-123!")
            user.save(update_fields=["password"])
        account, _ = BankAccount.objects.get_or_create(
            name="Cuenta principal demo",
            defaults={
                "bank": "Banco ficticio",
                "account_type": "Ahorros",
                "last_digits": "0042",
                "opening_balance": 500_000,
            },
        )
        infra, _ = ExpenseCategory.objects.get_or_create(name="Infraestructura")
        software, _ = ExpenseCategory.objects.get_or_create(name="Software de terceros")
        client, _ = Client.objects.get_or_create(
            name="Órbita Café",
            defaults={
                "billing_prefix": "ORBITA",
                "contact_name": "Equipo administrativo",
                "contact_email": "facturacion@orbita.test",
            },
        )
        contract, _ = Contract.objects.get_or_create(
            client=client,
            name="Automatización comercial",
            defaults={
                "start_date": date(2026, 9, 1),
                "end_date": date(2026, 12, 31),
                "status": Contract.Status.ACTIVE,
            },
        )
        ContractVersion.objects.get_or_create(
            contract=contract,
            version_number=1,
            defaults={
                "effective_from": date(2026, 9, 1),
                "period_amount": 550_000,
                "change_reason": "Versión demo inicial",
                "created_by": user,
            },
        )
        BillingRule.objects.get_or_create(
            contract=contract,
            defaults={
                "frequency": BillingRule.Frequency.MONTHLY,
                "due_days": [11, 26],
                "split_percentages": [50, 50],
            },
        )
        generate_contract_schedule(contract)
        payment, _ = Payment.objects.get_or_create(
            client=client,
            reference="DEMO-001",
            defaults={
                "bank_account": account,
                "amount": 1_250_000,
                "received_at": timezone.now(),
                "recorded_by": user,
            },
        )
        record_payment(payment=payment, user=user)
        first = contract.scheduled_charges.first().installments.first()
        if not payment.allocations.exists():
            allocate_payment(
                payment=payment, allocations=[{"installment_id": first.pk, "amount": first.amount}], user=user
            )
        Expense.objects.get_or_create(
            concept="Servidor demo",
            defaults={
                "category": infra,
                "scope": Expense.Scope.GLOBAL,
                "amount": 185_000,
                "incurred_at": timezone.now(),
                "due_date": date(2026, 9, 20),
                "recorded_by": user,
            },
        )
        plan, _ = ProvisionPlan.objects.get_or_create(
            name="Renovación infraestructura demo",
            defaults={
                "owner_type": ProvisionPlan.Owner.GLOBAL,
                "category": infra,
                "target_amount": 480_000,
                "due_date": date(2026, 12, 15),
                "contribution_start_date": date(2026, 9, 1),
            },
        )
        if not plan.contributions.exists():
            contribute(plan=plan, amount=120_000, user=user)
        fund, _ = InternalFund.objects.get_or_create(name="Reserva operativa demo")
        if not fund.movements.exists():
            FundMovement.objects.create(
                fund=fund,
                amount=80_000,
                occurred_at=timezone.now(),
                reason="Aporte inicial demo",
                recorded_by=user,
            )
        policy, _ = DistributionPolicy.objects.get_or_create(
            name="25% Global / 75% socios demo",
            defaults={"effective_from": date(2026, 9, 1), "reason": "Política de demostración"},
        )
        if not policy.participants.exists():
            for label, kind in (
                ("Global Automate", "global"),
                ("Socio A", "legacy"),
                ("Socio B", "legacy"),
                ("Socio C", "legacy"),
            ):
                DistributionParticipant.objects.create(
                    policy=policy, kind=kind, display_name=label, percentage_basis_points=2500
                )
        FinancialPeriod.objects.get_or_create(year=2026, month=9)
        BillingIssuer.objects.get_or_create(
            display_name="Emisor Demo", defaults={"email": "emisor@global.test", "is_default": True}
        )
        self.stdout.write(self.style.SUCCESS("Datos demo listos. Usuario: demo@global.test"))
