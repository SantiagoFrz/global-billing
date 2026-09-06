from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedUUIDModel


class Document(TimeStampedUUIDModel):
    class Type(models.TextChoices):
        CONTRACT = "contract", "Contrato"
        QUOTE = "quote", "Cotización"
        CHARGE = "charge", "Cuenta de cobro"
        PAYMENT_PROOF = "payment_proof", "Comprobante"
        SUPPLIER_INVOICE = "supplier_invoice", "Factura proveedor"
        RECEIPT = "receipt", "Recibo"
        TAX = "tax", "RUT"
        CERTIFICATE = "certificate", "Certificado"
        ANNEX = "annex", "Anexo"
        OTHER = "other", "Otro"

    name = models.CharField(max_length=220)
    document_type = models.CharField(max_length=30, choices=Type.choices, db_index=True)
    client = models.ForeignKey(
        "clients.Client", null=True, blank=True, on_delete=models.PROTECT, related_name="documents"
    )
    project = models.ForeignKey(
        "projects.Project", null=True, blank=True, on_delete=models.PROTECT, related_name="documents"
    )
    contract = models.ForeignKey(
        "contracts.Contract", null=True, blank=True, on_delete=models.PROTECT, related_name="documents"
    )
    document_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    archived = models.BooleanField(default=False)


class DocumentVersion(TimeStampedUUIDModel):
    document = models.ForeignKey(Document, on_delete=models.PROTECT, related_name="versions")
    version_number = models.PositiveIntegerField()
    file = models.FileField(upload_to="documents/%Y/%m/")
    original_filename = models.CharField(max_length=240)
    content_type = models.CharField(max_length=120)
    size_bytes = models.PositiveBigIntegerField()
    sha256 = models.CharField(max_length=64)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="document_versions_uploaded"
    )
    notes = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["document", "version_number"], name="unique_document_version")
        ]


class InternalNote(TimeStampedUUIDModel):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="internal_notes"
    )
    text = models.TextField()
    client = models.ForeignKey(
        "clients.Client", null=True, blank=True, on_delete=models.CASCADE, related_name="internal_notes"
    )
    project = models.ForeignKey(
        "projects.Project", null=True, blank=True, on_delete=models.CASCADE, related_name="internal_notes"
    )
    contract = models.ForeignKey(
        "contracts.Contract", null=True, blank=True, on_delete=models.CASCADE, related_name="internal_notes"
    )
