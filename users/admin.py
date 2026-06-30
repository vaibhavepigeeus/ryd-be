from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import (
    CoachCoachee,
    ResetTokens,
    UserAuditHistory,
    UserPasswordHistory,
    UserPermissions,
    Users,
    UserSessionManagement,
)


@admin.register(Users)
class UsersAdmin(BaseUserAdmin):
    ordering = ("email",)
    filter_horizontal = ()
    list_display = ("id", "user_name", "email", "role", "status", "is_staff", "is_superuser")
    list_filter = ("status", "role", "is_staff", "is_superuser")
    search_fields = ("user_name", "email", "role", "department")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Profile", {"fields": ("user_name", "role", "status", "department", "division", "reporting_manager", "user_permissions")}),
        ("Dates", {"fields": ("user_start_date", "user_end_date", "password_updated_at", "last_login")}),
        ("Permissions", {"fields": ("is_staff", "is_superuser", "is_active")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "user_name", "role", "status", "department", "password1", "password2", "is_staff", "is_superuser", "is_active"),
        }),
    )


@admin.register(UserPermissions)
class UserPermissionsAdmin(admin.ModelAdmin):
    list_display = ("id", "role", "created_at")
    search_fields = ("role",)


@admin.register(ResetTokens)
class ResetTokensAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "resetToken", "created_at")


@admin.register(UserPasswordHistory)
class UserPasswordHistoryAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at")


@admin.register(UserAuditHistory)
class UserAuditHistoryAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "api_url", "api_method", "response_status_code", "created_datetime")
    list_filter = ("api_method", "response_status_code")


@admin.register(UserSessionManagement)
class UserSessionManagementAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "isLoggedIn", "logged_in_time")


@admin.register(CoachCoachee)
class CoachCoacheeAdmin(admin.ModelAdmin):
    list_display = ("id", "coach", "coachee", "created_at")
    list_filter = ("created_at",)
    search_fields = ("coach__user_name", "coach__email", "coachee__user_name", "coachee__email")
    autocomplete_fields = ("coach", "coachee")
