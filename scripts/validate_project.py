#!/usr/bin/env python3

"""
Validate the local Siyana AI repository before profiling or submission.

This script checks:

- Required project files
- Python and shell syntax
- JSON validity
- Frontend resource references
- GGUF presence and Git exclusion
- Local runtime dependencies
- SQLite FTS5 availability
- Forbidden placeholder values
- Accidental secret-like Hugging Face tokens

The script does not start llama-server or perform inference.
"""

from __future__ import annotations

import json
import re
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Sequence


PROJECT_DIR = Path(__file__).resolve().parent.parent


REQUIRED_FILES = [
    Path(".gitignore"),
    Path("metadata.json"),
    Path("download_model.sh"),
    Path("REPORT.md"),
    Path("requirements-prototype.txt"),
    Path("config/system_prompt.txt"),
    Path("model/Qwen3-4B-Q4_K_M.gguf"),
    Path("prototype/backend/app/main.py"),
    Path("prototype/backend/app/document_store.py"),
    Path("prototype/backend/app/rag_api.py"),
    Path("prototype/frontend/index.html"),
    Path("prototype/frontend/styles.css"),
    Path("prototype/frontend/app.js"),
    Path("scripts/start_siyana.sh"),
    Path("scripts/stop_siyana.sh"),
]


PYTHON_FILES = [
    Path("prototype/backend/app/main.py"),
    Path("prototype/backend/app/document_store.py"),
    Path("prototype/backend/app/rag_api.py"),
    Path("scripts/run_domain_evaluation.py"),
    Path("scripts/build_full_dataset.py"),
    Path("scripts/analyze_evaluation_scores.py"),
]


SHELL_FILES = [
    Path("download_model.sh"),
    Path("scripts/start_siyana.sh"),
    Path("scripts/stop_siyana.sh"),
]


JSON_FILES = [
    Path("metadata.json"),
    Path("evaluation/domain/prompts-pilot.json"),
    Path("evaluation/domain/prompts-full.json"),
]


PLACEHOLDER_PATTERNS = [
    r"your-team-id",
    r"your-name",
    r"your-email",
    r"your-github",
    r"YourModel",
    r"your-model\.gguf",
    r"Brief description",
]


def print_result(
    passed: bool,
    label: str,
    detail: str = "",
) -> None:
    """Print one validation result."""

    marker = "PASS" if passed else "FAIL"

    line = f"[{marker}] {label}"

    if detail:
        line += f": {detail}"

    print(line)


def run_command(
    command: Sequence[str],
) -> tuple[bool, str]:
    """Run a local validation command."""

    result = subprocess.run(
        command,
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        check=False,
    )

    output = "\n".join(
        part.strip()
        for part in (
            result.stdout,
            result.stderr,
        )
        if part.strip()
    )

    return result.returncode == 0, output


def validate_required_files() -> list:
    """Check required project files."""

    failures: list[str] = []

    for relative_path in REQUIRED_FILES:
        absolute_path = PROJECT_DIR / relative_path
        exists = absolute_path.is_file()

        print_result(
            exists,
            f"Required file {relative_path}",
        )

        if not exists:
            failures.append(
                f"Missing file: {relative_path}"
            )

    return failures


def validate_python_files() -> list:
    """Compile Python sources without executing them."""

    failures: list[str] = []

    existing_files = [
        str(path)
        for path in PYTHON_FILES
        if (PROJECT_DIR / path).is_file()
    ]

    if not existing_files:
        failures.append(
            "No Python files were available for syntax validation."
        )

        return failures

    passed, output = run_command(
        [
            sys.executable,
            "-m",
            "py_compile",
            *existing_files,
        ]
    )

    print_result(
        passed,
        "Python syntax",
        output if not passed else "",
    )

    if not passed:
        failures.append(
            f"Python syntax failure: {output}"
        )

    return failures


def validate_shell_files() -> list:
    """Validate Bash syntax."""

    failures: list[str] = []

    for relative_path in SHELL_FILES:
        absolute_path = PROJECT_DIR / relative_path

        if not absolute_path.is_file():
            continue

        passed, output = run_command(
            [
                "bash",
                "-n",
                str(relative_path),
            ]
        )

        print_result(
            passed,
            f"Bash syntax {relative_path}",
            output if not passed else "",
        )

        if not passed:
            failures.append(
                f"Bash syntax failure in {relative_path}: "
                f"{output}"
            )

    return failures


