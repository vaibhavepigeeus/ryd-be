from decimal import Decimal

from django.db import models
from django.db.models import Max


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

    class Meta:
        db_table = "form_questions"
        ordering = ["id"]

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
