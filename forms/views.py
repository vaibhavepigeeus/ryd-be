from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import FormForm, FormPage, FormPageSubmission, FormQuestion, FormSubsection, FormType
from .questionnaire import build_questionnaire_detail
from .question_versioning import create_question_version
from .serializers import (
    FormFormSerializer,
    FormPageSerializer,
    FormPageSubmissionSerializer,
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
        submission = FormPageSubmission.objects.create(
            page=page,
            response_data=request.data,
        )
        return Response(
            FormPageSubmissionSerializer(submission).data,
            status=status.HTTP_201_CREATED,
        )
