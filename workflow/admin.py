from django.contrib import admin

from .models import (
    EmailWorkFlow,
    Notification,
    NotificationMessage,
    WorkFlow,
    WorkflowAudit,
    WorkflowInstance,
    WorkStep,
)


@admin.register(WorkStep)
class WorkStepAdmin(admin.ModelAdmin):
    list_display = ("id", "step_name", "step_seq_no", "status")
    filter_horizontal = ("user",)


@admin.register(WorkFlow)
class WorkFlowAdmin(admin.ModelAdmin):
    list_display = ("id", "workflow_name", "created_at")
    filter_horizontal = ("workflow_step",)


@admin.register(EmailWorkFlow)
class EmailWorkFlowAdmin(admin.ModelAdmin):
    list_display = ("id", "business_function", "workflow")


@admin.register(WorkflowInstance)
class WorkflowInstanceAdmin(admin.ModelAdmin):
    list_display = ("id", "ticket_no", "workflow_status", "current_step", "created_at")
    list_filter = ("workflow_status",)


@admin.register(NotificationMessage)
class NotificationMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "message_type", "context", "created_at")
    list_filter = ("message_type", "context")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "title", "is_read", "is_sent", "created_at")
    list_filter = ("is_read", "is_sent")


@admin.register(WorkflowAudit)
class WorkflowAuditAdmin(admin.ModelAdmin):
    list_display = ("id", "workflow_instance", "created_at")
