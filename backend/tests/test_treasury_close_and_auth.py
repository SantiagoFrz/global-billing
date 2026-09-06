import pyotp
import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import TOTPDevice
from apps.accounts.services import decrypt_secret
from apps.periods.models import FinancialPeriod
from apps.periods.services import close_period, reopen_period
from apps.treasury.models import BankAccount, InternalTransfer
from apps.treasury.services import execute_internal_transfer


@pytest.mark.django_db
def test_internal_transfer_balances_to_zero(admin):
    source = BankAccount.objects.create(name="Origen", opening_balance=1_000_000)
    target = BankAccount.objects.create(name="Destino", opening_balance=0)
    transfer = InternalTransfer.objects.create(
        from_account=source,
        to_account=target,
        amount=300_000,
        occurred_at=timezone.now(),
        reason="Mover liquidez",
        recorded_by=admin,
    )
    execute_internal_transfer(transfer=transfer, user=admin)
    transfer.refresh_from_db()
    assert transfer.out_transaction.amount == -300_000
    assert transfer.in_transaction.amount == 300_000
    assert transfer.out_transaction.amount + transfer.in_transaction.amount == 0


@pytest.mark.django_db
def test_close_reopen_preserves_close_version(admin):
    period = FinancialPeriod.objects.create(year=2026, month=9)
    checklist = {str(step): True for step in range(1, 11)}
    close = close_period(period=period, snapshot={"available": 1_000_000}, checklist=checklist, user=admin)
    event = reopen_period(period=period, reason="Faltó registrar un gasto", user=admin)
    period.refresh_from_db()
    assert close.version == 1
    assert event.previous_close_id == close.pk
    assert period.status == FinancialPeriod.Status.REOPENED
    assert period.close_versions.count() == 1


@pytest.mark.django_db
def test_login_with_totp(admin):
    api = APIClient()
    response = api.post(
        "/api/v1/auth/login/", {"email": admin.email, "password": "A-strong-password-123!"}, format="json"
    )
    assert response.status_code == 200
    assert response.data["requires2FA"] is False
    setup = api.post("/api/v1/auth/2fa/setup/", {}, format="json")
    assert setup.status_code == 200
    secret = decrypt_secret(TOTPDevice.objects.get(user=admin).encrypted_secret)
    confirm = api.post("/api/v1/auth/2fa/confirm/", {"code": pyotp.TOTP(secret).now()}, format="json")
    assert confirm.status_code == 200
    assert len(confirm.data["backupCodes"]) == 8
    api.post("/api/v1/auth/logout/", {}, format="json")
    response = api.post(
        "/api/v1/auth/login/", {"email": admin.email, "password": "A-strong-password-123!"}, format="json"
    )
    assert response.data["requires2FA"] is True
    verify = api.post("/api/v1/auth/2fa/verify/", {"code": pyotp.TOTP(secret).now()}, format="json")
    assert verify.status_code == 200
