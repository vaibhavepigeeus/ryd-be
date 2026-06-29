import json
import logging
import os
from datetime import datetime

from decouple import config
from django.conf import settings
from django.db.models import Q
from django.http import JsonResponse
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics, status, viewsets
from rest_framework.decorators import api_view
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from filemanagement.views import reusable_file_upload
from users.models import Users
from users.utils import send_email
from .models import Notification, NotificationMessage, WorkFlow, WorkflowInstance, WorkStep, WorkflowAudit
from .notifications import create_notification
from .serializers import (
    NotificationSerializer,
    WorkFlowCreateSerializer,
    WorkFlowSerializer,
    WorkflowInstanceSerializer,
    WorkStepCreateSerializer,
    WorkStepSerializer,
)
from . import dashboard_views

logger = logging.getLogger(__name__)


def get_user(request):
    user_id = request.headers.get("user-id")
    return Users.objects.get(id=user_id)


class WorkStepViewSet(viewsets.ModelViewSet):
    queryset = WorkStep.objects.all()
    serializer_class = WorkStepSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def create(self, request, *args, **kwargs):
        serializer = WorkStepCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.user.set(request.data["user"])
        obj.step_name = request.data["step_name"]
        obj.comments = request.data["comments"]
        obj.status = request.data["status"]
        obj.save()
        return Response(WorkStepCreateSerializer(obj).data, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


class WorkFlowViewSet(viewsets.ModelViewSet):
    queryset = WorkFlow.objects.all()
    serializer_class = WorkFlowSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def create(self, request, *args, **kwargs):
        serializer = WorkFlowCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.workflow_step.set(request.data["workflow_step"])
        obj.workflow_name = request.data["workflow_name"]
        obj.save()
        return Response(WorkFlowCreateSerializer(obj).data, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


class WorkflowInstanceViewSet(viewsets.ModelViewSet):
    queryset = WorkflowInstance.objects.all()
    serializer_class = WorkflowInstanceSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    env_name = settings.ENVIRONMENT

    def workflow_specific_change_values(self, data, workflow_name):
        return data.get("changefields", {})

    def workflow_specific_change_implement(self, request, rec, reference_id, workflow_name, stepp, user=None):
        WorkflowAudit.objects.create(
            workflow_instance=None,
            audit_data={
                "workflow_name": workflow_name,
                "step_process": stepp,
                "reference_id": reference_id,
                "changefields": rec,
                "changed_by": get_user(request).pk,
                "event_type": "workflow_step_process",
            },
        )

    def createnew_new(self, request, files):
        data = request.data
        workflow_name = data["workflow_name"]
        reference_id = data["bank_txn_id"]
        comments = data["comments"]
        initiated_user_id = data["initiated_user_id"]
        user_data = Users.objects.get(id=initiated_user_id)

        initiated_data = {
            "id": user_data.id,
            "email": user_data.email,
            "user_name": user_data.user_name,
        }
        initiator_step = {
            "user": [initiated_data],
            "comments": comments,
            "status": "NEW",
            "ctime": str(datetime.now()),
            "uptime": "",
            "step_name": "initiater",
            "step_process": None,
        }

        workflow = WorkFlow.objects.get(workflow_name=workflow_name)
        workflow_data = WorkFlowSerializer(workflow).data
        db_files = []
        for uploaded_file in files:
            upload_data = {
                "module_name": data.get("module_name", "workflow"),
                "bucket_name": config("AWS_STORAGE_BUCKET_NAME", default=""),
            }
            file_result = reusable_file_upload(get_user(request), uploaded_file, upload_data, is_upload=False)
            if isinstance(file_result, Response) and file_result.status_code < 400:
                db_files.append(file_result.data["file_name"])

        instance = WorkflowInstance.objects.create(
            workflow=workflow,
            bank_txn_id=reference_id,
            file=",".join(db_files),
        )
        instance.ticket_no = f"TKT{instance.id:07d}"
        instance.save()

        workflow_users = []
        for workstep in workflow.workflow_step.all():
            workflow_users.extend(list(workstep.user.all()))
        unique_users = list(set(workflow_users))

        template, _ = NotificationMessage.objects.get_or_create(
            context="workflow_assignment",
            message_type="success",
            defaults={"message": "Workflow {workflow_name} initiated for {bank_txn_id}"},
        )
        message_text = template.message.format(workflow_name=workflow_name, bank_txn_id=reference_id)
        for user in unique_users:
            create_notification(
                user=user,
                title="Workflow Initiated",
                message=message_text,
                action=f"/workflow/instances?bank_txn_id={instance.bank_txn_id}",
                templateID=template,
            )

        steps = [initiator_step]
        current_step = None
        current_step_userids = []
        for index, step in enumerate(workflow_data["workflow_step"]):
            if index == 0:
                current_step = step["step_name"]
                current_step_userids = [u["id"] for u in step.get("user", [])]
            steps.append({
                "id": step["id"],
                "ctime": "",
                "status": step["status"],
                "uptime": "",
                "comments": step["comments"],
                "step_name": step["step_name"],
                "step_process": step.get("step_process"),
                "user": step.get("user", []),
            })

        instance.changefields = self.workflow_specific_change_values(data, workflow_name)
        instance.workflow_json_data = {
            "id": workflow_data["id"],
            "workflow_name": workflow_name,
            "workflow_step": steps,
        }
        instance.current_step = current_step
        instance.current_step_userids = current_step_userids
        instance.initiated_by = initiated_user_id
        instance.workflow_status = "In Process"
        instance.save()

        try:
            reviewer_emails = [Users.objects.get(id=uid).get_decrypted_email() for uid in current_step_userids]
            send_email(
                sender_email=settings.EMAIL_HOST_USER,
                recipient_email=reviewer_emails + [user_data.get_decrypted_email()],
                subject="New Worklist Item Assigned to You",
                body=settings.WORK_FLOW_INITIATE_BODY.format(
                    imagepath="",
                    reviewer_approver="Reviewer",
                    initiator=user_data.user_name,
                    transaction_id=reference_id,
                    env_name=self.env_name,
                ),
            )
        except Exception as e:
            logger.error("Workflow initiate email failed: %s", e)

        return WorkflowInstanceSerializer(instance)

    def create(self, request, *args, **kwargs):
        files = request.FILES.getlist("files")
        serializer = self.createnew_new(request, files)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def partial_update_new(self, request):
        obj = self.get_object()
        reference_id = request.data["bank_txn_id"]
        step_name = request.data["step_name"]
        step_status = request.data["status"]
        comments = request.data["comments"]
        user_id = request.data["user_id"]
        user_data = Users.objects.get(id=user_id)

        actor = {
            "id": user_data.id,
            "email": user_data.get_decrypted_email(),
            "user_name": user_data.user_name,
        }

        workflow_json = obj.workflow_json_data
        workflow_name = workflow_json["workflow_name"]
        steps = workflow_json["workflow_step"]
        length = len(steps) - 1
        step_name_found = 0
        current_step_userids = []
        past_step_email_recs = []

        for index, step in enumerate(steps):
            if step_name_found == 1 and step_status.lower() != "reject":
                obj.current_step = step["step_name"]
                obj.workflow_status = "in process"
                current_step_userids = [u["id"] for u in step.get("user", [])]
                step_name_found = 0

            if step["step_name"] == step_name:
                step["ctime"] = str(datetime.now())
                step["status"] = step_status
                step["comments"] = comments
                step["user"] = [actor]
                past_step_email_recs = [actor]
                step_name_found = 1

                if step.get("step_process") and step_status.lower() == "approve":
                    self.workflow_specific_change_implement(
                        request,
                        obj.changefields,
                        reference_id,
                        workflow_name,
                        step["step_process"],
                        user=actor,
                    )
                    if index == length:
                        obj.workflow_status = "completed"
                        obj.current_step = None
                elif step_status.lower() == "reject":
                    obj.current_step = None
                    obj.workflow_status = "rejected"

        obj.bank_txn_id = reference_id
        obj.workflow_json_data = {
            "id": workflow_json["id"],
            "workflow_name": workflow_name,
            "workflow_step": steps,
        }
        obj.current_step_userids = current_step_userids
        obj.save()

        WorkflowAudit.objects.create(
            workflow_instance=obj,
            audit_data={
                "step_name": step_name,
                "status": step_status,
                "comments": comments,
                "changed_by": user_data.pk,
                "event_type": "workflow_status_change",
            },
        )

        try:
            reviewer_emails = [Users.objects.get(id=uid).get_decrypted_email() for uid in current_step_userids]
            past_emails = [u["email"] for u in past_step_email_recs]
            send_email(
                sender_email=settings.EMAIL_HOST_USER,
                recipient_email=reviewer_emails + past_emails,
                subject=f"Status Update for {reference_id}",
                body=settings.WORK_FLOW_CHANGE_STATUS_REVIEWER_BODY.format(
                    imagepath="",
                    reviewer_approver=user_data.user_name,
                    initiator=user_data.user_name,
                    transaction_id=reference_id,
                    env_name=self.env_name,
                ),
            )
        except Exception as e:
            logger.error("Workflow status email failed: %s", e)

        return WorkflowInstanceSerializer(obj)

    def partial_update(self, request, *args, **kwargs):
        serializer = self.partial_update_new(request)
        return Response(serializer.data)


@api_view(["POST"])
def setWorkflowWithTransaction(request):
    json_data = json.loads(request.body.decode("utf-8"))
    workflow_id = json_data["workflow_id"]
    reference_id = json_data["bank_txn_id"]
    try:
        workflow = WorkFlow.objects.get(id=workflow_id)
    except WorkFlow.DoesNotExist:
        return Response({"msg": "Workflow not found"}, status=400)

    instance, _ = WorkflowInstance.objects.get_or_create(
        bank_txn_id=reference_id,
        defaults={"workflow": workflow, "workflow_status": "Assigned"},
    )
    instance.workflow = workflow
    instance.save()
    return Response({"data": WorkflowInstanceSerializer(instance).data}, status=200)


@csrf_exempt
def getWorkflowList(request):
    if request.method != "GET":
        return JsonResponse({"Error": "Method not allowed"}, status=405)

    user_id = request.GET.get("user_id")
    if not user_id:
        return Response({"Error": "Please give a user id"}, status=status.HTTP_400_BAD_REQUEST)

    user_id = int(user_id)
    page_number = int(request.GET.get("skip", 0))
    rows_per_page = int(request.GET.get("pageSize", 20))
    skip = page_number * rows_per_page

    try:
        user_data = Users.objects.get(id=user_id)
    except Users.DoesNotExist:
        return Response({"Error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    initiated_data = {
        "user": [{"id": user_data.id, "email": user_data.email, "user_name": user_data.user_name}]
    }

    filter_conditions = Q()
    workflow_name = request.GET.get("workflowName")
    from_date = request.GET.get("fromDateReceived")
    to_date = request.GET.get("toDateReceived")

    if workflow_name:
        filter_conditions &= Q(workflow__workflow_name__in=workflow_name.split(","))
    if from_date and to_date:
        from_dt = parse_datetime(from_date)
        to_dt = parse_datetime(to_date)
        if from_dt and to_dt:
            to_dt = to_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
            filter_conditions &= Q(created_at__range=(from_dt, to_dt))

    filter_conditions &= Q(workflow_json_data__contains={"workflow_step": [initiated_data]})
    queryset = WorkflowInstance.objects.filter(filter_conditions).order_by("-id")

    matched = []
    for item in queryset:
        current_step = item.current_step
        for step in item.workflow_json_data.get("workflow_step", []):
            for user in step.get("user", []):
                if user["id"] == user_id and step["step_name"] in (current_step, "initiater"):
                    matched.append(item)
                    break

    serializer = WorkflowInstanceSerializer(matched[skip : skip + rows_per_page], many=True)
    return JsonResponse({"count": len(matched), "data": serializer.data}, safe=False)


class WorkstepUserUpdateAPIView(APIView):
    def patch(self, request, pk):
        user_id = request.data.get("user_id")
        if not pk or not user_id:
            return Response({"Error": "Insufficient data"}, status=status.HTTP_400_BAD_REQUEST)
        workstep = WorkStep.objects.get(id=pk)
        workstep.user.add(user_id)
        return Response({"message": "WorkStep user updated successfully"})

    def delete(self, request, pk):
        user_id = request.query_params.get("user_id")
        if not pk or not user_id:
            return Response({"Error": "Insufficient data"}, status=status.HTTP_400_BAD_REQUEST)
        workstep = WorkStep.objects.get(id=pk)
        workstep.user.remove(Users.objects.get(id=user_id))
        return Response({"message": "WorkStep user removed successfully"})


class FetchUnreadNotification(generics.ListAPIView):
    serializer_class = NotificationSerializer
    pagination_class = None

    def get_queryset(self):
        user = get_user(self.request)
        return Notification.objects.filter(user=user.id, is_read=False).order_by("-created_at")


class MarkNotificationRead(APIView):
    def patch(self, request, pk):
        user = get_user(request)
        try:
            notif = Notification.objects.get(id=pk, user=user.id)
            notif.is_read = True
            notif.save()
            return Response({"success": True})
        except Notification.DoesNotExist:
            return Response({"error": "Notification not found"}, status=status.HTTP_404_NOT_FOUND)


# Re-export dashboard views
get_workflow_dashboard_summary = dashboard_views.get_workflow_dashboard_summary
get_aging_analysis = dashboard_views.get_aging_analysis
get_workflow_type_breakdown = dashboard_views.get_workflow_type_breakdown
get_workflow_overview = dashboard_views.get_workflow_overview
get_team_activity = dashboard_views.get_team_activity
get_pending_workflow_details = dashboard_views.get_pending_workflow_details
