# Configuración local

## Docker

1. Copiar `.env.example` a `.env` y reemplazar secretos.
2. Ejecutar `docker compose up --build -d`.
3. Crear usuario con `docker compose exec backend python manage.py bootstrap_admin`.
4. Abrir `http://localhost:3000`.

Para desarrollo local, confirmar que `.env` conserve estos orígenes y opciones:

```dotenv
DEBUG=true
ALLOWED_HOSTS=localhost,127.0.0.1,backend
CSRF_TRUSTED_ORIGINS=http://localhost:3000
CORS_ALLOWED_ORIGINS=http://localhost:3000
SECURE_SSL_REDIRECT=false
```

Después de cambiar `.env`, recrear los contenedores con
`docker compose up -d --force-recreate`. Un error `Failed to fetch` no es un
estado vacío normal: indica que el proxy `/api` no consiguió respuesta del
backend.

El repositorio fija scripts shell en LF mediante `.gitattributes`. El Dockerfile también elimina CRLF del entrypoint para que los checkouts realizados desde Windows sean reproducibles.

Clave Fernet: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`.

## Desarrollo nativo

Backend usa SQLite solo como comodidad local. Instalar `backend/requirements-dev.txt`, migrar y levantar `manage.py runserver`. Frontend requiere Node 22 y `npm ci`.

Datos falsos opcionales: `cd backend && python manage.py seed_demo`. Nunca ejecutar el seed en producción.

Django guarda instantes timezone-aware y opera en `America/Bogota`; la interfaz formatea COP con `es-CO` sin decimales.
