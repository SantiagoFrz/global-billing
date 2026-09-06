from django.db import models

from apps.common.models import TimeStampedUUIDModel


class Client(TimeStampedUUIDModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Activo"
        INACTIVE = "inactive", "Inactivo"
        LEAD = "lead", "Prospecto"
        ARCHIVED = "archived", "Archivado"

    name = models.CharField(max_length=180)
    legal_name = models.CharField(max_length=220, blank=True)
    billing_prefix = models.CharField(max_length=24, unique=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE, db_index=True)
    contact_name = models.CharField(max_length=180, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=40, blank=True)
    notes = models.TextField(blank=True)
    legacy_source = models.BooleanField(default=False)

    class Meta:
        ordering = ("name",)
        indexes = [models.Index(fields=["status", "name"])]

    def save(self, *args, **kwargs):
        self.billing_prefix = self.billing_prefix.strip().upper()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


class ClientBillingProfile(TimeStampedUUIDModel):
    client = models.OneToOneField(Client, on_delete=models.CASCADE, related_name="billing_profile")
    billing_name = models.CharField(max_length=220)
    identification_type = models.CharField(max_length=30, blank=True)
    identification = models.CharField(max_length=80, blank=True)
    billing_email = models.EmailField(blank=True)
    billing_address = models.TextField(blank=True)
    payment_notes = models.TextField(blank=True)
