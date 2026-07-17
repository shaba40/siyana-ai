#!/usr/bin/env python3

"""
Siyana AI local document and grounded-chat API.

This module provides:

- Local PDF and TXT import
- Imported-document listing
- Local document deletion
- SQLite FTS5 search
- Grounded Qwen3-4B answers with document citations

All documents, extracted content, searches, questions, and responses remain
on the local computer.
"""

from __future__ import annotations

import asyncio
import json
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Literal

from fastapi import (
    APIRouter,
    File,
    HTTPException,
    Query,
    UploadFile,
)
from pydantic import BaseModel, Field

from prototype.backend.app.document_store import (
    DocumentStore,
    DocumentStoreError,
    DuplicateDocumentError,
    EmptyDocumentError,
    UnsupportedDocumentError,
)


# ---------------------------------------------------------------------------
# Project configuration
# ---------------------------------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parents[3]

DATABASE_PATH = (
    PROJECT_DIR
    / "prototype"
    / "data"
    / "manuals.db"
)

DOCUMENTS_DIRECTORY = (
    PROJECT_DIR
    / "prototype"
    / "data"
    / "documents"
)

SYSTEM_PROMPT_PATH = (
    PROJECT_DIR
    / "config"
    / "system_prompt.txt"
)

LLAMA_BASE_URL = "http://127.0.0.1:8080"

MAX_UPLOAD_BYTES = 25 * 1024 * 1024
MAX_RETRIEVAL_RESULTS = 5
MAX_RETRIEVAL_CHARACTERS = 7500
MAX_GENERATED_TOKENS = 700
RESPONSE_TIMEOUT_SECONDS = 360
TEMPERATURE = 0.2


document_store = DocumentStore(
    database_path=DATABASE_PATH,
    documents_directory=DOCUMENTS_DIRECTORY,
)

router = APIRouter(
    prefix="/api",
    tags=["Local manuals and grounded chat"],
)


# ---------------------------------------------------------------------------
# API data models
# ---------------------------------------------------------------------------

SupportedLanguage = Literal["en", "fr", "ar"]


class DocumentSummary(BaseModel):
    """Imported local document information."""

    id: int
    filename: str
    file_type: str
    file_size_bytes: int
    sha256: str
    page_count: int
    chunk_count: int
    extracted_characters: int
    imported_at: str


class DocumentListResponse(BaseModel):
    """List of local documents and index statistics."""

    documents: list[DocumentSummary]
    document_count: int
    chunk_count: int


class ImportResponse(BaseModel):
    """Result of a local document import."""

    message: str
    document: DocumentSummary


class DeleteResponse(BaseModel):
    """Result of deleting a local document."""

    deleted: bool
    document_id: int


class SearchResult(BaseModel):
    """One locally retrieved document section."""

    document_id: int
    chunk_id: int
    filename: str
    page_number: int
    content: str
    rank: float
    citation: str


class SearchResponse(BaseModel):
    """Local search response."""

    query: str
    result_count: int
    results: list[SearchResult]


class GroundedChatRequest(BaseModel):
    """Grounded maintenance-question request."""

    language: SupportedLanguage = "en"

    question: str = Field(
        min_length=3,
        max_length=4000,
    )

    machine_name: str = Field(
        default="",
        max_length=200,
    )

    machine_model: str = Field(
        default="",
        max_length=200,
    )

    additional_context: str = Field(
        default="",
        max_length=3000,
    )

    use_documents: bool = True

    maximum_sources: int = Field(
        default=5,
        ge=1,
        le=10,
    )


class Citation(BaseModel):
    """Citation returned with a grounded answer."""

    number: int
    filename: str
    page_number: int
    document_id: int
    chunk_id: int
    excerpt: str


class GroundedChatResponse(BaseModel):
    """Grounded local-model answer."""

    answer: str
    language: SupportedLanguage
    duration_seconds: float
    model: str
    offline: bool
    document_search_used: bool
    source_count: int
    citations: list[Citation]
    safety_notice: str


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------

def load_system_prompt() -> str:
    """Load the approved Siyana AI system prompt."""

    if not SYSTEM_PROMPT_PATH.exists():
        raise RuntimeError(
            f"System prompt was not found: {SYSTEM_PROMPT_PATH}"
        )

    return SYSTEM_PROMPT_PATH.read_text(
        encoding="utf-8"
    ).strip()


def request_json(
    url: str,
    *,
    payload: dict[str, Any],
    timeout: int,
) -> dict[str, Any]:
    """Send a JSON POST request to the local llama.cpp server."""

    encoded = json.dumps(
        payload,
        ensure_ascii=False,
    ).encode("utf-8")

    request = urllib.request.Request(
        url=url,
        data=encoded,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=timeout,
        ) as response:
            body = response.read().decode("utf-8")
            return json.loads(body)

    except urllib.error.HTTPError as error:
        body = error.read().decode(
            "utf-8",
            errors="replace",
        )

        raise RuntimeError(
            f"Local model returned HTTP {error.code}: {body}"
        ) from error

    except urllib.error.URLError as error:
        raise RuntimeError(
            "Unable to communicate with the local model server: "
            f"{error.reason}"
        ) from error

    except json.JSONDecodeError as error:
        raise RuntimeError(
            "The local model server returned invalid JSON."
        ) from error


