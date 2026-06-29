import uuid
from decimal import Decimal

from django.db import models
from django.db.models import Max
from django.utils import timezone


class FormFrequency(models.IntegerChoices):
    ANNUALLY = 1, "Annually"
    QUARTERLY = 2, "Quarterly"
    MONTHLY = 3, "Monthly"
    WEEKLY = 4, "Weekly"
    DAILY = 5, "Daily"
    ADHOC = 6, "Adhoc"
    OTHER = 99, "Other"


class AnswerType(models.TextChoices):
    TEXT = "text", "Text"
    TEXTAREA = "textarea", "Text Area"
    NUMBER = "number", "Number"
    DATE = "date", "Date"
    DROPDOWN = "dropdown", "Dropdown"
    MULTI_SELECT = "multi_select", "Multi Select"
    CHECKBOX = "checkbox", "Checkbox"
    RADIO = "radio", "Radio"
    FILE = "file", "File"


class FormType(models.Model):
    form_id = models.PositiveIntegerField(editable=False)
    form_version = models.DecimalField(max_digits=4, decimal_places=1, default=Decimal("1.0"))
    form_name = models.TextField(help_text="Rich text (HTML) for form title")
    frequency = models.IntegerField(choices=FormFrequency.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "form_types"
        unique_together = [("form_id", "form_version")]
        ordering = ["form_id", "-form_version"]

    def save(self, *args, **kwargs):
        if not self.form_id:
            max_form_id = FormType.objects.aggregate(m=Max("form_id"))["m"]
            self.form_id = (max_form_id or 0) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Form {self.form_id} v{self.form_version}"


class FormSubsection(models.Model):
    form_type = models.ForeignKey(
        FormType,
        on_delete=models.CASCADE,
        related_name="subsections",
    )
    version = models.DecimalField(max_digits=4, decimal_places=1, default=Decimal("1.0"))
    subsection = models.TextField(help_text="Rich text (HTML) subsection heading")

    class Meta:
        db_table = "form_subsection"
        ordering = ["id"]

    def __str__(self):
        return f"Subsection {self.id} (v{self.version})"


class FormQuestion(models.Model):
    form_type = models.ForeignKey(
        FormType,
        on_delete=models.CASCADE,
        related_name="questions",
    )
    version = models.DecimalField(max_digits=4, decimal_places=1, default=Decimal("1.0"))
    question_id = models.CharField(max_length=50, null=True, blank=True)
    association_subsection = models.ForeignKey(
        FormSubsection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="questions",
    )
    question = models.TextField(help_text="Rich text (HTML) question text")
    answer_type = models.CharField(max_length=50, choices=AnswerType.choices)
    sequence_no = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Display order within the form version (lower = earlier)",
    )

    class Meta:
        db_table = "form_questions"
        ordering = ["sequence_no", "id"]

    def save(self, *args, **kwargs):
        if self.sequence_no is None:
            max_seq = FormQuestion.objects.filter(
                form_type=self.form_type,
                version=self.version,
            ).aggregate(m=Max("sequence_no"))["m"]
            self.sequence_no = (max_seq or 0) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.question_id or f"Question {self.id}"


class FormForm(models.Model):
    form_type = models.ForeignKey(
        FormType,
        on_delete=models.CASCADE,
        related_name="form_items",
    )
    version = models.DecimalField(max_digits=4, decimal_places=1, default=Decimal("1.0"))
    form_id = models.PositiveIntegerField()
    form_version = models.DecimalField(max_digits=4, decimal_places=1)
    sequence_no = models.PositiveIntegerField()
    user_entered = models.BooleanField(default=False)
    paratext = models.TextField(null=True, blank=True, help_text="Rich text (HTML)")
    image = models.CharField(max_length=500, null=True, blank=True)
    question = models.ForeignKey(
        FormQuestion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="form_items",
    )
    auto_select_version = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    auto_select_text = models.TextField(null=True, blank=True, help_text="Rich text (HTML)")

    class Meta:
        db_table = "form_forms"
        ordering = ["sequence_no"]

    def save(self, *args, **kwargs):
        if self.form_type_id:
            self.form_id = self.form_type.form_id
            self.form_version = self.form_type.form_version
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Form item {self.sequence_no} (form {self.form_id} v{self.form_version})"


class FormPage(models.Model):
    """Saved form-builder page layout and content."""

    page_name = models.CharField(max_length=255)
    layout_data = models.JSONField(default=dict)
    is_published = models.BooleanField(default=False)
    publish_slug = models.CharField(max_length=64, unique=True, null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "form_pages"
        ordering = ["-updated_at"]

    def publish(self):
        if not self.publish_slug:
            self.publish_slug = uuid.uuid4().hex[:12]
        self.is_published = True
        self.published_at = timezone.now()
        self.save(
            update_fields=["is_published", "publish_slug", "published_at", "updated_at"]
        )

    def __str__(self):
        return self.page_name


class FormPageSubmission(models.Model):
    page = models.ForeignKey(
        FormPage,
        on_delete=models.CASCADE,
        related_name="submissions",
    )
    response_data = models.JSONField(default=dict)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "form_page_submissions"
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"Submission {self.id} for {self.page.page_name}"
