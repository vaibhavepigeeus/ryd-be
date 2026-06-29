from rest_framework import serializers

from .models import CommonAudit, Documents, EmailDocs, Entity


class DocumentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Documents
        fields = "__all__"


class EntitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Entity
        fields = "__all__"


class CommonAuditSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommonAudit
        fields = "__all__"


class EmailDocsSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailDocs
        fields = "__all__"
