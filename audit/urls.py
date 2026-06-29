from django.urls import path

from . import views

urlpatterns = [
    path("common/", views.CommonAuditListView.as_view(), name="common_audit_list"),
    path("user-history/", views.user_audit_history, name="user_audit_history"),
    path("workflow-history/", views.workflow_audit_history, name="workflow_audit_history"),
]
