from django.db import models
from users.models import *

class FileManagement(models.Model):
    file_name = models.CharField(max_length=255, null=True)
    file_path = models.CharField(max_length=1024, null=True)
    file_type = models.CharField(max_length=100, null=True)
    file_size = models.BigIntegerField(null=True)
    file_info = models.JSONField(null=True, blank=True)
    module_name = models.CharField(max_length=100, null=True)
    archived = models.BooleanField(default=False)
    created_by = models.ForeignKey(Users, null=True, on_delete=models.SET_NULL, blank=True, related_name='file_created_by')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.file_name