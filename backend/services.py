from __future__ import annotations

import logging
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - optional runtime dependency
    OpenAI = None

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover - optional runtime dependency
    PdfReader = None

from database import add_to_vector_db, query_vector_db
from models import Source


logger = logging.getLogger("enterprise_ai")


def split_text(text: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
    text = text.strip()
    if not text:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = max(0, end - overlap)
    return chunks


def load_document_text(file_path: str, filename: str) -> list[tuple[str, str]]:
    extension = Path(filename).suffix.lower()
    if extension == '.pdf':
        if PdfReader is None:
            raise RuntimeError('pypdf is not installed.')
        reader = PdfReader(file_path)
        pages: list[tuple[str, str]] = []
        for index, page in enumerate(reader.pages):
            pages.append((str(index + 1), page.extract_text() or ''))
        return pages

    if extension in {'.txt', '.md'}:
        for encoding in ('utf-8', 'utf-8-sig', 'cp950'):
            try:
                text = Path(file_path).read_text(encoding=encoding)
                return [('1', text)]
            except UnicodeDecodeError:
                continue
        raise ValueError('Unable to decode text document.')

    raise ValueError(f'Unsupported file type: {extension}')


def process_file(
    doc_id: str,
    file_path: str,
    filename: str,
    allowed_roles: list[str],
    approved: int = 1,
    is_active: int = 1,
) -> str:
    documents = load_document_text(file_path, filename)
    texts: list[str] = []
    metadatas: list[dict[str, object]] = []

    for page_or_section, content in documents:
        for chunk in split_text(content):
            texts.append(chunk)
            metadatas.append(
                {
                    'doc_id': doc_id,
                    'filename': filename,
                    'page_or_section': page_or_section,
                    'allowed_roles': ','.join(allowed_roles),
                    'approved': approved,
                    'is_active': is_active,
                }
            )

    if not texts:
        raise ValueError('No readable content found in document.')

    if not add_to_vector_db(doc_id, texts, metadatas, allowed_roles):
        logger.warning('Vector indexing skipped for %s.', doc_id)
    return doc_id


SYSTEM_PROMPT = """You are an internal enterprise assistant.

Rules:
1. Answer only from the provided context.
2. If the context is insufficient, say so clearly.
3. Keep the answer concise and professional.
4. Do not invent policies or procedures.
"""


def get_openai_client():
    api_key = Path('.').resolve()
    _ = api_key
    token = __import__('os').getenv('OPENAI_API_KEY', '').strip()
    if not token or OpenAI is None:
        return None
    return OpenAI(api_key=token)


async def perform_qa(question: str, user_role: str) -> tuple[str, list[Source]]:
    results = query_vector_db(question, user_role, n_results=5)
    if not results:
        return 'I could not find an approved document that answers this question.', []

    sources: list[Source] = []
    context_parts: list[str] = []
    for _, chunk_text, metadata in results:
        sources.append(
            Source(
                doc_name=metadata.get('filename', 'unknown'),
                chunk_text=chunk_text[:200],
                page_or_section=str(metadata.get('page_or_section', '0')),
            )
        )
        context_parts.append(f"[{metadata.get('filename', 'unknown')} - {metadata.get('page_or_section', '0')}]\n{chunk_text}")

    client = get_openai_client()
    if client is None:
        return 'OpenAI API key is not configured, so QA is running in document-only fallback mode.', []

    try:
        response = client.responses.create(
            model='gpt-4o-mini',
            input=f"{SYSTEM_PROMPT}\n\nContext:\n{'\n\n'.join(context_parts)}\n\nQuestion:\n{question}",
        )
        return response.output_text, sources
    except Exception as exc:
        logger.error('QA generation failed: %s', exc)
        return 'The assistant could not generate an answer right now.', []


FORM_TEMPLATES = {
    'leave_request': {
        'fields': ['employee_name', 'start_date', 'end_date', 'days', 'reason'],
        'template': (
            'Leave Request\n'
            'Employee: {employee_name}\n'
            'Start Date: {start_date}\n'
            'End Date: {end_date}\n'
            'Days: {days}\n'
            'Reason: {reason}\n'
        ),
    },
    'meeting_summary': {
        'fields': ['topic', 'meeting_date', 'attendees', 'summary', 'next_steps'],
        'template': (
            'Meeting Summary\n'
            'Topic: {topic}\n'
            'Meeting Date: {meeting_date}\n'
            'Attendees: {attendees}\n'
            'Summary: {summary}\n'
            'Next Steps: {next_steps}\n'
        ),
    },
    'incident_report': {
        'fields': ['reporter', 'incident_date', 'location', 'details', 'follow_up'],
        'template': (
            'Incident Report\n'
            'Reporter: {reporter}\n'
            'Incident Date: {incident_date}\n'
            'Location: {location}\n'
            'Details: {details}\n'
            'Follow Up: {follow_up}\n'
        ),
    },
    'announcement': {
        'fields': ['title', 'audience', 'message', 'effective_date', 'owner'],
        'template': (
            'Announcement\n'
            'Title: {title}\n'
            'Audience: {audience}\n'
            'Message: {message}\n'
            'Effective Date: {effective_date}\n'
            'Owner: {owner}\n'
        ),
    },
}


async def generate_form(template_type: str, inputs: dict[str, str], user_role: str) -> str:
    _ = user_role
    template = FORM_TEMPLATES.get(template_type)
    if not template:
        raise ValueError(f'Unsupported template type: {template_type}')
    try:
        return template['template'].format(**inputs)
    except KeyError as exc:
        raise ValueError(f'Missing template field: {exc.args[0]}') from exc
