from rest_framework.views import exception_handler


def spanish_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return response
    if isinstance(response.data, dict) and "detail" in response.data:
        detail = str(response.data["detail"])
        translations = {
            "Authentication credentials were not provided.": "Debes iniciar sesión.",
            "Invalid username/password.": "Correo o contraseña incorrectos.",
            "You do not have permission to perform this action.": "No tienes permiso para realizar esta acción.",
            "Not found.": "No encontramos el registro solicitado.",
        }
        response.data["detail"] = translations.get(detail, detail)
    return response
