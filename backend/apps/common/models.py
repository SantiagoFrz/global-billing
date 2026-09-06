from __future__ import annotations

import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class TimeStampedUUIDModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class FinancialRecord(TimeStampedUUIDModel):
    is_void = models.BooleanField(default=False)
    voided_at = models.DateTimeField(null=True, blank=True)
    voided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="+"
    )
    void_reason = models.TextField(blank=True)

    class Meta:
        abstract = True

    def clean(self) -> None:
        if self.is_void and not self.void_reason:
            raise ValidationError({"void_reason": "Debes indicar el motivo de anulación."})


def validate_non_negative(value: int) -> None:
    if value < 0:
        raise ValidationError("El valor no puede ser negativo.")


def money_field(**kwargs):
    return models.BigIntegerField(validators=[validate_non_negative], **kwargs)
