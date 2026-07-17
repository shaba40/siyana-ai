#!/usr/bin/env python3

"""
Local smoke test for the Siyana AI document repository.
"""

from __future__ import annotations

from pathlib import Path

from prototype.backend.app.document_store import (
    DocumentStore,
)


PROJECT_DIR = Path(__file__).resolve().parent.parent

DATABASE_PATH = (
    PROJECT_DIR
    / "prototype"
    / "data"
    / "test-manuals.db"
)

DOCUMENTS_DIRECTORY = (
    PROJECT_DIR
    / "prototype"
    / "data"
    / "test-documents"
)


def main() -> None:
    """Import and search one synthetic maintenance document."""

    store = DocumentStore(
        database_path=DATABASE_PATH,
        documents_directory=DOCUMENTS_DIRECTORY,
    )

    sample_text = """
Pneumatic Cylinder Troubleshooting

Before inspecting the pneumatic machine, stop the machine,
isolate all hazardous energy sources, and release stored air
pressure according to the approved workplace procedure.

A cylinder that moves slowly in both directions may be affected
by low supply pressure, a restricted filter, a partially closed
flow-control valve, a leaking hose, internal cylinder leakage,
or excessive mechanical load.

Never increase the pressure above the equipment manufacturer's
specified limit. Do not search for leaks by putting hands close
to moving machine components.

Record the measured supply pressure, machine model, operating
load, symptoms, and recent maintenance history before escalating
the problem to qualified maintenance personnel.
""".strip()

    content = sample_text.encode("utf-8")

    try:
        imported = store.import_document(
            original_filename="sample-pneumatic-manual.txt",
            content=content,
        )

        print("Imported document:")
        print(imported)

    except Exception as error:
        print(f"Import note: {error}")

    print()
    print("Documents:")

    for document in store.list_documents():
        print(document)

    print()
    print("Search results:")

    results = store.search(
        "pneumatic cylinder slow pressure leakage",
        limit=5,
    )

    for result in results:
        print("-" * 72)
        print("Citation:", result["citation"])
        print("Rank:", result["rank"])
        print(result["content"][:500])

    print()
    print("Statistics:")
    print(store.database_statistics())


if __name__ == "__main__":
    main()
