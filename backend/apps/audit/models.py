from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedUUIDModel


class AuditLog(TimeStampedUUIDModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT, related_name="audit_logs"
    )
    action = models.CharField(max_length=120, db_index=True)
    entity_type = models.CharField(max_length=120, db_index=True)
    entity_id = models.CharField(max_length=80, db_index=True)
    before = models.JSONField(default=dict, blank=True)
    after = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["entity_type", "entity_id", "-created_at"])]


class ActivityEvent(TimeStampedUUIDModel):
    client = models.ForeignKey(
        "clients.Client", null=True, blank=True, on_delete=models.CASCADE, related_name="activity"
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT, related_name="activity_events"
    )
    event_type = models.CharField(max_length=100, db_index=True)
    title = models.CharField(max_length=220)
    description = models.TextField(blank=True)
    entity_type = models.CharField(max_length=100, blank=True)
    entity_id = models.CharField(max_length=80, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ("-created_at",)
