#!/usr/bin/env python3

"""
Local document storage and retrieval for Siyana AI.

Features:

- Imports text-based PDF and TXT manuals.
- Extracts text entirely on the local computer.
- Divides text into overlapping searchable sections.
- Stores document metadata in SQLite.
- Indexes sections with SQLite FTS5.
- Retrieves relevant sections using BM25 relevance ranking.
- Deletes imported documents and indexed content.
- Does not require network access.

Scanned image-only PDFs are not OCR-processed in this version.
"""

from __future__ import annotations

import hashlib
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pypdf import PdfReader


SUPPORTED_EXTENSIONS = {".pdf", ".txt"}

MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024
MAX_PDF_PAGES = 500

DEFAULT_CHUNK_CHARACTERS = 1800
DEFAULT_CHUNK_OVERLAP = 250
DEFAULT_SEARCH_LIMIT = 5


@dataclass(frozen=True)
class ExtractedPage:
    """Text extracted from one page or text-file section."""

    page_number: int
    text: str


@dataclass(frozen=True)
class DocumentChunk:
    """One searchable document section."""

    page_number: int
    chunk_index: int
    content: str


class DocumentStoreError(RuntimeError):
    """Base exception for local document operations."""


class UnsupportedDocumentError(DocumentStoreError):
    """Raised when the selected file type is unsupported."""


class EmptyDocumentError(DocumentStoreError):
    """Raised when no useful text can be extracted."""


class DuplicateDocumentError(DocumentStoreError):
    """Raised when the same file was already imported."""