def extract_answer(response: dict[str, Any]) -> str:
    """Extract the assistant answer from an OpenAI-compatible response."""

    try:
        content = (
            response["choices"][0]["message"]["content"]
        )
    except (
        KeyError,
        IndexError,
        TypeError,
    ) as error:
        raise RuntimeError(
            "The local model response did not contain "
            "choices[0].message.content."
        ) from error

    if not isinstance(content, str):
        raise RuntimeError(
            "The local model returned an unsupported response format."
        )

    answer = content.strip()

    if not answer:
        raise RuntimeError(
            "The local model returned an empty answer."
        )

    return answer


def language_instruction(
    language: SupportedLanguage,
) -> str:
    """Return a strict response-language instruction."""

    instructions = {
        "en": "Respond only in English.",
        "fr": "Répondez uniquement en français.",
        "ar": "أجب باللغة العربية فقط.",
    }

    return instructions[language]


def safety_notice(
    language: SupportedLanguage,
) -> str:
    """Return a localized application safety notice."""

    notices = {
        "en": (
            "Preliminary guidance only. Follow the equipment manual, "
            "approved workplace procedures, and qualified maintenance "
            "personnel."
        ),
        "fr": (
            "Conseils préliminaires uniquement. Respectez le manuel de "
            "l'équipement, les procédures approuvées et faites intervenir "
            "du personnel qualifié."
        ),
        "ar": (
            "هذه إرشادات أولية فقط. يجب اتباع دليل المعدة وإجراءات العمل "
            "المعتمدة والاستعانة بأشخاص مؤهلين."
        ),
    }

    return notices[language]


# ---------------------------------------------------------------------------
# Grounding and prompt construction
# ---------------------------------------------------------------------------

def truncate_text(
    text: str,
    maximum_characters: int,
) -> str:
    """Truncate text without adding excessive prompt content."""

    normalized = text.strip()

    if len(normalized) <= maximum_characters:
        return normalized

    return normalized[:maximum_characters].rstrip() + "..."


def build_source_context(
    results: list[dict[str, Any]],
) -> tuple[str, list[Citation]]:
    """Create numbered model context and public citations."""

    if not results:
        return "", []

    context_sections: list[str] = []
    citations: list[Citation] = []

    used_characters = 0

    for number, result in enumerate(
        results,
        start=1,
    ):
        remaining = (
            MAX_RETRIEVAL_CHARACTERS
            - used_characters
        )

        if remaining <= 0:
            break

        excerpt = truncate_text(
            result["content"],
            min(remaining, 1800),
        )

        source_header = (
            f"[SOURCE {number}]\n"
            f"File: {result['filename']}\n"
            f"Page: {result['page_number']}\n"
            f"Content:\n{excerpt}"
        )

        context_sections.append(source_header)
        used_characters += len(source_header)

        citations.append(
            Citation(
                number=number,
                filename=result["filename"],
                page_number=result["page_number"],
                document_id=result["document_id"],
                chunk_id=result["chunk_id"],
                excerpt=truncate_text(
                    result["content"],
                    450,
                ),
            )
        )

    return "\n\n".join(context_sections), citations


