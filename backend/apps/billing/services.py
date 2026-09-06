from __future__ import annotations

import calendar
import hashlib
from datetime import date
from io import BytesIO

from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from apps.audit.services import audit_event
from apps.contracts.models import BillingRule, Contract, ContractVersion

from .models import (
    BillingIssuer,
    BillingSequence,
    ChargeDocument,
    GeneratedMessage,
    Installment,
    ScheduledCharge,
    Waiver,
)


def add_months(value: date, months: int) -> date:
    target_month = value.month - 1 + months
    year = value.year + target_month // 12
    month = target_month % 12 + 1
    return date(year, month, min(value.day, calendar.monthrange(year, month)[1]))


def month_end(value: date) -> date:
    return date(value.year, value.month, calendar.monthrange(value.year, value.month)[1])


def due_date_for(period: date, day: int) -> date:
    return date(period.year, period.month, min(day, calendar.monthrange(period.year, period.month)[1]))


def _version_for(contract: Contract, period_start: date) -> ContractVersion:
    version = (
        contract.versions.filter(effective_from__lte=period_start)
        .filter(models.Q(effective_until__isnull=True) | models.Q(effective_until__gte=period_start))
        .order_by("-effective_from", "-version_number")
        .first()
    )
    if not version:
        raise ValueError(f"No existe una versión contractual vigente para {period_start:%Y-%m-%d}.")
    return version


