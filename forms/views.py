from django.conf import settings
from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from users.constants import UserRole

from .auth_helpers import get_user_from_request

from .models import FormForm, FormPage, FormPageSubmission, FormQuestion, FormSubsection, FormType
from .questionnaire import build_questionnaire_detail
from .question_versioning import create_question_version
from .serializers import (
    FormFormSerializer,
    FormPageSerializer,
    FormPageSubmissionDetailSerializer,
    FormPageSubmissionSerializer,
    FormPageSummarySerializer,
    FormQuestionSerializer,
    FormSubsectionSerializer,
    FormTypeSerializer,
)


class FormTypeListCreateView(generics.ListCreateAPIView):
    queryset = FormType.objects.all()
    serializer_class = FormTypeSerializer


class FormTypeDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = FormType.objects.all()
    serializer_class = FormTypeSerializer


class FormSubsectionListCreateView(generics.ListCreateAPIView):
    queryset = FormSubsection.objects.all()
    serializer_class = FormSubsectionSerializer
    filterset_fields = ["form_type", "version"]


class FormSubsectionDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = FormSubsection.objects.all()
    serializer_class = FormSubsectionSerializer


class FormQuestionListCreateView(generics.ListCreateAPIView):
    queryset = FormQuestion.objects.all().order_by("sequence_no", "id")
    serializer_class = FormQuestionSerializer
    filterset_fields = ["form_type", "version", "association_subsection"]


class FormQuestionDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = FormQuestion.objects.all()
    serializer_class = FormQuestionSerializer


class FormQuestionNewVersionView(APIView):
    """Create a new form_questions row (version + 1, new question_id) from an existing question."""

    def post(self, request, pk):
        source = get_object_or_404(FormQuestion, pk=pk)
        question_text = request.data.get("question")

        if question_text is None or str(question_text).strip() == "":
            return Response(
                {"detail": "question text is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        new_question = create_question_version(source, str(question_text).strip())
        return Response(
            FormQuestionSerializer(new_question).data,
            status=status.HTTP_201_CREATED,
        )


class FormFormListCreateView(generics.ListCreateAPIView):
    queryset = FormForm.objects.all()
    serializer_class = FormFormSerializer
    filterset_fields = ["form_type", "form_id", "form_version"]


class FormFormDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = FormForm.objects.all()
    serializer_class = FormFormSerializer


class FormTypeFullView(APIView):
    """Returns a nested questionnaire payload for the form builder."""

    def get(self, request, pk):
        form_type = get_object_or_404(FormType, pk=pk)
        return Response(build_questionnaire_detail(form_type))


class FormPageListCreateView(generics.ListCreateAPIView):
    queryset = FormPage.objects.all()
    serializer_class = FormPageSerializer


class FormPageDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = FormPage.objects.all()
    serializer_class = FormPageSerializer


class FormPagePublishView(APIView):
    def post(self, request, pk):
        page = get_object_or_404(FormPage, pk=pk)
        page.publish()
        return Response(
            {
                "id": page.id,
                "publish_slug": page.publish_slug,
                "published_at": page.published_at,
                "public_url": f"/p/{page.publish_slug}",
            }
        )


class PublishedPageView(APIView):
    """Public endpoint — returns a published page for respondents."""

    def get(self, request, slug):
        page = get_object_or_404(FormPage, publish_slug=slug, is_published=True)
        return Response(FormPageSerializer(page).data)


class PublishedPageSubmitView(APIView):
    """Public endpoint — saves a respondent's form answers."""

    def post(self, request, slug):
        page = get_object_or_404(FormPage, publish_slug=slug, is_published=True)
        user = get_user_from_request(request)
        submission = FormPageSubmission.objects.create(
            page=page,
            response_data=request.data,
            submitted_by=user if user else None,
        )
        return Response(
            FormPageSubmissionSerializer(submission).data,
            status=status.HTTP_201_CREATED,
        )


class FormPageWithResponsesListView(generics.ListAPIView):
    """List saved builder pages with submission counts."""

    serializer_class = FormPageSummarySerializer

    def get_queryset(self):
        return (
            FormPage.objects.annotate(submission_count=Count("submissions"))
            .order_by("-updated_at")
        )


class FormPageSubmissionListView(generics.ListAPIView):
    """List submissions for a saved builder page."""

    serializer_class = FormPageSubmissionSerializer

    def get_queryset(self):
        page = get_object_or_404(FormPage, pk=self.kwargs["page_id"])
        return page.submissions.all()


class MySubmissionsListView(APIView):
    """List form submissions for the authenticated coachee."""

    def get(self, request):
        user = get_user_from_request(request)
        if not user:
            return Response(
                {"detail": "Authentication required."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if user.role != UserRole.COACHEE:
            return Response(
                {"detail": "Only coachees can view their submissions."},
                status=status.HTTP_403_FORBIDDEN,
            )

        submissions = (
            FormPageSubmission.objects.filter(submitted_by=user)
            .select_related("page")
            .order_by("-submitted_at")
        )
        return Response(FormPageSubmissionSerializer(submissions, many=True).data)


class FormPageSubmissionDetailView(APIView):
    """Return a single submission with its page layout for read-only viewing."""

    def get(self, request, submission_id):
        submission = get_object_or_404(
            FormPageSubmission.objects.select_related("page"),
            pk=submission_id,
        )
        user = get_user_from_request(request)
        if user and user.role == UserRole.COACHEE:
            if submission.submitted_by_id != user.id:
                return Response(
                    {"detail": "Submission not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )
        return Response(FormPageSubmissionDetailSerializer(submission).data)
