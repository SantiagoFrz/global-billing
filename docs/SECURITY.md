# Seguridad

- Sesiones server-side; cookies `HttpOnly`, `Secure` en producción y `SameSite=Lax`.
- CSRF en mutaciones; no se guardan JWT ni secretos en `localStorage`.
- Login limitado por IP: 8 intentos en 15 minutos.
- TOTP con secreto cifrado Fernet y backup codes hasheados.
- Contraseñas de mínimo 12 caracteres y permisos internos de administrador en toda la API.
- Headers anti-sniffing/clickjacking, HSTS/SSL en producción.
- Auditoría before/after; anulación en vez de borrado financiero.
- Archivos con UUID físico, allowlist y 10 MB máximo.

Cada administrador debe tener cuenta, TOTP y backup codes individuales. Rotar `DJANGO_SECRET_KEY`, `FIELD_ENCRYPTION_KEY` y DB ante exposición. La clave Fernet debe estar en el gestor seguro de configuración, no en el dump.

Antes de producción: `python manage.py check --deploy`, revisar CORS/CSRF y verificar `X-Forwarded-Proto` de Nginx.
