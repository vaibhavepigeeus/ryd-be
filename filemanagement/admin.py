from django.contrib import admin

from .models import FileManagement


@admin.register(FileManagement)
class FileManagementAdmin(admin.ModelAdmin):
    list_display = ("id", "file_name", "file_type", "module_name", "archived", "created_at")
    list_filter = ("file_type", "module_name", "archived")
    search_fields = ("file_name",)
