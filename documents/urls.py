from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("document_upload", views.DocumentsViewSet, basename="document_upload")
router.register("entity", views.EntityViewSet, basename="entity")

urlpatterns = [
    path("", include(router.urls)),
    path("read_email_list/", views.read_email_list, name="read_email_list"),
    path("send_reply_email/", views.send_reply_email, name="send_reply_email"),
    path("get_all_entity_divisions/", views.get_all_entity_divisions, name="get_all_entity_divisions"),
]
