from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.response import Response

from documents.models import CommonAudit
from documents.serializers import CommonAuditSerializer
from users.models import UserAuditHistory


class UserAuditHistorySerializer:
    """Inline serializer to avoid circular imports in users app."""

    @staticmethod
    def serialize(qs):
        return [
            {
                "id": row.id,
                "user_id": row.user_id,
                "ip": row.ip,
                "api_url": row.api_url,
                "api_method": row.api_method,
                "response_status_code": row.response_status_code,
                "payload": row.payload,
                "response": row.response,
                "created_datetime": row.created_datetime,
            }
            for row in qs
        ]


class CommonAuditListView(generics.ListAPIView):
    queryset = CommonAudit.objects.all().order_by("-created_at")
    serializer_class = CommonAuditSerializer


@api_view(["GET"])
def user_audit_history(request):
    user_id = request.query_params.get("user_id")
    qs = UserAuditHistory.objects.all().order_by("-created_datetime")
    if user_id:
        qs = qs.filter(user_id=user_id)
    skip = int(request.query_params.get("skip", 0))
    page_size = int(request.query_params.get("pageSize", 50))
    data = UserAuditHistorySerializer.serialize(qs[skip : skip + page_size])
    return Response({"count": qs.count(), "data": data})


@api_view(["GET"])
def workflow_audit_history(request):
    from workflow.models import WorkflowAudit

    instance_id = request.query_params.get("workflow_instance_id")
    qs = WorkflowAudit.objects.all().order_by("-created_at")
    if instance_id:
        qs = qs.filter(workflow_instance_id=instance_id)
    skip = int(request.query_params.get("skip", 0))
    page_size = int(request.query_params.get("pageSize", 50))
    data = [
        {
            "id": row.id,
            "workflow_instance_id": row.workflow_instance_id,
            "audit_data": row.audit_data,
            "created_at": row.created_at,
        }
        for row in qs[skip : skip + page_size]
    ]
    return Response({"count": qs.count(), "data": data})
