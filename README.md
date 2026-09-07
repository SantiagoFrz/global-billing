# Global Billing

Sistema interno administrativo, financiero, contractual y de tesorería de Global Automate. La fuente de verdad financiera vive en Django/PostgreSQL; la interfaz Next.js consume una API autenticada por sesión segura.

## Inicio rápido

Requisitos: Docker Engine 24+ y Docker Compose v2.

```bash
cp .env.example .env
# Reemplazar todos los valores `replace-with-*`
docker compose up --build -d
docker compose exec backend python manage.py bootstrap_admin
```

Abrir `http://localhost:3000`. El administrador debe activar TOTP antes de operar en producción.

`.env.example` está preparado para HTTP local. No uses la configuración de
producción (`DEBUG=false` + `SECURE_SSL_REDIRECT=true`) en localhost: las
peticiones internas del proxy serían redirigidas a HTTPS y el navegador
mostraría `Failed to fetch`.

## Desarrollo sin Docker

```bash
python3.12 -m venv .venv
. .venv/bin/activate
pip install -r backend/requirements-dev.txt
cd backend && python manage.py migrate && python manage.py runserver
```

En otra terminal:

```bash
cd frontend
npm ci
npm run dev
```

La configuración local usa SQLite si `POSTGRES_HOST` no está definido. Producción exige PostgreSQL.

## Pruebas y calidad

```bash
.venv/bin/ruff check backend
.venv/bin/pytest backend
cd frontend && npm run lint && npm run typecheck && npm test && npm run build
```

Los E2E requieren backend y frontend levantados: `cd frontend && npm run test:e2e`.

## Money.xlsx

```bash
cd backend
python manage.py import_money_xlsx /ruta/Money.xlsx --dry-run
python manage.py import_money_xlsx /ruta/Money.xlsx
```

El hash del archivo hace la importación idempotente. Los registros conservan hoja, fila y celda. Ver [guía de migración](docs/MIGRATION_MONEY_XLSX.md).

## Jobs, backups y operación

Celery Worker y Beat se levantan con Compose. Backup manual: `docker compose --profile backup run --rm backup`.

- [Arquitectura](docs/ARCHITECTURE.md)
- [Modelo de dominio](docs/DOMAIN_MODEL.md)
- [Reglas financieras](docs/FINANCIAL_RULES.md)
- [Configuración local](docs/LOCAL_SETUP.md)
- [Despliegue](docs/DEPLOYMENT.md)
- [Backups](docs/BACKUP_RESTORE.md)
- [Seguridad](docs/SECURITY.md)
- [Informe de entrega](docs/FINAL_REPORT.md)

No se deben commitear `.env`, secretos TOTP, credenciales, documentos ni dumps.
