from __future__ import annotations

from django.db import transaction
from django.db.models import Sum

from apps.audit.services import audit_event
from apps.billing.models import Installment
from apps.treasury.models import BankTransaction

from .models import Payment, PaymentAllocation


@transaction.atomic
def record_payment(*, payment: Payment, user) -> Payment:
    payment = Payment.objects.select_for_update().get(pk=payment.pk)
    if payment.bank_transaction_id:
        return payment
    tx = BankTransaction.objects.create(
        account=payment.bank_account,
        kind=BankTransaction.Kind.PAYMENT,
        amount=payment.amount,
        occurred_at=payment.received_at,
        description=f"Pago recibido de {payment.client.name}",
        external_reference=payment.reference,
        recorded_by=user,
        source_type="payment",
        source_id=str(payment.pk),
    )
    payment.bank_transaction = tx
    payment.save(update_fields=["bank_transaction", "updated_at"])
    audit_event(
        user=user,
        action="payment.recorded",
        instance=payment,
        after={"amount": payment.amount, "bank_transaction": str(tx.pk)},
    )
    return payment


@transaction.atomic
def allocate_payment(*, payment: Payment, allocations: list[dict], user=None) -> list[PaymentAllocation]:
    payment = Payment.objects.select_for_update().get(pk=payment.pk)
    already_allocated = payment.allocations.filter(is_void=False).aggregate(total=Sum("amount"))["total"] or 0
    requested = sum(int(item["amount"]) for item in allocations)
    if requested <= 0 or already_allocated + requested > payment.amount:
        raise ValueError("El monto asignado supera el valor disponible del pago.")
    results: list[PaymentAllocation] = []
    for item in allocations:
        installment = (
            Installment.objects.select_for_update()
            .select_related("charge__contract__client")
            .get(pk=item["installment_id"])
        )
        amount = int(item["amount"])
        if installment.charge.contract.client_id != payment.client_id:
            raise ValueError("No puedes asignar un pago a una obligación de otro cliente.")
        if amount <= 0 or amount > installment.balance:
            raise ValueError("El monto asignado supera el saldo pendiente de la cuota.")
        allocation = PaymentAllocation.objects.create(payment=payment, installment=installment, amount=amount)
        results.append(allocation)
    audit_event(
        user=user,
        action="payment.allocated",
        instance=payment,
        after={"allocated": requested, "installments": [str(x.installment_id) for x in results]},
    )
    return results
