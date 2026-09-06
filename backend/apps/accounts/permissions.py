from rest_framework.permissions import BasePermission


class IsInternalAdmin(BasePermission):
    message = "Solo los administradores internos pueden realizar esta acción."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_active
            and request.user.is_admin
        )
