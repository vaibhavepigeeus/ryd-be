from django.db import models

from users.models import Users


class WorkStep(models.Model):
    step_name = models.CharField(max_length=200)
    comments = models.TextField(blank=True, null=True)
    user = models.ManyToManyField(Users, blank=True, related_name="workstep_users")
    ctime = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    uptime = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=100, blank=True, null=True)
    step_seq_no = models.IntegerField(null=True)
    step_process = models.CharField(null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        ordering = ("step_seq_no",)


class WorkFlow(models.Model):
    workflow_name = models.CharField(max_length=200)
    workflow_step = models.ManyToManyField(WorkStep, blank=True, related_name="worksteps")
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)


class EmailWorkFlow(models.Model):
    business_function = models.CharField(max_length=200, null=True, blank=True)
    workflow = models.ForeignKey(WorkFlow, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(blank=True, null=True)


class WorkflowInstance(models.Model):
    """Generic workflow instance (originally WorkflowBankTransactions)."""
    workflow = models.ForeignKey(WorkFlow, on_delete=models.CASCADE, null=True, blank=True)
    workflow_json_data = models.JSONField(blank=True, null=True)
    ticket_no = models.CharField(max_length=100, blank=True, null=True)
    changefields = models.JSONField(blank=True, null=True)
    current_step = models.CharField(max_length=100, blank=True, null=True)
    bank_txn_id = models.CharField(max_length=100, null=True, blank=True)
    workflow_status = models.CharField(max_length=100, null=True, blank=True)
    file = models.CharField(max_length=255, null=True, blank=True)
    initiated_by = models.IntegerField(null=True, blank=True)
    current_step_userids = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)


class NotificationMessage(models.Model):
    MESSAGE_TYPES = (
        ("success", "Success"),
        ("error", "Error"),
        ("warning", "Warning"),
        ("info", "Info"),
    )
    CONTEXTS = (
        ("workflow_assignment", "Workflow Assignment"),
        ("email_workflow", "Email Workflow Assignment"),
        ("generic", "Generic"),
    )
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default="info")
    context = models.CharField(max_length=50, choices=CONTEXTS, default="generic")
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)


class Notification(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=255)
    message = models.TextField()
    action = models.CharField(max_length=500, blank=True, null=True)
    message_template = models.ForeignKey(
        NotificationMessage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
    )
    is_read = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class WorkflowAudit(models.Model):
    workflow_instance = models.ForeignKey(WorkflowInstance, on_delete=models.CASCADE, null=True)
    audit_data = models.JSONField(null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
