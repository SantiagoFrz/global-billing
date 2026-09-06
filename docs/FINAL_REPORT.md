# Informe de entrega técnica

Fecha de corte: 6 de septiembre de 2026.

## Construido

- Backend Django/DRF modular con autenticación por sesión, TOTP, backup codes, rate limit y auditoría.
- Dominio para clientes, proyectos, servicios, contratos versionados, calendarios, cuotas, pagos/allocations, condonaciones, cuentas PDF, gastos/allocations, provisiones, fondos, tesorería, transferencias, distribución y cierre versionado.
- Dashboard con desglose navegable, calendario, aging, rentabilidad, proyección y exportaciones PDF/XLSX.
- Frontend Next.js/TypeScript responsive, modo oscuro/claro, design tokens Global Automate, command palette y wrapper `GlobalGlass` con fallback.
- Celery/Redis con jobs idempotentes de borradores, estados y alertas.
- Documentos en volumen con versiones, nombres físicos UUID, allowlist y tamaño máximo.
- Docker Compose, Nginx, CI, healthcheck, bootstrap seguro, backup/restore y rotación.

## Validación ejecutada

- Backend: 14 pruebas unitarias/de dominio/API, todas aprobadas.
- Frontend: lint y TypeScript strict aprobados; 3 pruebas de componentes/formato aprobadas; build de producción aprobado.
- Django: migraciones al día y `check --deploy` sin observaciones con configuración de producción simulada.
- Money.xlsx: importación real repetida; segundo pase idempotente.
- UI: login inspeccionado en viewport real. El runner no pudo descargar el binario de Chromium para ejecutar Playwright localmente; CI lo instala y ejecuta el smoke desktop/móvil.
- Dockerfile/Compose preparados; este runner no dispone del daemon Docker para construir las imágenes aquí.

## Migración recibida

1 lote, 26 registros y 3 issues de conciliación. No se materializaron movimientos ambiguos. Detalle completo en `MIGRATION_MONEY_XLSX.md`.

## Acciones pendientes externas

- Conectar una identidad autorizada de GitHub para publicar los commits locales.
- Entregar acceso SSH al VPS e información de Nginx existente.
- Confirmar que DNS apunta al VPS y emitir certificado Let's Encrypt.
- Crear las tres cuentas administrativas con contraseñas temporales individuales y enrolar TOTP.
- Entregar plantilla definitiva y datos legales de emisores; la plantilla provisional no contiene identificaciones inventadas.
- Configurar destino remoto de backup S3 compatible y ejecutar simulacro de restauración.

## Credenciales que deben conservar los administradores

No deben almacenarse en este documento ni en Git: `.env`, contraseña PostgreSQL, `DJANGO_SECRET_KEY`, `FIELD_ENCRYPTION_KEY`, TOTP, códigos de respaldo, acceso SSH/DNS y credenciales del proveedor de backups.

## Mantenimiento

- Revisar diariamente fallos de jobs y backup; semanalmente cartera/provisiones; mensualmente cierre y reconciliación.
- Instalar actualizaciones de seguridad en una rama, ejecutar CI y tomar backup antes del release.
- Ensayar restauración al menos trimestralmente.

## Mejoras futuras

Integración bancaria, Web Push/WhatsApp mediante adapters existentes, almacenamiento remoto de documentos, roles granulares y un módulo contable colombiano separado del dominio actual.
