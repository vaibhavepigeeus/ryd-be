from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("workstep", views.WorkStepViewSet, basename="workstep")
router.register("workflow", views.WorkFlowViewSet, basename="workflow")
router.register("workflow_bank_transactions", views.WorkflowInstanceViewSet, basename="workflow_bank_transactions")

urlpatterns = [
    path("", include(router.urls)),
    path("workflow_assign_transaction/", views.setWorkflowWithTransaction, name="workflow_assign_transaction"),
    path("get_workflow_list_id/", views.getWorkflowList, name="get_workflow_list_id"),
    path("workstep_user_update/<str:pk>/", views.WorkstepUserUpdateAPIView.as_view(), name="workstep_user_update"),
    path("workflow_dashboard/summary/", views.get_workflow_dashboard_summary, name="workflow_dashboard_summary"),
    path("workflow_dashboard/aging_analysis/", views.get_aging_analysis, name="workflow_dashboard_aging_analysis"),
    path("workflow_dashboard/workflow_type_breakdown/", views.get_workflow_type_breakdown, name="workflow_dashboard_workflow_type_breakdown"),
    path("workflow_dashboard/overview/", views.get_workflow_overview, name="workflow_dashboard_overview"),
    path("workflow_dashboard/team_activity/", views.get_team_activity, name="workflow_dashboard_team_activity"),
    path("workflow_dashboard/pending_details/", views.get_pending_workflow_details, name="workflow_dashboard_pending_details"),
    path("fetch_unread_notifications/", views.FetchUnreadNotification.as_view(), name="fetch_unread_notifications"),
    path("notifications/<int:pk>/mark_read/", views.MarkNotificationRead.as_view(), name="mark_as_read"),
]
