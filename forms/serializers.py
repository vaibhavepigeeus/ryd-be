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
    page_name = serializers.CharField(source="page.page_name", read_only=True)
    submitted_by = serializers.SerializerMethodField()

    class Meta:
        model = FormPageSubmission
        fields = ("id", "page", "page_name", "response_data", "submitted_at", "submitted_by")
        read_only_fields = ("submitted_at",)

    def get_submitted_by(self, obj):
        user = obj.submitted_by
        if not user:
            return None
        return {
            "id": user.id,
            "user_name": user.user_name,
            "email": user.get_decrypted_email(),
        }


class FormPageSummarySerializer(serializers.ModelSerializer):
    submission_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = FormPage
        fields = (
            "id",
            "page_name",
            "is_published",
            "publish_slug",
            "updated_at",
            "created_at",
            "submission_count",
        )


class FormPageSubmissionDetailSerializer(serializers.ModelSerializer):
    page = FormPageSerializer(read_only=True)
    submitted_by = serializers.SerializerMethodField()

    class Meta:
        model = FormPageSubmission
        fields = ("id", "page", "response_data", "submitted_at", "submitted_by")

    def get_submitted_by(self, obj):
        user = obj.submitted_by
        if not user:
            return None
        return {
            "id": user.id,
            "user_name": user.user_name,
            "email": user.get_decrypted_email(),
        }
