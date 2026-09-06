from __future__ import annotations

from .context import request_ip, request_user
from .models import AuditLog


def audit_event(*, action: str, instance, user=None, before=None, after=None, metadata=None) -> AuditLog:
    return AuditLog.objects.create(
        user=user or request_user.get(),
        action=action,
        entity_type=instance._meta.label_lower,
        entity_id=str(instance.pk),
        before=before or {},
        after=after or {},
        metadata=metadata or {},
        ip_address=request_ip.get(),
    )