def build_grounded_user_message(
    request: GroundedChatRequest,
    source_context: str,
) -> str:
    """Build the grounded user prompt."""

    lines = [
        "/no_think",
        "",
        language_instruction(request.language),
        "",
        "User question:",
        request.question.strip(),
    ]

    if request.machine_name.strip():
        lines.extend(
            [
                "",
                "Machine or equipment name:",
                request.machine_name.strip(),
            ]
        )

    if request.machine_model.strip():
        lines.extend(
            [
                "",
                "Machine model:",
                request.machine_model.strip(),
            ]
        )

    if request.additional_context.strip():
        lines.extend(
            [
                "",
                "Additional user-provided context:",
                request.additional_context.strip(),
            ]
        )

    if source_context:
        lines.extend(
            [
                "",
                "LOCAL MANUAL EXCERPTS",
                "",
                source_context,
                "",
                "GROUNDING RULES",
                "",
                (
                    "Use the excerpts only when they are relevant to the "
                    "question and equipment."
                ),
                (
                    "When using an excerpt, cite it using its exact source "
                    "number, for example [SOURCE 1]."
                ),
                (
                    "Do not claim that a source says something that is not "
                    "present in its excerpt."
                ),
                (
                    "If the excerpts are insufficient, state what information "
                    "or documentation is still required."
                ),
                (
                    "Do not invent alarm meanings, limits, settings, "
                    "tolerances, intervals, or procedures."
                ),
            ]
        )

    else:
        lines.extend(
            [
                "",
                "LOCAL MANUAL EXCERPTS",
                "",
                "No relevant local manual excerpt was found.",
                "",
                (
                    "Provide only general preliminary guidance and clearly "
                    "state that no relevant local manual source was found."
                ),
                (
                    "Do not invent equipment-specific values, alarm meanings, "
                    "diagnoses, or repair procedures."
                ),
            ]
        )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Document endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/documents/import",
    response_model=ImportResponse,
)
async def import_document(
    file: UploadFile = File(...),
) -> ImportResponse:
    """Import one PDF or TXT manual into the local repository."""

    filename = (
        Path(file.filename or "document").name
    )

    try:
        content = await file.read(
            MAX_UPLOAD_BYTES + 1
        )

    finally:
        await file.close()

    if len(content) > MAX_UPLOAD_BYTES:
        maximum_mb = (
            MAX_UPLOAD_BYTES
            // (1024 * 1024)
        )

        raise HTTPException(
            status_code=413,
            detail=(
                "The selected document is too large. "
                f"Maximum size: {maximum_mb} MB."
            ),
        )

    try:
        document = await asyncio.to_thread(
            document_store.import_document,
            filename,
            content,
        )

    except DuplicateDocumentError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from error

    except (
        UnsupportedDocumentError,
        EmptyDocumentError,
    ) as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except DocumentStoreError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    return ImportResponse(
        message="Document imported locally.",
        document=DocumentSummary(**document),
    )


@router.get(
    "/documents",
    response_model=DocumentListResponse,
)
async def list_documents() -> DocumentListResponse:
    """List locally imported documents."""

    documents = await asyncio.to_thread(
        document_store.list_documents
    )

    statistics = await asyncio.to_thread(
        document_store.database_statistics
    )

    return DocumentListResponse(
        documents=[
            DocumentSummary(**document)
            for document in documents
        ],
        document_count=statistics["document_count"],
        chunk_count=statistics["chunk_count"],
    )


@router.delete(
    "/documents/{document_id}",
    response_model=DeleteResponse,
)
async def delete_document(
    document_id: int,
) -> DeleteResponse:
    """Delete one local document and its searchable content."""

    deleted = await asyncio.to_thread(
        document_store.delete_document,
        document_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Document was not found.",
        )

    return DeleteResponse(
        deleted=True,
        document_id=document_id,
    )


@router.get(
    "/documents/search",
    response_model=SearchResponse,
)
async def search_documents(
    q: str = Query(
        min_length=2,
        max_length=1000,
    ),
    limit: int = Query(
        default=5,
        ge=1,
        le=10,
    ),
) -> SearchResponse:
    """Search local PDF and TXT manual sections."""

    try:
        results = await asyncio.to_thread(
            document_store.search,
            q,
            limit,
        )

    except DocumentStoreError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    return SearchResponse(
        query=q,
        result_count=len(results),
        results=[
            SearchResult(**result)
            for result in results
        ],
    )


# ---------------------------------------------------------------------------
# Grounded chat endpoint
# ---------------------------------------------------------------------------

@router.post(
    "/chat-grounded",
    response_model=GroundedChatResponse,
)
async def grounded_chat(
    request: GroundedChatRequest,
) -> GroundedChatResponse:
    """Generate a locally grounded industrial-maintenance answer."""

    retrieval_results: list[dict[str, Any]] = []

    if request.use_documents:
        try:
            retrieval_results = await asyncio.to_thread(
                document_store.search,
                request.question,
                request.maximum_sources,
            )

        except DocumentStoreError as error:
            raise HTTPException(
                status_code=400,
                detail=str(error),
            ) from error

    source_context, citations = build_source_context(
        retrieval_results
    )

    system_prompt = load_system_prompt()

    user_message = build_grounded_user_message(
        request,
        source_context,
    )

    payload = {
        "model": "Qwen3-4B-Q4_K_M",
        "messages": [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_message,
            },
        ],
        "temperature": TEMPERATURE,
        "max_tokens": MAX_GENERATED_TOKENS,
        "stream": False,
    }

    started = time.monotonic()

    try:
        response = await asyncio.to_thread(
            request_json,
            f"{LLAMA_BASE_URL}/v1/chat/completions",
            payload=payload,
            timeout=RESPONSE_TIMEOUT_SECONDS,
        )

        answer = extract_answer(response)

    except RuntimeError as error:
        raise HTTPException(
            status_code=502,
            detail=str(error),
        ) from error

    duration_seconds = round(
        time.monotonic() - started,
        3,
    )

    return GroundedChatResponse(
        answer=answer,
        language=request.language,
        duration_seconds=duration_seconds,
        model="Qwen3-4B Q4_K_M",
        offline=True,
        document_search_used=(
            request.use_documents
            and bool(retrieval_results)
        ),
        source_count=len(citations),
        citations=citations,
        safety_notice=safety_notice(
            request.language
        ),
    )