def validate_json_files() -> list:
    """Parse the required JSON documents."""

    failures: list[str] = []

    for relative_path in JSON_FILES:
        absolute_path = PROJECT_DIR / relative_path

        if not absolute_path.is_file():
            continue

        try:
            with absolute_path.open(
                encoding="utf-8"
            ) as file:
                json.load(file)

            print_result(
                True,
                f"JSON validity {relative_path}",
            )

        except (
            OSError,
            json.JSONDecodeError,
        ) as error:
            print_result(
                False,
                f"JSON validity {relative_path}",
                str(error),
            )

            failures.append(
                f"Invalid JSON in {relative_path}: {error}"
            )

    return failures


def validate_frontend() -> list:
    """Check frontend files and resource references."""

    failures: list[str] = []

    html_path = (
        PROJECT_DIR
        / "prototype"
        / "frontend"
        / "index.html"
    )

    css_path = (
        PROJECT_DIR
        / "prototype"
        / "frontend"
        / "styles.css"
    )

    js_path = (
        PROJECT_DIR
        / "prototype"
        / "frontend"
        / "app.js"
    )

    if html_path.is_file():
        html = html_path.read_text(
            encoding="utf-8"
        )

        checks = {
            "HTML stylesheet reference":
                'href="/static/styles.css"',
            "HTML JavaScript reference":
                'src="/static/app.js"',
            "HTML chat form":
                'id="chatForm"',
            "HTML manual input":
                'id="manualFile"',
            "HTML citation list":
                'id="citationList"',
        }

        for label, expected in checks.items():
            passed = expected in html

            print_result(
                passed,
                label,
            )

            if not passed:
                failures.append(
                    f"{label} is missing."
                )

        escaped = bool(
            re.search(
                r"&lt;|&gt;|```html|<br\s*/?>",
                html,
                flags=re.IGNORECASE,
            )
        )

        print_result(
            not escaped,
            "HTML is not escaped or Markdown-wrapped",
        )

        if escaped:
            failures.append(
                "index.html contains escaped HTML, "
                "Markdown fences, or copied line breaks."
            )

        if css_path.is_file():
            css = css_path.read_text(
                encoding="utf-8"
            )

            balanced = (
                css.count("{")
                == css.count("}")
                and bool(css.strip())
            )

            print_result(
                balanced,
                "CSS brace balance",
            )

            if not balanced:
                failures.append(
                    "styles.css is empty or has unbalanced braces."
                )

    if js_path.is_file():
        node = shutil.which("node")

        if node:
            passed, output = run_command(
                [
                    node,
                    "--check",
                    str(
                        js_path.relative_to(
                            PROJECT_DIR
                        )
                    ),
                ]
            )

            print_result(
                passed,
                "JavaScript syntax",
                output if not passed else "",
            )

            if not passed:
                failures.append(
                    f"JavaScript syntax failure: {output}"
                )

        else:
            print_result(
                True,
                "JavaScript syntax",
                "Skipped because Node.js is unavailable",
            )

    return failures


def validate_model_and_git() -> list:
    """Check the local GGUF and Git exclusion."""

    failures: list[str] = []

    model_relative = Path(
        "model/Qwen3-4B-Q4_K_M.gguf"
    )

    model_path = PROJECT_DIR / model_relative

    if model_path.is_file():
        size_bytes = model_path.stat().st_size

        plausible = size_bytes > 1_000_000_000

        print_result(
            plausible,
            "GGUF file size",
            f"{size_bytes / (1024 ** 3):.2f} GiB",
        )

        if not plausible:
            failures.append(
                "The GGUF file is unexpectedly small."
            )

    passed, output = run_command(
        [
            "git",
            "check-ignore",
            "-v",
            str(model_relative),
        ]
    )

    print_result(
        passed,
        "GGUF is excluded from Git",
        output if passed else "",
    )

    if not passed:
        failures.append(
            "The GGUF model is not excluded by .gitignore."
        )

    passed, output = run_command(
        [
            "git",
            "ls-files",
            "*.gguf",
        ]
    )

    no_tracked_models = (
        passed
        and not output.strip()
    )

    print_result(
        no_tracked_models,
        "No GGUF model is tracked by Git",
        output if not no_tracked_models else "",
    )

    if not no_tracked_models:
        failures.append(
            "One or more GGUF files are tracked by Git."
        )

    return failures