class DocumentStore:
    """SQLite-backed local manual repository."""

    def __init__(
        self,
        database_path: Path,
        documents_directory: Path,
    ) -> None:
        self.database_path = database_path.resolve()
        self.documents_directory = documents_directory.resolve()

        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.documents_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.initialize_database()

    def connect(self) -> sqlite3.Connection:
        """Open a configured SQLite connection."""

        connection = sqlite3.connect(
            self.database_path,
            timeout=30,
        )

        connection.row_factory = sqlite3.Row

        connection.execute(
            "PRAGMA foreign_keys = ON"
        )

        connection.execute(
            "PRAGMA journal_mode = WAL"
        )

        return connection

    def initialize_database(self) -> None:
        """Create metadata and FTS5 tables."""

        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    stored_filename TEXT NOT NULL UNIQUE,
                    file_type TEXT NOT NULL,
                    file_size_bytes INTEGER NOT NULL,
                    sha256 TEXT NOT NULL UNIQUE,
                    page_count INTEGER NOT NULL,
                    chunk_count INTEGER NOT NULL,
                    extracted_characters INTEGER NOT NULL,
                    imported_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER NOT NULL,
                    page_number INTEGER NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    content TEXT NOT NULL,

                    FOREIGN KEY (document_id)
                        REFERENCES documents(id)
                        ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS
                    idx_chunks_document_id
                    ON chunks(document_id);

                CREATE UNIQUE INDEX IF NOT EXISTS
                    idx_chunks_document_position
                    ON chunks(
                        document_id,
                        page_number,
                        chunk_index
                    );

                CREATE VIRTUAL TABLE IF NOT EXISTS
                    chunks_fts
                    USING fts5(
                        content,
                        document_id UNINDEXED,
                        chunk_id UNINDEXED,
                        filename UNINDEXED,
                        page_number UNINDEXED,
                        tokenize='unicode61 remove_diacritics 2'
                    );
                """
            )

    @staticmethod
    def utc_timestamp() -> str:
        """Return an ISO-formatted UTC timestamp."""

        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def calculate_sha256(content: bytes) -> str:
        """Calculate a file SHA-256 digest."""

        return hashlib.sha256(content).hexdigest()

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Create a safe local storage filename."""

        original = Path(filename).name.strip()

        if not original:
            original = "document"

        stem = Path(original).stem
        suffix = Path(original).suffix.lower()

        safe_stem = re.sub(
            r"[^A-Za-z0-9._-]+",
            "_",
            stem,
        ).strip("._")

        if not safe_stem:
            safe_stem = "document"

        return f"{safe_stem}{suffix}"

    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize extracted text while retaining paragraphs."""

        text = text.replace("\x00", " ")
        text = text.replace("\r\n", "\n")
        text = text.replace("\r", "\n")

        lines: list[str] = []

        for line in text.splitlines():
            normalized_line = re.sub(
                r"[ \t]+",
                " ",
                line,
            ).strip()

            lines.append(normalized_line)

        normalized = "\n".join(lines)

        normalized = re.sub(
            r"\n{3,}",
            "\n\n",
            normalized,
        )

        return normalized.strip()

    def validate_upload(
        self,
        filename: str,
        content: bytes,
    ) -> str:
        """Validate extension, size and content."""

        suffix = Path(filename).suffix.lower()

        if suffix not in SUPPORTED_EXTENSIONS:
            supported = ", ".join(
                sorted(SUPPORTED_EXTENSIONS)
            )

            raise UnsupportedDocumentError(
                "Unsupported document type. "
                f"Supported types: {supported}"
            )

        if not content:
            raise EmptyDocumentError(
                "The selected document is empty."
            )

        if len(content) > MAX_FILE_SIZE_BYTES:
            maximum_mb = (
                MAX_FILE_SIZE_BYTES
                // (1024 * 1024)
            )

            raise DocumentStoreError(
                "The document is too large. "
                f"Maximum size: {maximum_mb} MB."
            )

        return suffix

    def extract_pdf(
        self,
        file_path: Path,
    ) -> list:
        """Extract text from a text-based PDF."""

        try:
            reader = PdfReader(
                str(file_path),
                strict=False,
            )
        except Exception as error:
            raise DocumentStoreError(
                f"Unable to open PDF: {error}"
            ) from error

        if reader.is_encrypted:
            try:
                unlocked = reader.decrypt("")
            except Exception as error:
                raise DocumentStoreError(
                    "The PDF is encrypted and could not "
                    "be opened without a password."
                ) from error

            if unlocked == 0:
                raise DocumentStoreError(
                    "Password-protected PDFs are not "
                    "supported in this prototype."
                )

        page_count = len(reader.pages)

        if page_count == 0:
            raise EmptyDocumentError(
                "The PDF contains no pages."
            )

        if page_count > MAX_PDF_PAGES:
            raise DocumentStoreError(
                "The PDF contains too many pages. "
                f"Maximum supported pages: {MAX_PDF_PAGES}."
            )

        extracted_pages: list[ExtractedPage] = []

        for page_index, page in enumerate(
            reader.pages,
            start=1,
        ):
            try:
                text = page.extract_text() or ""
            except Exception as error:
                raise DocumentStoreError(
                    "Unable to extract text from "
                    f"PDF page {page_index}: {error}"
                ) from error

            normalized = self.normalize_text(text)

            if normalized:
                extracted_pages.append(
                    ExtractedPage(
                        page_number=page_index,
                        text=normalized,
                    )
                )

        if not extracted_pages:
            raise EmptyDocumentError(
                "No searchable text was extracted. "
                "The PDF may be scanned or image-only. "
                "OCR is not included in this version."
            )

        return extracted_pages

    def extract_txt(
        self,
        file_path: Path,
    ) -> list:
        """Extract text from a UTF-8 or common text file."""

        raw = file_path.read_bytes()

        decoded: str | None = None

        for encoding in (
            "utf-8-sig",
            "utf-8",
            "cp1252",
            "latin-1",
        ):
            try:
                decoded = raw.decode(encoding)
                break
            except UnicodeDecodeError:
                continue

        if decoded is None:
            raise DocumentStoreError(
                "The text-file encoding could not be detected."
            )

        normalized = self.normalize_text(decoded)

        if not normalized:
            raise EmptyDocumentError(
                "No searchable text was found "
                "in the text file."
            )

        return [
            ExtractedPage(
                page_number=1,
                text=normalized,
            )
        ]

    def extract_document(
        self,
        file_path: Path,
        suffix: str,
    ) -> list:
        """Extract text based on the document type."""

        if suffix == ".pdf":
            return self.extract_pdf(file_path)

        if suffix == ".txt":
            return self.extract_txt(file_path)

        raise UnsupportedDocumentError(
            f"Unsupported extension: {suffix}"
        )

    @staticmethod
    def split_long_paragraph(
        paragraph: str,
        maximum_characters: int,
    ) -> list:
        """Split a long paragraph without discarding text."""

        pieces: list[str] = []
        remaining = paragraph.strip()

        while len(remaining) > maximum_characters:
            preferred_end = maximum_characters

            candidates = [
                remaining.rfind(". ", 0, preferred_end),
                remaining.rfind("; ", 0, preferred_end),
                remaining.rfind(", ", 0, preferred_end),
                remaining.rfind(" ", 0, preferred_end),
            ]

            split_position = max(candidates)

            if split_position < maximum_characters // 2:
                split_position = maximum_characters
            else:
                split_position += 1

            piece = remaining[:split_position].strip()

            if piece:
                pieces.append(piece)

            remaining = remaining[split_position:].strip()

        if remaining:
            pieces.append(remaining)

        return pieces

    def chunk_page(
        self,
        page: ExtractedPage,
        maximum_characters: int = DEFAULT_CHUNK_CHARACTERS,
        overlap_characters: int = DEFAULT_CHUNK_OVERLAP,
    ) -> list:
        """Divide one page into overlapping searchable sections."""

        paragraphs = [
            paragraph.strip()
            for paragraph in re.split(
                r"\n\s*\n",
                page.text,
            )
            if paragraph.strip()
        ]

        units: list[str] = []

        for paragraph in paragraphs:
            if len(paragraph) <= maximum_characters:
                units.append(paragraph)
            else:
                units.extend(
                    self.split_long_paragraph(
                        paragraph,
                        maximum_characters,
                    )
                )

        chunks: list[str] = []
        current_parts: list[str] = []
        current_length = 0

        for unit in units:
            added_length = (
                len(unit)
                + (2 if current_parts else 0)
            )

            if (
                current_parts
                and current_length + added_length
                > maximum_characters
            ):
                chunk_text = "\n\n".join(
                    current_parts
                ).strip()

                if chunk_text:
                    chunks.append(chunk_text)

                overlap_text = (
                    chunk_text[-overlap_characters:]
                    if overlap_characters > 0
                    else ""
                ).strip()

                current_parts = (
                    [overlap_text, unit]
                    if overlap_text
                    else [unit]
                )

                current_length = len(
                    "\n\n".join(current_parts)
                )

            else:
                current_parts.append(unit)
                current_length += added_length

        if current_parts:
            chunk_text = "\n\n".join(
                current_parts
            ).strip()

            if chunk_text:
                chunks.append(chunk_text)

        return [
            DocumentChunk(
                page_number=page.page_number,
                chunk_index=index,
                content=content,
            )
            for index, content in enumerate(
                chunks,
                start=1,
            )
        ]

    def create_chunks(
        self,
        pages: list[ExtractedPage],
    ) -> list:
        """Create chunks for all extracted pages."""

        chunks: list[DocumentChunk] = []

        for page in pages:
            chunks.extend(
                self.chunk_page(page)
            )

        if not chunks:
            raise EmptyDocumentError(
                "No searchable sections could be created."
            )

        return chunks

    def unique_stored_filename(
        self,
        original_filename: str,
        sha256: str,
    ) -> str:
        """Build a collision-resistant stored filename."""

        safe_name = self.sanitize_filename(
            original_filename
        )

        stem = Path(safe_name).stem
        suffix = Path(safe_name).suffix.lower()

        return f"{stem}-{sha256[:12]}{suffix}"

    def import_document(
        self,
        original_filename: str,
        content: bytes,
    ) -> dict[str, Any]:
        """Save, extract, chunk and index a local document."""

        suffix = self.validate_upload(
            original_filename,
            content,
        )

        sha256 = self.calculate_sha256(content)

        with self.connect() as connection:
            duplicate = connection.execute(
                """
                SELECT id, filename
                FROM documents
                WHERE sha256 = ?
                """,
                (sha256,),
            ).fetchone()

        if duplicate is not None:
            raise DuplicateDocumentError(
                "This document was already imported as "
                f"'{duplicate['filename']}'."
            )

        stored_filename = self.unique_stored_filename(
            original_filename,
            sha256,
        )

        stored_path = (
            self.documents_directory
            / stored_filename
        )

        stored_path.write_bytes(content)

        try:
            pages = self.extract_document(
                stored_path,
                suffix,
            )

            chunks = self.create_chunks(pages)

            extracted_characters = sum(
                len(page.text)
                for page in pages
            )

            imported_at = self.utc_timestamp()

            with self.connect() as connection:
                cursor = connection.execute(
                    """
                    INSERT INTO documents (
                        filename,
                        stored_filename,
                        file_type,
                        file_size_bytes,
                        sha256,
                        page_count,
                        chunk_count,
                        extracted_characters,
                        imported_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        Path(original_filename).name,
                        stored_filename,
                        suffix,
                        len(content),
                        sha256,
                        max(
                            page.page_number
                            for page in pages
                        ),
                        len(chunks),
                        extracted_characters,
                        imported_at,
                    ),
                )

                document_id = int(
                    cursor.lastrowid
                )

                for chunk in chunks:
                    chunk_cursor = connection.execute(
                        """
                        INSERT INTO chunks (
                            document_id,
                            page_number,
                            chunk_index,
                            content
                        )
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            document_id,
                            chunk.page_number,
                            chunk.chunk_index,
                            chunk.content,
                        ),
                    )

                    chunk_id = int(
                        chunk_cursor.lastrowid
                    )

                    connection.execute(
                        """
                        INSERT INTO chunks_fts (
                            content,
                            document_id,
                            chunk_id,
                            filename,
                            page_number
                        )
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            chunk.content,
                            str(document_id),
                            str(chunk_id),
                            Path(original_filename).name,
                            str(chunk.page_number),
                        ),
                    )

                connection.commit()

        except Exception:
            stored_path.unlink(
                missing_ok=True
            )
            raise

        return {
            "id": document_id,
            "filename": Path(
                original_filename
            ).name,
            "file_type": suffix,
            "file_size_bytes": len(content),
            "sha256": sha256,
            "page_count": max(
                page.page_number
                for page in pages
            ),
            "chunk_count": len(chunks),
            "extracted_characters": (
                extracted_characters
            ),
            "imported_at": imported_at,
        }

    def list_documents(self) -> list[dict[str, Any]]:
        """Return all imported documents."""

        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    id,
                    filename,
                    file_type,
                    file_size_bytes,
                    sha256,
                    page_count,
                    chunk_count,
                    extracted_characters,
                    imported_at
                FROM documents
                ORDER BY imported_at DESC
                """
            ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    def delete_document(
        self,
        document_id: int,
    ) -> bool:
        """Delete one document and its local index."""

        with self.connect() as connection:
            document = connection.execute(
                """
                SELECT stored_filename
                FROM documents
                WHERE id = ?
                """,
                (document_id,),
            ).fetchone()

            if document is None:
                return False

            connection.execute(
                """
                DELETE FROM chunks_fts
                WHERE document_id = ?
                """,
                (str(document_id),),
            )

            connection.execute(
                """
                DELETE FROM documents
                WHERE id = ?
                """,
                (document_id,),
            )

            connection.commit()

        stored_path = (
            self.documents_directory
            / document["stored_filename"]
        )

        stored_path.unlink(
            missing_ok=True
        )

        return True

    @staticmethod
    def prepare_fts_query(query: str) -> str:
        """Create a conservative FTS5 OR query."""

        words = re.findall(
            r"[A-Za-zÀ-ÖØ-öø-ÿ0-9_\u0600-\u06FF]+",
            query,
        )

        unique_words: list[str] = []
        seen: set[str] = set()

        for word in words:
            normalized = word.casefold()

            if len(normalized) < 2:
                continue

            if normalized in seen:
                continue

            seen.add(normalized)
            unique_words.append(normalized)

        if not unique_words:
            return ""

        limited = unique_words[:20]

        quoted = [
            f'"{word.replace(chr(34), "")}"'
            for word in limited
        ]

        return " OR ".join(quoted)

    def search(
        self,
        query: str,
        limit: int = DEFAULT_SEARCH_LIMIT,
    ) -> list[dict[str, Any]]:
        """Search indexed manuals using FTS5 BM25 ranking."""

        prepared_query = self.prepare_fts_query(
            query
        )

        if not prepared_query:
            return []

        safe_limit = max(
            1,
            min(limit, 10),
        )

        with self.connect() as connection:
            try:
                rows = connection.execute(
                    """
                    SELECT
                        CAST(document_id AS INTEGER)
                            AS document_id,
                        CAST(chunk_id AS INTEGER)
                            AS chunk_id,
                        filename,
                        CAST(page_number AS INTEGER)
                            AS page_number,
                        content,
                        bm25(chunks_fts) AS rank
                    FROM chunks_fts
                    WHERE chunks_fts MATCH ?
                    ORDER BY rank
                    LIMIT ?
                    """,
                    (
                        prepared_query,
                        safe_limit,
                    ),
                ).fetchall()

            except sqlite3.OperationalError as error:
                raise DocumentStoreError(
                    f"Unable to search document index: {error}"
                ) from error

        return [
            {
                "document_id": row["document_id"],
                "chunk_id": row["chunk_id"],
                "filename": row["filename"],
                "page_number": row["page_number"],
                "content": row["content"],
                "rank": row["rank"],
                "citation": (
                    f"{row['filename']}, "
                    f"page {row['page_number']}"
                ),
            }
            for row in rows
        ]

    def database_statistics(self) -> dict[str, int]:
        """Return local retrieval statistics."""

        with self.connect() as connection:
            document_count = connection.execute(
                "SELECT COUNT(*) FROM documents"
            ).fetchone()[0]

            chunk_count = connection.execute(
                "SELECT COUNT(*) FROM chunks"
            ).fetchone()[0]

        return {
            "document_count": int(
                document_count
            ),
            "chunk_count": int(
                chunk_count
            ),
        }
