from django.conf import settings
from django.db import connection
from django.http import JsonResponse


def health(request):
    database = "ok"
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        database = "error"
    status = 200 if database == "ok" else 503
    return JsonResponse(
        {
            "status": "ok" if status == 200 else "degraded",
            "database": database,
            "version": settings.APP_VERSION,
        },
        status=status,
    )
