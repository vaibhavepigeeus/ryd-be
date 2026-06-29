from rest_framework import serializers

from .models import FormForm, FormPage, FormPageSubmission, FormQuestion, FormSubsection, FormType


class FormTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormType
        fields = "__all__"
        read_only_fields = ("form_id", "created_at", "updated_at")


class FormSubsectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormSubsection
        fields = "__all__"


class FormQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormQuestion
        fields = "__all__"


class FormFormSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormForm
        fields = "__all__"
        read_only_fields = ("form_id", "form_version")


class FormPageSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormPage
        fields = "__all__"
        read_only_fields = ("created_at", "updated_at", "publish_slug", "published_at", "is_published")


class FormPageSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormPageSubmission
        fields = "__all__"
        read_only_fields = ("submitted_at",)
