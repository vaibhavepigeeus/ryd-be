from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import FormForm, FormQuestion, FormSubsection, FormType
from .questionnaire import build_questionnaire_detail
from .serializers import (
    FormFormSerializer,
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
    queryset = FormQuestion.objects.all()
    serializer_class = FormQuestionSerializer
    filterset_fields = ["form_type", "version", "association_subsection"]


class FormQuestionDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = FormQuestion.objects.all()
    serializer_class = FormQuestionSerializer


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
