from django.contrib import admin

from .models import CommonAudit, Documents, EmailDocs, Entity


@admin.register(Documents)
class DocumentsAdmin(admin.ModelAdmin):
    list_display = ("id", "document_name", "document_type", "document_date", "archived")
    list_filter = ("document_type", "archived")
    search_fields = ("document_name",)


@admin.register(Entity)
class EntityAdmin(admin.ModelAdmin):
    list_display = ("id", "entity_name", "entity_divisions")
    search_fields = ("entity_name", "entity_divisions")


@admin.register(CommonAudit)
class CommonAuditAdmin(admin.ModelAdmin):
    list_display = ("id", "table_name", "record_id", "field_name", "event_type", "created_at")
    list_filter = ("table_name", "event_type")


@admin.register(EmailDocs)
class EmailDocsAdmin(admin.ModelAdmin):
    list_display = ("id", "from_email", "to_email", "subject", "date")
    search_fields = ("from_email", "to_email", "subject")
