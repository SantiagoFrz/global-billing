# Backup y restauración

El backup contiene dump comprimido de PostgreSQL, documentos y manifiesto. Rotación: 7 diarios, 4 semanales y 6 mensuales.

```bash
docker compose --profile backup run --rm backup
```

Programar diariamente desde cron/systemd. `BACKUP_S3_URI` prepara una copia remota cuando existe AWS CLI; guardar solo en el VPS no protege ante pérdida total.

## Restauración segura

1. Poner la aplicación en mantenimiento y crear otro backup.
2. Restaurar primero en base aislada.
3. Verificar conteos, último cierre, documentos y login.
4. Ejecutar `docker compose --profile restore run --rm restore /backups/daily/TIMESTAMP` solo sobre el destino confirmado.

El script usa `--clean --if-exists` y es destructivo sobre la base destino. Registrar operador, snapshot, hashes y resultado. Recomendación: simulacro trimestral.
