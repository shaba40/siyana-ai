#!/usr/bin/env python3

"""
Build and validate the complete Siyana AI evaluation dataset.

The source prompts are stored in three language-specific JSON files:

- evaluation/domain/datasets/prompts-en.json
- evaluation/domain/datasets/prompts-fr.json
- evaluation/domain/datasets/prompts-ar.json

The validated output is written to:

- evaluation/domain/prompts-full.json
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parent.parent

DATASET_DIR = PROJECT_DIR / "evaluation" / "domain" / "datasets"

SOURCE_FILES = [
    DATASET_DIR / "prompts-en.json",
    DATASET_DIR / "prompts-fr.json",
    DATASET_DIR / "prompts-ar.json",
]

OUTPUT_FILE = (
    PROJECT_DIR
    / "evaluation"
    / "domain"
    / "prompts-full.json"
)

EXPECTED_LANGUAGES = {
    "en": 20,
    "fr": 20,
    "ar": 20,
}

EXPECTED_CATEGORIES_PER_LANGUAGE = {
    "troubleshooting": 5,
    "preventive_maintenance": 5,
    "enterprise_productivity": 4,
    "safety": 3,
    "insufficient_information": 3,
}

REQUIRED_FIELDS = {
    "id",
    "language",
    "category",
    "prompt",
    "expected_behaviors",
}


def load_json(path: Path) -> Any:
    """Load a UTF-8 JSON file."""

    if not path.exists():
        raise RuntimeError(f"Missing dataset file: {path}")

    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"Invalid JSON in {path}: "
            f"line {error.lineno}, "
            f"column {error.colno}: "
            f"{error.msg}"
        ) from error


def validate_prompt(
    prompt: Any,
    source_path: Path,
    position: int,
) -> dict[str, Any]:
    """Validate one evaluation prompt."""

    if not isinstance(prompt, dict):
        raise RuntimeError(
            f"{source_path}: prompt {position} must be an object."
        )

    missing_fields = REQUIRED_FIELDS - set(prompt)

    if missing_fields:
        raise RuntimeError(
            f"{source_path}: prompt {position} is missing fields: "
            f"{sorted(missing_fields)}"
        )

    prompt_id = prompt["id"]

    if not isinstance(prompt_id, str) or not prompt_id.strip():
        raise RuntimeError(
            f"{source_path}: prompt {position} has an invalid ID."
        )

    language = prompt["language"]

    if language not in EXPECTED_LANGUAGES:
        raise RuntimeError(
            f"{source_path}: {prompt_id} has unsupported language "
            f"{language!r}."
        )

    category = prompt["category"]

    if category not in EXPECTED_CATEGORIES_PER_LANGUAGE:
        raise RuntimeError(
            f"{source_path}: {prompt_id} has unsupported category "
            f"{category!r}."
        )

    prompt_text = prompt["prompt"]

    if not isinstance(prompt_text, str) or not prompt_text.strip():
        raise RuntimeError(
            f"{source_path}: {prompt_id} has empty prompt text."
        )

    expected_behaviors = prompt["expected_behaviors"]

    if not isinstance(expected_behaviors, list):
        raise RuntimeError(
            f"{source_path}: {prompt_id} expected_behaviors "
            "must be an array."
        )

    if len(expected_behaviors) < 3:
        raise RuntimeError(
            f"{source_path}: {prompt_id} must contain at least "
            "three expected behaviors."
        )

    for behavior_index, behavior in enumerate(
        expected_behaviors,
        start=1,
    ):
        if not isinstance(behavior, str) or not behavior.strip():
            raise RuntimeError(
                f"{source_path}: {prompt_id} expected behavior "
                f"{behavior_index} is invalid."
            )

    return prompt


def validate_distribution(
    prompts: list[dict[str, Any]],
) -> None:
    """Validate language and category distribution."""

    language_counts = Counter(
        prompt["language"]
        for prompt in prompts
    )

    for language, expected_count in EXPECTED_LANGUAGES.items():
        actual_count = language_counts[language]

        if actual_count != expected_count:
            raise RuntimeError(
                f"Language {language} contains {actual_count} prompts; "
                f"expected {expected_count}."
            )

    for language in EXPECTED_LANGUAGES:
        language_prompts = [
            prompt
            for prompt in prompts
            if prompt["language"] == language
        ]

        category_counts = Counter(
            prompt["category"]
            for prompt in language_prompts
        )

        for category, expected_count in (
            EXPECTED_CATEGORIES_PER_LANGUAGE.items()
        ):
            actual_count = category_counts[category]

            if actual_count != expected_count:
                raise RuntimeError(
                    f"Language {language}, category {category}: "
                    f"{actual_count} prompts; expected "
                    f"{expected_count}."
                )


def main() -> int:
    """Build the complete evaluation dataset."""

    combined_prompts: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for source_path in SOURCE_FILES:
        source_data = load_json(source_path)

        if not isinstance(source_data, list):
            raise RuntimeError(
                f"{source_path} must contain a JSON array."
            )

        for position, raw_prompt in enumerate(
            source_data,
            start=1,
        ):
            prompt = validate_prompt(
                raw_prompt,
                source_path,
                position,
            )

            prompt_id = prompt["id"]

            if prompt_id in seen_ids:
                raise RuntimeError(
                    f"Duplicate prompt ID: {prompt_id}"
                )

            seen_ids.add(prompt_id)
            combined_prompts.append(prompt)

    if len(combined_prompts) != 60:
        raise RuntimeError(
            f"The combined dataset contains "
            f"{len(combined_prompts)} prompts; expected 60."
        )

    validate_distribution(combined_prompts)

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = OUTPUT_FILE.with_suffix(".json.tmp")

    with temporary_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            combined_prompts,
            file,
            ensure_ascii=False,
            indent=2,
        )
        file.write("\n")

    temporary_path.replace(OUTPUT_FILE)

    print("Full dataset created successfully.")
    print(f"Output: {OUTPUT_FILE}")
    print(f"Total prompts: {len(combined_prompts)}")

    language_counts = Counter(
        prompt["language"]
        for prompt in combined_prompts
    )

    for language in ("en", "fr", "ar"):
        print(f"{language}: {language_counts[language]}")

        language_prompts = [
            prompt
            for prompt in combined_prompts
            if prompt["language"] == language
        ]

        category_counts = Counter(
            prompt["category"]
            for prompt in language_prompts
        )

        for category in EXPECTED_CATEGORIES_PER_LANGUAGE:
            print(
                f"  {category}: "
                f"{category_counts[category]}"
            )

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
