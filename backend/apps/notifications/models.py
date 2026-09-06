from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedUUIDModel


class Notification(TimeStampedUUIDModel):
    class Severity(models.TextChoices):
        INFO = "info", "Información"
        WARNING = "warning", "Advertencia"
        CRITICAL = "critical", "Crítica"
        SUCCESS = "success", "Éxito"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    title = models.CharField(max_length=220)
    body = models.TextField()
    severity = models.CharField(max_length=12, choices=Severity.choices, default=Severity.INFO)
    event_key = models.CharField(max_length=180)
    action_url = models.CharField(max_length=300, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    provider = models.CharField(max_length=30, default="in_app")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["recipient", "event_key"], name="unique_notification_event_per_user"
            )
        ]
        ordering = ("-created_at",)
