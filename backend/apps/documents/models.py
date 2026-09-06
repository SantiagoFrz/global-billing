import uuid
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.common.models import TimeStampedUUIDModel

ALLOWED_DOCUMENT_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".docx", ".xlsx"}
ALLOWED_DOCUMENT_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}
MAX_DOCUMENT_SIZE = 10 * 1024 * 1024


def secure_document_path(instance, filename: str) -> str:
    extension = Path(filename).suffix.lower()
    created_at = instance.created_at or timezone.now()
    return f"documents/{created_at:%Y/%m}/{uuid.uuid4().hex}{extension}"


def validate_document_file(file) -> None:
    extension = Path(file.name).suffix.lower()
    content_type = getattr(file, "content_type", "")
    if extension not in ALLOWED_DOCUMENT_EXTENSIONS:
        raise ValidationError("Este tipo de archivo no está permitido.")
    if content_type and content_type not in ALLOWED_DOCUMENT_TYPES:
        raise ValidationError("El contenido del archivo no coincide con un formato permitido.")
    if file.size > MAX_DOCUMENT_SIZE:
        raise ValidationError("El archivo supera el límite de 10 MB.")


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
    file = models.FileField(upload_to=secure_document_path, validators=[validate_document_file])
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
