# Despliegue en VPS

## Prerrequisitos

- Acceso SSH, Docker Compose y registro DNS de `billing.globalautomate.co` apuntando al VPS.
- Nginx existente inspeccionado y respaldado.
- Secretos de `.env` entregados por canal seguro.

## Procedimiento

1. Clonar en `/opt/global-billing` y crear `.env` con `DEBUG=false`.
2. `docker compose up --build -d`.
3. Crear cada administrador con `docker compose exec backend python manage.py bootstrap_admin`, cambiando variables entre ejecuciones.
4. Añadir solo el server block de `deploy/nginx/` al Nginx existente y ejecutar `nginx -t`.
5. Obtener TLS: `certbot --nginx -d billing.globalautomate.co`.
6. Verificar `/api/health/`, login, TOTP, jobs, documento y backup.
7. Activar cron del backup y ensayar restauración aislada.

No activar HSTS hasta confirmar HTTPS. Django habilita cookies Secure, HSTS y redirección SSL con `DEBUG=false`.

## Actualización

```bash
git pull --ff-only
docker compose build
docker compose up -d
docker compose exec backend python manage.py migrate --noinput
```

Revisar `docker compose ps` y logs. El deploy automático no está habilitado.
