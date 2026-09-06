from django.db import transaction

from apps.audit.services import audit_event

from .models import BankTransaction, InternalTransfer


@transaction.atomic
def execute_internal_transfer(*, transfer: InternalTransfer, user) -> InternalTransfer:
    if transfer.from_account_id == transfer.to_account_id or transfer.amount <= 0:
        raise ValueError("La transferencia requiere cuentas distintas y un monto positivo.")
    if transfer.out_transaction_id or transfer.in_transaction_id:
        return transfer
    out_tx = BankTransaction.objects.create(
        account=transfer.from_account,
        kind=BankTransaction.Kind.TRANSFER_OUT,
        amount=-transfer.amount,
        occurred_at=transfer.occurred_at,
        description=transfer.reason,
        recorded_by=user,
        source_type="internal_transfer",
        source_id=str(transfer.pk),
    )
    in_tx = BankTransaction.objects.create(
        account=transfer.to_account,
        kind=BankTransaction.Kind.TRANSFER_IN,
        amount=transfer.amount,
        occurred_at=transfer.occurred_at,
        description=transfer.reason,
        recorded_by=user,
        source_type="internal_transfer",
        source_id=str(transfer.pk),
    )
    transfer.out_transaction = out_tx
    transfer.in_transaction = in_tx
    transfer.save(update_fields=["out_transaction", "in_transaction", "updated_at"])
    audit_event(
        user=user,
        action="treasury.transfer.executed",
        instance=transfer,
        after={"amount": transfer.amount, "net": 0},
    )
    return transfer
