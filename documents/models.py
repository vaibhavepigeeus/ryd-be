import datetime

import boto3
from decouple import config
from django.db import models


class Documents(models.Model):
    document_name = models.CharField(max_length=255)
    document_date = models.DateField()
    upload_date = models.DateTimeField(auto_now_add=True)
    document_file = models.FileField(upload_to="documents/media/", blank=True, null=True)
    document_type = models.CharField(max_length=200)
    document_details = models.CharField(max_length=100, blank=True, null=True)
    archieve_by = models.CharField(max_length=100, null=True)
    archieve_datetime = models.DateTimeField(default=datetime.datetime.now)
    document_url = models.TextField(null=True)
    archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def delete(self, *args, **kwargs):
        if self.document_file:
            s3_client = boto3.client("s3")
            s3_bucket = config("AWS_STORAGE_BUCKET_NAME")
            s3_key = self.document_file.name
            s3_client.delete_object(Bucket=s3_bucket, Key=s3_key)
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.document_name or str(self.id)


class Entity(models.Model):
    entity_divisions = models.CharField(max_length=100)
    created_by = models.CharField(max_length=100, null=True, blank=True)
    addedDateAndTime = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_by = models.CharField(max_length=100, null=True, blank=True)
    updatedDateAndTime = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_fields = models.TextField(null=True, blank=True)
    entity_name = models.CharField(max_length=100, null=True)

    def __str__(self):
        return self.entity_divisions


class CommonAudit(models.Model):
    table_name = models.CharField(max_length=100, null=True, blank=True)
    record_id = models.IntegerField(null=True, blank=True)
    field_name = models.CharField(max_length=100, null=True, blank=True)
    old_value = models.JSONField(null=True)
    new_value = models.JSONField(null=True)
    changed_by = models.ForeignKey(
        "users.Users",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_user",
    )
    event_type = models.CharField(max_length=100, null=True, blank=True)
    previous_time = models.DateTimeField(null=True, blank=True)
    current_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)


class EmailDocs(models.Model):
    workflow = models.ForeignKey(
        "workflow.EmailWorkFlow",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="email_doc",
    )
    from_email = models.CharField(max_length=100, null=True, blank=True)
    to_email = models.CharField(max_length=100, null=True, blank=True)
    cc = models.CharField(max_length=100, null=True, blank=True)
    subject = models.CharField(max_length=200, null=True, blank=True)
    body = models.TextField(null=True, blank=True)
    attachments = models.CharField(max_length=255, null=True, blank=True)
    date = models.DateTimeField(null=True, blank=True)
    time = models.TimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
