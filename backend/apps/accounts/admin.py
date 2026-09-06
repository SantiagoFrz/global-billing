from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class GlobalBillingUserAdmin(UserAdmin):
    ordering = ("email",)
    list_display = ("email", "full_name", "is_active", "is_staff")
    fieldsets = UserAdmin.fieldsets + (("Global Billing", {"fields": ("full_name", "is_admin")}),)
