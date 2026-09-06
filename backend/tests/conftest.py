import pytest

from apps.accounts.models import User
from apps.clients.models import Client
from apps.treasury.models import BankAccount


@pytest.fixture
def admin(db):
    return User.objects.create_user(
        email="admin@example.test", password="A-strong-password-123!", full_name="Admin de prueba"
    )


@pytest.fixture
def client(db):
    return Client.objects.create(name="Cliente de prueba", billing_prefix="PRUEBA")


@pytest.fixture
def account(db):
    return BankAccount.objects.create(name="Cuenta de prueba", opening_balance=0)
