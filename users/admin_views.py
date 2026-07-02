from django.conf import settings
from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from forms.models import FormPage
from forms.serializers import FormPageSummarySerializer

from .constants import UserRole
from .models import CoachCoachee, Users
from .serializers import (
    AdminCoachListSerializer,
    AdminCreateCoachSerializer,
    AdminCreateCoacheeSerializer,
    CoachCoacheeListSerializer,
)
from .views import _get_user_from_request


def _is_admin(user):
    return (
        user.role == UserRole.ADMIN
        or user.is_staff
        or user.is_superuser
    )


def _require_admin(request):
    user = _get_user_from_request(request)
    if not user:
        return None, Response(
            {"message": "Authentication required.", "success": False},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    if not _is_admin(user):
        return None, Response(
            {"message": "Admin access required.", "success": False},
            status=status.HTTP_403_FORBIDDEN,
        )
    return user, None


def _validation_error_response(serializer):
    first_error = next(iter(serializer.errors.values()), ["Invalid data"])[0]
    return Response(
        {
            "message": first_error,
            "errors": serializer.errors,
            "success": False,
        },
        status=status.HTTP_400_BAD_REQUEST,
    )


def _serialize_coach(coach, total_forms):
    return AdminCoachListSerializer(
        coach,
        context={"total_forms": total_forms},
    ).data


def _get_coach_or_404(coach_id):
    return get_object_or_404(Users, id=coach_id, role=UserRole.COACH)


def _creation_message(entity_label, email_sent, email_error=None):
    if email_sent:
        return f"{entity_label} created. A login password has been sent to their email."
    detail = email_error or "SMTP delivery failed."
    if settings.DEBUG or settings.ENVIRONMENT == "DEVELOPMENT":
        detail += " Check the backend terminal for the generated password."
    return f"{entity_label} created, but the welcome email could not be sent. {detail}"


@api_view(["GET"])
def admin_dashboard_stats(request):
    _, denied = _require_admin(request)
    if denied:
        return denied

    return Response(
        {
            "total_coaches": Users.objects.filter(role=UserRole.COACH).count(),
            "active_coaches": Users.objects.filter(
                role=UserRole.COACH, status="Active"
            ).count(),
            "total_coachees": Users.objects.filter(role=UserRole.COACHEE).count(),
            "total_forms": FormPage.objects.count(),
        }
    )


@api_view(["GET", "POST"])
def admin_coaches(request):
    _, denied = _require_admin(request)
    if denied:
        return denied

    if request.method == "POST":
        serializer = AdminCreateCoachSerializer(data=request.data)
        if not serializer.is_valid():
            return _validation_error_response(serializer)

        coach = serializer.save()
        total_forms = FormPage.objects.count()
        email_sent = getattr(serializer, "email_sent", False)
        return Response(
            {
                "message": _creation_message(
                    "Coach",
                    email_sent,
                    getattr(serializer, "email_error", None),
                ),
                "success": True,
                "email_sent": email_sent,
                "coach": _serialize_coach(coach, total_forms),
            },
            status=status.HTTP_201_CREATED,
        )

    coaches = (
        Users.objects.filter(role=UserRole.COACH)
        .annotate(coachee_count=Count("coachee_links", distinct=True))
        .order_by("user_name")
    )
    total_forms = FormPage.objects.count()
    serializer = AdminCoachListSerializer(
        coaches,
        many=True,
        context={"total_forms": total_forms},
    )
    return Response({"coaches": serializer.data, "count": coaches.count()})


@api_view(["POST"])
def admin_create_coachee(request):
    _, denied = _require_admin(request)
    if denied:
        return denied

    serializer = AdminCreateCoacheeSerializer(data=request.data)
    if not serializer.is_valid():
        return _validation_error_response(serializer)

    coachee = serializer.save()
    email_sent = getattr(serializer, "email_sent", False)
    return Response(
        {
            "message": _creation_message(
                "Coachee",
                email_sent,
                getattr(serializer, "email_error", None),
            ),
            "success": True,
            "email_sent": email_sent,
            "coachee": {
                "id": coachee.id,
                "user_name": coachee.user_name,
                "email": coachee.get_decrypted_email(),
                "status": coachee.status,
                "coach_id": coachee.reporting_manager_id,
            },
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
def admin_coach_forms(request, coach_id):
    _, denied = _require_admin(request)
    if denied:
        return denied

    coach = _get_coach_or_404(coach_id)
    total_forms = FormPage.objects.count()
    pages = (
        FormPage.objects.annotate(submission_count=Count("submissions"))
        .order_by("-updated_at")
    )
    return Response(
        {
            "coach": _serialize_coach(coach, total_forms),
            "forms": FormPageSummarySerializer(pages, many=True).data,
        }
    )


@api_view(["GET"])
def admin_coach_coachees(request, coach_id):
    _, denied = _require_admin(request)
    if denied:
        return denied

    coach = _get_coach_or_404(coach_id)
    total_forms = FormPage.objects.count()
    links = (
        CoachCoachee.objects.filter(coach=coach)
        .select_related("coachee")
        .order_by("-created_at")
    )
    return Response(
        {
            "coach": _serialize_coach(coach, total_forms),
            "coachees": CoachCoacheeListSerializer(links, many=True).data,
        }
    )