def validate_runtime() -> list:
    """Check required local programs and SQLite FTS5."""

    failures: list[str] = []

    commands = [
        "python",
        "llama-cli",
        "llama-server",
        "llama-bench",
        "adtc-profiler",
    ]

    for name in commands:
        location = shutil.which(name)
        passed = location is not None

        print_result(
            passed,
            f"Runtime command {name}",
            location or "",
        )

        if not passed:
            failures.append(
                f"Required command is unavailable: {name}"
            )

    try:
        connection = sqlite3.connect(":memory:")

        connection.execute(
            "CREATE VIRTUAL TABLE test_fts "
            "USING fts5(content)"
        )

        connection.close()

        print_result(
            True,
            "SQLite FTS5",
        )

    except sqlite3.Error as error:
        print_result(
            False,
            "SQLite FTS5",
            str(error),
        )

        failures.append(
            f"SQLite FTS5 is unavailable: {error}"
        )

    return failures


def validate_metadata() -> list:
    """Check metadata structure and placeholders."""

    failures: list[str] = []

    metadata_path = PROJECT_DIR / "metadata.json"

    if not metadata_path.is_file():
        return failures

    text = metadata_path.read_text(
        encoding="utf-8"
    )

    placeholder_matches: list[str] = []

    for pattern in PLACEHOLDER_PATTERNS:
        if re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        ):
            placeholder_matches.append(
                pattern
            )

    no_placeholders = not placeholder_matches

    print_result(
        no_placeholders,
        "metadata.json has no known placeholders",
        (
            ", ".join(placeholder_matches)
            if placeholder_matches
            else ""
        ),
    )

    if placeholder_matches:
        failures.append(
            "metadata.json still contains placeholders."
        )

    try:
        metadata = json.loads(text)
    except json.JSONDecodeError:
        return failures

    test_prompts = metadata.get(
        "test_prompts",
        []
    )

    exactly_two = (
        isinstance(test_prompts, list)
        and len(test_prompts) == 2
    )

    print_result(
        exactly_two,
        "metadata.json contains exactly two test prompts",
        (
            str(len(test_prompts))
            if isinstance(test_prompts, list)
            else "not an array"
        ),
    )

    if not exactly_two:
        failures.append(
            "metadata.json must contain exactly two test prompts."
        )

    runtime = metadata.get(
        "_runtime",
        {}
    )

    expected_model_path = (
        "model/Qwen3-4B-Q4_K_M.gguf"
    )

    correct_model_path = (
        isinstance(runtime, dict)
        and runtime.get("model_path")
        == expected_model_path
    )

    print_result(
        correct_model_path,
        "metadata model path",
        (
            str(runtime.get("model_path"))
            if isinstance(runtime, dict)
            else "missing"
        ),
    )

    if not correct_model_path:
        failures.append(
            "metadata.json has the wrong runtime model path."
        )

    return failures


def validate_secrets() -> list:
    """Search tracked text files for Hugging Face token patterns."""

    failures: list[str] = []

    passed, tracked_output = run_command(
        [
            "git",
            "ls-files",
        ]
    )

    if not passed:
        failures.append(
            "Unable to list tracked Git files."
        )

        return failures

    suspicious: list[str] = []

    for entry in tracked_output.splitlines():
        path = PROJECT_DIR / entry

        if not path.is_file():
            continue

        try:
            content = path.read_text(
                encoding="utf-8"
            )
        except (
            UnicodeDecodeError,
            OSError,
        ):
            continue

        if re.search(
            r"\bhf_[A-Za-z0-9]{20,}\b",
            content,
        ):
            suspicious.append(entry)

    clean = not suspicious

    print_result(
        clean,
        "No Hugging Face token pattern in tracked files",
        ", ".join(suspicious),
    )

    if suspicious:
        failures.append(
            "Potential Hugging Face token detected "
            "in tracked files."
        )

    return failures


def main() -> int:
    """Run every validation check."""

    print("=" * 72)
    print("Siyana AI project validation")
    print("=" * 72)
    print()

    failures: list[str] = []

    failures.extend(
        validate_required_files()
    )

    failures.extend(
        validate_python_files()
    )

    failures.extend(
        validate_shell_files()
    )

    failures.extend(
        validate_json_files()
    )

    failures.extend(
        validate_frontend()
    )

    failures.extend(
        validate_model_and_git()
    )

    failures.extend(
        validate_runtime()
    )

    failures.extend(
        validate_metadata()
    )

    failures.extend(
        validate_secrets()
    )

    print()
    print("=" * 72)

    if failures:
        print(
            f"Validation failed with "
            f"{len(failures)} issue(s):"
        )

        for failure in failures:
            print(f"- {failure}")

        print("=" * 72)
        return 1

    print("All Siyana AI validation checks passed.")
    print("=" * 72)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())