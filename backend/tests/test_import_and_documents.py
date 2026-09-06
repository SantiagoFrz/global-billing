from __future__ import annotations

from io import StringIO

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import override_settings
from openpyxl import Workbook

from apps.billing.models import BillingIssuer, Installment, ScheduledCharge
from apps.billing.services import generate_charge_document
from apps.contracts.models import Contract, ContractVersion
from apps.documents.models import MAX_DOCUMENT_SIZE, validate_document_file
from apps.reporting.models import ImportBatch, LegacyRecord, ReconciliationIssue


@pytest.mark.django_db
def test_money_import_is_idempotent_and_preserves_source(tmp_path):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Hoja 1"
    sheet["A3"] = "Junio-Julio"
    sheet["B3"] = 525_000
    sheet["C3"] = "Cliente legado"
    sheet["H3"] = "VPS"
    sheet["I3"] = 100_000
    sheet["Z3"] = 100_000
    sheet["AA3"] = 425_000
    path = tmp_path / "Money.xlsx"
    workbook.save(path)

    dry_output = StringIO()
    call_command("import_money_xlsx", str(path), dry_run=True, stdout=dry_output)
    assert '"dry_run": true' in dry_output.getvalue()
    assert ImportBatch.objects.count() == 0

    call_command("import_money_xlsx", str(path), stdout=StringIO())
    call_command("import_money_xlsx", str(path), stdout=StringIO())
    assert ImportBatch.objects.count() == 1
    assert LegacyRecord.objects.filter(source_cell="B3", legacy_period_label="Junio-Julio").exists()
    assert ReconciliationIssue.objects.filter(code="income_total_mismatch").exists()


def test_document_allowlist_and_size_validation():
    good = SimpleUploadedFile("contrato.pdf", b"%PDF-1.4", content_type="application/pdf")
    validate_document_file(good)

    executable = SimpleUploadedFile("malware.exe", b"MZ", content_type="application/octet-stream")
    with pytest.raises(ValidationError):
        validate_document_file(executable)

    oversized = SimpleUploadedFile(
        "grande.pdf", b"x" * (MAX_DOCUMENT_SIZE + 1), content_type="application/pdf"
    )
    with pytest.raises(ValidationError):
        validate_document_file(oversized)


@pytest.mark.django_db
def test_charge_document_pdf_is_reproducible_and_idempotent(tmp_path, admin, client):
    from datetime import date

    contract = Contract.objects.create(
        client=client, name="Servicio", start_date=date(2026, 9, 1), end_date=date(2026, 9, 30)
    )
    version = ContractVersion.objects.create(
        contract=contract,
        version_number=1,
        effective_from=date(2026, 9, 1),
        period_amount=300_000,
        change_reason="Inicio",
        created_by=admin,
    )
    charge = ScheduledCharge.objects.create(
        contract=contract,
        contract_version=version,
        service_period_start=date(2026, 9, 1),
        service_period_end=date(2026, 9, 30),
        amount=300_000,
    )
    installment = Installment.objects.create(
        charge=charge, sequence=1, due_date=date(2026, 9, 15), amount=300_000
    )
    issuer = BillingIssuer.objects.create(display_name="Emisor de prueba", is_default=True)

    with override_settings(MEDIA_ROOT=tmp_path):
        first = generate_charge_document(installment=installment, issuer=issuer, user=admin)
        second = generate_charge_document(installment=installment, issuer=issuer, user=admin)

    assert first.pk == second.pk
    assert first.consecutive == "PRUEBA-001"
    assert first.pdf_file.name.endswith("PRUEBA-001-r1.pdf")
    assert first.messages.count() == 1
