from __future__ import annotations

import os

from django.core.management.base import BaseCommand, CommandError

from apps.accounts.models import User


class Command(BaseCommand):
    help = "Crea el administrador inicial desde variables de entorno, sin imprimir la contraseña."

    def handle(self, *args, **options):
        email = os.getenv("INITIAL_ADMIN_EMAIL", "").strip().lower()
        name = os.getenv("INITIAL_ADMIN_NAME", "").strip()
        password = os.getenv("INITIAL_ADMIN_PASSWORD", "")
        if not email or not name or not password:
            raise CommandError(
                "Define INITIAL_ADMIN_EMAIL, INITIAL_ADMIN_NAME e INITIAL_ADMIN_PASSWORD."
            )
        if len(password) < 12:
            raise CommandError("La contraseña inicial debe tener al menos 12 caracteres.")
        user, created = User.objects.get_or_create(
            email=email,
            defaults={"full_name": name, "is_staff": True, "is_superuser": True},
        )
        if not created:
            self.stdout.write(self.style.WARNING("El usuario ya existe; no se modificó."))
            return
        user.set_password(password)
        user.save(update_fields=["password"])
        self.stdout.write(self.style.SUCCESS(f"Administrador creado: {email}"))
