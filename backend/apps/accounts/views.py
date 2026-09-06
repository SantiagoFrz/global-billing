from __future__ import annotations

import base64
from io import BytesIO

import pyotp
import qrcode
from django.contrib.auth import authenticate, login, logout
from django.core.cache import cache
from django.middleware.csrf import get_token
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import BackupCode, TOTPDevice, User
from .services import decrypt_secret, encrypt_secret


def _client_ip(request) -> str:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    return (forwarded.split(",")[0] if forwarded else request.META.get("REMOTE_ADDR", "unknown")).strip()


class CSRFView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({"csrfToken": get_token(request)})


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        key = f"login-attempts:{_client_ip(request)}"
        attempts = cache.get(key, 0)
        if attempts >= 8:
            return Response({"detail": "Demasiados intentos. Intenta de nuevo en 15 minutos."}, status=429)
        user = authenticate(
            request, username=request.data.get("email", ""), password=request.data.get("password", "")
        )
        if not user or not user.is_active:
            cache.set(key, attempts + 1, 900)
            return Response(
                {"detail": "Correo o contraseña incorrectos."}, status=status.HTTP_400_BAD_REQUEST
            )
        cache.delete(key)
        device = TOTPDevice.objects.filter(user=user, confirmed=True).first()
        if device:
            request.session["pre_2fa_user_id"] = str(user.id)
            return Response({"requires2FA": True})
        login(request, user)
        return Response(
            {"requires2FA": False, "user": {"id": str(user.id), "name": user.full_name, "email": user.email}}
        )


class LogoutView(APIView):
    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SessionView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        if not request.user.is_authenticated:
            return Response({"authenticated": False})
        has_2fa = TOTPDevice.objects.filter(user=request.user, confirmed=True).exists()
        return Response(
            {
                "authenticated": True,
                "user": {
                    "id": str(request.user.id),
                    "name": request.user.full_name,
                    "email": request.user.email,
                    "twoFactorEnabled": has_2fa,
                },
            }
        )


class TOTPSetupView(APIView):
    def post(self, request):
        secret = pyotp.random_base32()
        device, _ = TOTPDevice.objects.update_or_create(
            user=request.user,
            defaults={"encrypted_secret": encrypt_secret(secret), "confirmed": False, "confirmed_at": None},
        )
        uri = pyotp.TOTP(secret).provisioning_uri(name=request.user.email, issuer_name="Global Billing")
        image = qrcode.make(uri)
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        qr = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()
        return Response({"secret": secret, "provisioningUri": uri, "qrCode": qr, "deviceId": device.pk})


class TOTPConfirmView(APIView):
    def post(self, request):
        device = TOTPDevice.objects.filter(user=request.user, confirmed=False).first()
        if not device or not pyotp.TOTP(decrypt_secret(device.encrypted_secret)).verify(
            str(request.data.get("code", "")), valid_window=1
        ):
            return Response({"detail": "El código no es válido."}, status=400)
        device.confirmed = True
        device.confirmed_at = timezone.now()
        device.save(update_fields=["confirmed", "confirmed_at"])
        codes = BackupCode.generate_for(request.user)
        return Response({"backupCodes": codes})


class TOTPVerifyView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        user_id = request.session.get("pre_2fa_user_id")
        user = User.objects.filter(id=user_id, is_active=True).first()
        if not user:
            return Response({"detail": "La sesión de verificación expiró."}, status=400)
        code = str(request.data.get("code", ""))
        device = TOTPDevice.objects.filter(user=user, confirmed=True).first()
        valid = bool(
            device and pyotp.TOTP(decrypt_secret(device.encrypted_secret)).verify(code, valid_window=1)
        )
        if not valid:
            backup = BackupCode.objects.filter(
                user=user, code_hash=BackupCode.hash_code(code), used_at__isnull=True
            ).first()
            if backup:
                backup.used_at = timezone.now()
                backup.save(update_fields=["used_at"])
                valid = True
        if not valid:
            return Response({"detail": "El código no es válido."}, status=400)
        login(request, user)
        request.session.pop("pre_2fa_user_id", None)
        return Response({"user": {"id": str(user.id), "name": user.full_name, "email": user.email}})