def _split_amount(amount: int, percentages: list[int], count: int) -> list[int]:
    percentages = percentages or ([100 // count] * count)
    if len(percentages) != count or sum(percentages) != 100:
        raise ValueError("La división de cuotas debe tener un porcentaje por fecha y sumar 100%.")
    pieces: list[int] = []
    allocated = 0
    for index, percentage in enumerate(percentages):
        piece = amount - allocated if index == count - 1 else amount * percentage // 100
        pieces.append(piece)
        allocated += piece
    return pieces


@transaction.atomic
def generate_contract_schedule(contract: Contract, *, through: date | None = None) -> list[ScheduledCharge]:
    contract = Contract.objects.select_for_update().get(pk=contract.pk)
    rule: BillingRule = contract.billing_rule
    end = (
        min(x for x in [contract.end_date, through] if x is not None)
        if (contract.end_date or through)
        else add_months(contract.start_date, 12)
    )
    created: list[ScheduledCharge] = []
    cursor = date(contract.start_date.year, contract.start_date.month, 1)
    step = {
        BillingRule.Frequency.ONCE: 1200,
        BillingRule.Frequency.MONTHLY: 1,
        BillingRule.Frequency.BIMONTHLY: 2,
        BillingRule.Frequency.QUARTERLY: 3,
    }.get(rule.frequency, 1)
    while cursor <= end:
        version = _version_for(contract, cursor)
        charge, was_created = ScheduledCharge.objects.get_or_create(
            contract=contract,
            service_period_start=cursor,
            is_void=False,
            defaults={
                "contract_version": version,
                "service_period_end": min(month_end(add_months(cursor, step - 1)), end),
                "amount": version.period_amount,
            },
        )
        if was_created:
            days = rule.due_days or [contract.start_date.day]
            amounts = _split_amount(charge.amount, list(rule.split_percentages), len(days))
            Installment.objects.bulk_create(
                [
                    Installment(
                        charge=charge, sequence=i + 1, due_date=due_date_for(cursor, day), amount=amounts[i]
                    )
                    for i, day in enumerate(days)
                ]
            )
            created.append(charge)
        if step == 1200:
            break
        cursor = add_months(cursor, step)
    return created


@transaction.atomic
def grant_waiver(*, installment: Installment, amount: int, reason: str, user) -> Waiver:
    installment = Installment.objects.select_for_update().select_related("charge").get(pk=installment.pk)
    if amount <= 0 or amount > installment.balance:
        raise ValueError("La condonación debe ser positiva y no superar el saldo pendiente.")
    waiver = Waiver.objects.create(
        installment=installment, amount=amount, reason=reason, granted_by=user, granted_at=timezone.now()
    )
    installment.waived_amount = models.F("waived_amount") + amount
    installment.save(update_fields=["waived_amount", "updated_at"])
    charge = installment.charge
    charge.waived_amount = models.F("waived_amount") + amount
    charge.save(update_fields=["waived_amount", "updated_at"])
    audit_event(
        user=user,
        action="billing.waiver.granted",
        instance=waiver,
        after={"amount": amount, "reason": reason},
    )
    return waiver


MESSAGE_VARIANTS = (
    "Hola, equipo de {client}. Esperamos que estén muy bien. Les compartimos la cuenta de cobro {number}, correspondiente a {concept} por {amount}.",
    "Buen día, equipo de {client}. Adjuntamos la cuenta {number} por {amount}, asociada a {concept}. Quedamos atentos a cualquier inquietud.",
    "Hola, {client}. Les hacemos llegar la cuenta de cobro {number} correspondiente a {concept}, con un valor de {amount}. Muchas gracias.",
)


def format_cop(value: int) -> str:
    return "$" + f"{value:,}".replace(",", ".")


@transaction.atomic
def generate_charge_document(
    *, installment: Installment, issuer: BillingIssuer, user=None, force_revision: bool = False
) -> ChargeDocument:
    installment = (
        Installment.objects.select_for_update()
        .select_related("charge__contract__client")
        .get(pk=installment.pk)
    )
    client = installment.charge.contract.client
    concept = f"Servicios {installment.charge.service_period_start:%d/%m/%Y} - {installment.charge.service_period_end:%d/%m/%Y}"
    fingerprint = hashlib.sha256(
        f"{installment.pk}:{installment.amount}:{installment.waived_amount}:{issuer.pk}:{concept}".encode()
    ).hexdigest()
    current = installment.documents.filter(is_outdated=False, is_void=False).first()
    if current and current.source_fingerprint == fingerprint and not force_revision:
        return current
    if current:
        current.is_outdated = True
        current.save(update_fields=["is_outdated", "updated_at"])
    sequence, _ = BillingSequence.objects.select_for_update().get_or_create(client=client)
    sequence.last_number += 1
    sequence.save(update_fields=["last_number", "updated_at"])
    consecutive = f"{client.billing_prefix}-{sequence.last_number:03d}"
    revision = (installment.documents.aggregate(max=models.Max("revision"))["max"] or 0) + 1
    document = ChargeDocument.objects.create(
        installment=installment,
        issuer=issuer,
        consecutive=consecutive,
        revision=revision,
        concept=concept,
        amount=installment.balance,
        source_fingerprint=fingerprint,
    )
    message_index = int(hashlib.sha256(f"{client.pk}:{revision}".encode()).hexdigest(), 16) % len(
        MESSAGE_VARIANTS
    )
    GeneratedMessage.objects.create(
        charge_document=document,
        variant_key=f"local-{message_index + 1}",
        body=MESSAGE_VARIANTS[message_index].format(
            client=client.name, number=consecutive, concept=concept, amount=format_cop(document.amount)
        ),
        created_by=user,
    )
    render_charge_document_pdf(document)
    audit_event(
        user=user,
        action="billing.document.generated",
        instance=document,
        after={"consecutive": consecutive, "amount": document.amount},
    )
    return document


def render_charge_document_pdf(document: ChargeDocument) -> None:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    purple = HexColor("#522e88")
    pdf.setFillColor(purple)
    pdf.rect(0, height - 42 * mm, width, 42 * mm, fill=1, stroke=0)
    pdf.setFillColorRGB(1, 1, 1)
    pdf.setFont("Helvetica-Bold", 21)
    pdf.drawString(22 * mm, height - 24 * mm, "GLOBAL AUTOMATE")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(22 * mm, height - 32 * mm, "Cuenta de cobro")
    pdf.setFillColorRGB(0.12, 0.1, 0.18)
    pdf.setFont("Helvetica-Bold", 15)
    pdf.drawString(22 * mm, height - 62 * mm, document.consecutive)
    pdf.setFont("Helvetica", 10)
    client = document.installment.charge.contract.client
    rows = [
        ("Cliente", client.legal_name or client.name),
        ("Concepto", document.concept),
        (
            "Periodo",
            f"{document.installment.charge.service_period_start:%d/%m/%Y} - {document.installment.charge.service_period_end:%d/%m/%Y}",
        ),
        ("Fecha límite", f"{document.installment.due_date:%d/%m/%Y}"),
        ("Emisor", document.issuer.display_name),
    ]
    y = height - 78 * mm
    for label, value in rows:
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawString(22 * mm, y, label.upper())
        pdf.setFont("Helvetica", 11)
        pdf.drawString(55 * mm, y, str(value)[:90])
        y -= 11 * mm
    pdf.setFillColor(purple)
    pdf.roundRect(22 * mm, y - 12 * mm, width - 44 * mm, 24 * mm, 4 * mm, fill=1, stroke=0)
    pdf.setFillColorRGB(1, 1, 1)
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawCentredString(width / 2, y - 3 * mm, format_cop(document.amount))
    pdf.setFillColorRGB(0.35, 0.33, 0.4)
    pdf.setFont("Helvetica", 8)
    pdf.drawString(22 * mm, 20 * mm, "Documento administrativo interno. No constituye factura electrónica.")
    pdf.showPage()
    pdf.save()
    document.pdf_file.save(
        f"{document.consecutive}-r{document.revision}.pdf", ContentFile(buffer.getvalue()), save=True
    )


# Avoid importing models at module initialization before Django app loading finishes.
from django.db import models  # noqa: E402
