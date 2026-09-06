from django.db import models

from apps.common.models import TimeStampedUUIDModel


class Service(TimeStampedUUIDModel):
    name = models.CharField(max_length=160, unique=True)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name


class Project(TimeStampedUUIDModel):
    class Status(models.TextChoices):
        PLANNED = "planned", "Planeado"
        ACTIVE = "active", "Activo"
        PAUSED = "paused", "Pausado"
        COMPLETED = "completed", "Completado"
        CANCELLED = "cancelled", "Cancelado"

    client = models.ForeignKey("clients.Client", on_delete=models.PROTECT, related_name="projects")
    name = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    services = models.ManyToManyField(Service, related_name="projects", blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE, db_index=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ("client__name", "name")
        constraints = [
            models.UniqueConstraint(fields=["client", "name"], name="unique_project_name_per_client")
        ]

    def __str__(self) -> str:
        return f"{self.client}: {self.name}"
