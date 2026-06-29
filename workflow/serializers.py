from rest_framework import serializers

from documents.models import EmailDocs
from users.serializers import MinimalUserSerializer
from .models import (
    EmailWorkFlow,
    Notification,
    WorkFlow,
    WorkflowInstance,
    WorkStep,
)


class WorkStepCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkStep
        fields = "__all__"


class WorkStepSerializer(serializers.ModelSerializer):
    user = MinimalUserSerializer(many=True, read_only=True)

    class Meta:
        model = WorkStep
        fields = "__all__"
        depth = 2


class WorkFlowCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkFlow
        fields = "__all__"


class WorkFlowSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkFlow
        fields = "__all__"
        depth = 3


class WorkflowInstanceSerializer(serializers.ModelSerializer):
    subject_line = serializers.SerializerMethodField()

    def get_subject_line(self, obj):
        if not obj.bank_txn_id or not str(obj.bank_txn_id).isdigit():
            return None
        try:
            email_doc = EmailDocs.objects.get(id=obj.bank_txn_id)
            return email_doc.subject
        except EmailDocs.DoesNotExist:
            return None

    class Meta:
        model = WorkflowInstance
        fields = "__all__"


class EmailWorkFlowSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailWorkFlow
        fields = "__all__"


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = "__all__"
