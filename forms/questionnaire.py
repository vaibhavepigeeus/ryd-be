from django.utils.html import strip_tags

from .models import FormFrequency, FormForm, FormQuestion, FormSubsection, FormType

FREQUENCY_LABELS = dict(FormFrequency.choices)


def _clean_html(value):
    if not value:
        return ''
    return strip_tags(value).strip()


def _frequency_subtitle(frequency):
    label = FREQUENCY_LABELS.get(frequency, 'Form')
    return f'RYD {label} Tool'


def build_questionnaire_list_item(form_type):
    return {
        'id': str(form_type.id),
        'formId': form_type.form_id,
        'formVersion': str(form_type.form_version),
        'title': _clean_html(form_type.form_name),
        'subtitle': _frequency_subtitle(form_type.frequency),
    }


def build_questionnaire_detail(form_type):
    version = form_type.form_version

    subsections = list(
        FormSubsection.objects.filter(form_type=form_type, version=version).order_by('id')
    )
    form_form_sequence = {
        item.question_id: item.sequence_no
        for item in FormForm.objects.filter(
            form_type=form_type,
            version=version,
            question__isnull=False,
        )
    }

    questions = list(
        FormQuestion.objects.filter(form_type=form_type, version=version).order_by(
            "sequence_no", "id"
        )
    )

    subsection_sections = {
        subsection.id: {
            'id': str(subsection.id),
            'title': _clean_html(subsection.subsection),
            'fields': [],
        }
        for subsection in subsections
    }

    sections = [subsection_sections[subsection.id] for subsection in subsections]
    general_section = None

    for question in questions:
        field = {
            'id': question.question_id or str(question.id),
            'label': _clean_html(question.question),
            'type': question.answer_type,
            'required': True,
            'sequenceNo': form_form_sequence.get(
                question.id, question.sequence_no
            ),
        }

        if question.association_subsection_id in subsection_sections:
            subsection_sections[question.association_subsection_id]['fields'].append(field)
        else:
            if general_section is None:
                general_section = {
                    'id': 'general',
                    'title': '',
                    'fields': [],
                }
                sections.insert(0, general_section)
            general_section['fields'].append(field)

    for section in sections:
        section['fields'].sort(key=lambda field: field['sequenceNo'])

    sections = [section for section in sections if section['title'] or section['fields']]

    return {
        **build_questionnaire_list_item(form_type),
        'sections': sections,
    }
