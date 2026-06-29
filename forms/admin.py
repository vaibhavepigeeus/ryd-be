from django.contrib import admin

from .models import FormForm, FormPage, FormPageSubmission, FormQuestion, FormSubsection, FormType


@admin.register(FormType)
class FormTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "form_id", "form_version", "frequency", "created_at")
    list_filter = ("frequency",)
    search_fields = ("form_name",)


@admin.register(FormSubsection)
class FormSubsectionAdmin(admin.ModelAdmin):
    list_display = ("id", "form_type", "version")
    list_filter = ("version",)


@admin.register(FormQuestion)
class FormQuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "question_id", "form_type", "version", "sequence_no", "answer_type")
    list_filter = ("answer_type", "version")
    ordering = ("sequence_no", "id")


@admin.register(FormForm)
class FormFormAdmin(admin.ModelAdmin):
    list_display = ("id", "form_id", "form_version", "sequence_no", "user_entered")
    list_filter = ("form_version",)


@admin.register(FormPage)
class FormPageAdmin(admin.ModelAdmin):
    list_display = ("id", "page_name", "is_published", "publish_slug", "created_at", "updated_at")
    search_fields = ("page_name", "publish_slug")
    list_filter = ("is_published",)


@admin.register(FormPageSubmission)
class FormPageSubmissionAdmin(admin.ModelAdmin):
    list_display = ("id", "page", "submitted_at")
    list_filter = ("submitted_at",)
