from django.urls import path

from .views import (
    CSRFView,
    LoginView,
    LogoutView,
    SessionView,
    TOTPConfirmView,
    TOTPSetupView,
    TOTPVerifyView,
)

urlpatterns = [
    path("csrf/", CSRFView.as_view()),
    path("login/", LoginView.as_view()),
    path("logout/", LogoutView.as_view()),
    path("session/", SessionView.as_view()),
    path("2fa/setup/", TOTPSetupView.as_view()),
    path("2fa/confirm/", TOTPConfirmView.as_view()),
    path("2fa/verify/", TOTPVerifyView.as_view()),
]
