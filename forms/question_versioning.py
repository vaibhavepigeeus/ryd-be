import uuid
from decimal import Decimal

from .models import FormQuestion


def generate_question_id():
    return f"Q{uuid.uuid4().hex[:8].upper()}"


def create_question_version(source: FormQuestion, question_text: str) -> FormQuestion:
    """Create a new form_questions row with incremented version and a fresh question_id."""
    new_version = source.version + Decimal("1.0")

    return FormQuestion.objects.create(
        form_type=source.form_type,
        version=new_version,
        question_id=generate_question_id(),
        association_subsection=source.association_subsection,
        question=question_text,
        answer_type=source.answer_type,
        sequence_no=source.sequence_no,
    )
