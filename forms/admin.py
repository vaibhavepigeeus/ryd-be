from django.contrib import admin

from .models import FormForm, FormQuestion, FormSubsection, FormType


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
    list_display = ("id", "question_id", "form_type", "version", "answer_type")
    list_filter = ("answer_type", "version")


@admin.register(FormForm)
class FormFormAdmin(admin.ModelAdmin):
    list_display = ("id", "form_id", "form_version", "sequence_no", "user_entered")
    list_filter = ("form_version",)
