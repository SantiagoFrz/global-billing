from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedUUIDModel


class ApplicationSetting(TimeStampedUUIDModel):
    key = models.CharField(max_length=120, unique=True)
    value = models.JSONField(default=dict)
    description = models.TextField(blank=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT, related_name="settings_updated"
    )


class ImportBatch(TimeStampedUUIDModel):
    class Status(models.TextChoices):
        DRY_RUN = "dry_run", "Simulación"
        IMPORTED = "imported", "Importado"
        REVIEW = "review", "Requiere revisión"
        FAILED = "failed", "Fallido"

    filename = models.CharField(max_length=240)
    sha256 = models.CharField(max_length=64)
    sheet_name = models.CharField(max_length=120)
    status = models.CharField(max_length=16, choices=Status.choices)
    summary = models.JSONField(default=dict)
    imported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT, related_name="imports"
    )

    class Meta:
        constraints = [models.UniqueConstraint(fields=["sha256", "status"], name="unique_import_file_status")]


class LegacyRecord(TimeStampedUUIDModel):
    batch = models.ForeignKey(ImportBatch, on_delete=models.PROTECT, related_name="records")
    record_type = models.CharField(max_length=30, db_index=True)
    legacy_period_label = models.CharField(max_length=120, blank=True)
    concept = models.CharField(max_length=240, blank=True)
    amount = models.BigIntegerField(null=True, blank=True)
    original_value = models.JSONField(default=dict)
    source_sheet = models.CharField(max_length=120)
    source_row = models.PositiveIntegerField()
    source_cell = models.CharField(max_length=20)
    mapped_entity_type = models.CharField(max_length=100, blank=True)
    mapped_entity_id = models.CharField(max_length=80, blank=True)
    requires_review = models.BooleanField(default=False)
    review_reason = models.TextField(blank=True)


class ReconciliationIssue(TimeStampedUUIDModel):
    batch = models.ForeignKey(ImportBatch, on_delete=models.CASCADE, related_name="issues")
    code = models.CharField(max_length=80)
    severity = models.CharField(max_length=16, default="warning")
    legacy_value = models.BigIntegerField(null=True, blank=True)
    recalculated_value = models.BigIntegerField(null=True, blank=True)
    difference = models.BigIntegerField(null=True, blank=True)
    message = models.TextField()
    source_reference = models.CharField(max_length=120)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="reconciliation_issues_resolved",
    )
