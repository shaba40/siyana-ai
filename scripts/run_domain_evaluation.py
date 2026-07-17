#!/usr/bin/env python3

"""
Siyana AI domain evaluation runner.

This program:

1. Starts a local llama.cpp server.
2. Loads the Siyana AI system prompt.
3. Loads evaluation prompts from JSON.
4. Sends every prompt to Qwen3-4B.
5. Saves individual and combined results.
6. Measures response duration.
7. Resumes without repeating successful prompts.
8. Stops the local server when evaluation finishes.

The program uses only Python's standard library.
No cloud API or external inference service is used.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Default project configuration
# ---------------------------------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parent.parent

DEFAULT_MODEL_PATH = (
    PROJECT_DIR / "model" / "Qwen3-4B-Q4_K_M.gguf"
)

DEFAULT_SYSTEM_PROMPT_PATH = (
    PROJECT_DIR / "config" / "system_prompt.txt"
)

DEFAULT_PROMPTS_PATH = (
    PROJECT_DIR / "evaluation" / "domain" / "prompts-pilot.json"
)

DEFAULT_RESPONSE_DIR = (
    PROJECT_DIR / "evaluation" / "domain" / "responses"
)

DEFAULT_REPORT_DIR = (
    PROJECT_DIR / "evaluation" / "domain" / "reports"
)

DEFAULT_SERVER_PATH = (
    PROJECT_DIR / ".venv" / "bin" / "llama-server"
)

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8080
DEFAULT_CONTEXT_SIZE = 4096
DEFAULT_THREADS = 4
DEFAULT_MAX_TOKENS = 500
DEFAULT_TEMPERATURE = 0.2
DEFAULT_SERVER_TIMEOUT_SECONDS = 180
DEFAULT_RESPONSE_TIMEOUT_SECONDS = 300


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def utc_timestamp() -> str:
    """Return the current UTC timestamp in ISO 8601 format."""

    return datetime.now(timezone.utc).isoformat()


def print_section(title: str) -> None:
    """Print a visible terminal section heading."""

    line = "=" * 72
    print()
    print(line)
    print(title)
    print(line)


def load_text_file(path: Path) -> str:
    """Load a UTF-8 text file."""

    try:
        return path.read_text(encoding="utf-8").strip()
    except FileNotFoundError as error:
        raise RuntimeError(f"Required text file was not found: {path}") from error


def load_json_file(path: Path) -> Any:
    """Load a UTF-8 JSON file."""

    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError as error:
        raise RuntimeError(f"Required JSON file was not found: {path}") from error
    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"Invalid JSON in {path}: line {error.lineno}, "
            f"column {error.colno}: {error.msg}"
        ) from error


def write_json_file(path: Path, data: Any) -> None:
    """Write formatted UTF-8 JSON atomically."""

    path.parent.mkdir(parents=True, exist_ok=True)

    temporary_path = path.with_suffix(path.suffix + ".tmp")

    with temporary_path.open("w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2,
        )
        file.write("\n")

    temporary_path.replace(path)


def validate_prompt_dataset(prompts: Any) -> list[dict[str, Any]]:
    """Validate the structure of the prompt dataset."""

    if not isinstance(prompts, list):
        raise RuntimeError("The prompt dataset must be a JSON array.")

    if not prompts:
        raise RuntimeError("The prompt dataset is empty.")

    required_fields = {
        "id",
        "language",
        "category",
        "prompt",
        "expected_behaviors",
    }

    supported_languages = {"en", "fr", "ar"}
    seen_ids: set[str] = set()

    for index, prompt in enumerate(prompts, start=1):
        if not isinstance(prompt, dict):
            raise RuntimeError(
                f"Prompt number {index} must be a JSON object."
            )

        missing_fields = required_fields - set(prompt.keys())

        if missing_fields:
            raise RuntimeError(
                f"Prompt number {index} is missing fields: "
                f"{sorted(missing_fields)}"
            )

        prompt_id = prompt["id"]

        if not isinstance(prompt_id, str) or not prompt_id.strip():
            raise RuntimeError(
                f"Prompt number {index} has an invalid ID."
            )

        if prompt_id in seen_ids:
            raise RuntimeError(
                f"Duplicate prompt ID detected: {prompt_id}"
            )

        seen_ids.add(prompt_id)

        language = prompt["language"]

        if language not in supported_languages:
            raise RuntimeError(
                f"Prompt {prompt_id} has unsupported language: "
                f"{language}"
            )

        if not isinstance(prompt["category"], str):
            raise RuntimeError(
                f"Prompt {prompt_id} has an invalid category."
            )

        if not isinstance(prompt["prompt"], str) or not prompt["prompt"].strip():
            raise RuntimeError(
                f"Prompt {prompt_id} has empty prompt text."
            )

        expected_behaviors = prompt["expected_behaviors"]

        if not isinstance(expected_behaviors, list):
            raise RuntimeError(
                f"Prompt {prompt_id} expected_behaviors must be an array."
            )

        if not all(
            isinstance(item, str) and item.strip()
            for item in expected_behaviors
        ):
            raise RuntimeError(
                f"Prompt {prompt_id} has an invalid expected behavior."
            )

    return prompts


def validate_required_paths(
    model_path: Path,
    system_prompt_path: Path,
    prompts_path: Path,
    server_path: Path,
) -> None:
    """Validate that required files exist before starting evaluation."""

    required_files = {
        "GGUF model": model_path,
        "System prompt": system_prompt_path,
        "Prompt dataset": prompts_path,
        "llama-server": server_path,
    }

    missing: list[str] = []

    for label, path in required_files.items():
        if not path.exists():
            missing.append(f"{label}: {path}")

    if missing:
        message = "The following required files are missing:\n"
        message += "\n".join(f"- {item}" for item in missing)
        raise RuntimeError(message)

    if not os.access(server_path, os.X_OK):
        raise RuntimeError(
            f"llama-server exists but is not executable: {server_path}"
        )

def build_server_command(
    server_path: Path,
    model_path: Path,
    host: str,
    port: int,
    context_size: int,
    threads: int,
) -> list:
    """Build the llama-server command."""

    return [
        str(server_path),
        "-m",
        str(model_path),
        "--host",
        host,
        "--port",
        str(port),
        "-c",
        str(context_size),
        "-t",
        str(threads),
        "--jinja",
    ]
# ---------------------------------------------------------------------------
# Local llama.cpp server management
# ---------------------------------------------------------------------------

def start_server(
    command: list[str],
    log_path: Path,
) -> tuple[subprocess.Popen[str], Any]:
    """Start llama-server and send logs to a file."""

    log_path.parent.mkdir(parents=True, exist_ok=True)

    log_file = log_path.open(
        "w",
        encoding="utf-8",
        buffering=1,
    )

    print("Starting local llama.cpp server:")
    print(" ".join(command))
    print(f"Server log: {log_path}")

    process = subprocess.Popen(
        command,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        text=True,
        start_new_session=True,
    )

    return process, log_file


def stop_server(process: subprocess.Popen[str] | None) -> None:
    """Stop llama-server cleanly."""

    if process is None:
        return

    if process.poll() is not None:
        return

    print()
    print("Stopping local llama.cpp server...")

    try:
        os.killpg(
            os.getpgid(process.pid),
            signal.SIGTERM,
        )
        process.wait(timeout=15)
    except subprocess.TimeoutExpired:
        print("Server did not stop in time; terminating forcefully.")
        os.killpg(
            os.getpgid(process.pid),
            signal.SIGKILL,
        )
        process.wait(timeout=5)
    except ProcessLookupError:
        pass


def request_json(
    url: str,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    timeout: int = 30,
) -> dict[str, Any]:
    """Send a local HTTP request and decode a JSON response."""

    data: bytes | None = None

    headers = {
        "Accept": "application/json",
    }

    if payload is not None:
        data = json.dumps(
            payload,
            ensure_ascii=False,
        ).encode("utf-8")

        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(
        url=url,
        data=data,
        headers=headers,
        method=method,
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
            f"HTTP {error.code} from {url}: {body}"
        ) from error

    except urllib.error.URLError as error:
        raise RuntimeError(
            f"Unable to connect to local server at {url}: "
            f"{error.reason}"
        ) from error

    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"Server returned invalid JSON from {url}."
        ) from error


def wait_for_server(
    process: subprocess.Popen[str],
    base_url: str,
    timeout_seconds: int,
    log_path: Path,
) -> None:
    """Wait until llama-server reports that it is healthy."""

    health_url = f"{base_url}/health"
    deadline = time.monotonic() + timeout_seconds

    print(f"Waiting for server health endpoint: {health_url}")

    while time.monotonic() < deadline:
        return_code = process.poll()

        if return_code is not None:
            raise RuntimeError(
                "llama-server exited before becoming ready. "
                f"Exit code: {return_code}. "
                f"Review the server log: {log_path}"
            )

        try:
            response = request_json(
                health_url,
                timeout=5,
            )

            status = str(response.get("status", "")).lower()

            if status in {"ok", "ready"}:
                print("Local model server is ready.")
                return

        except RuntimeError:
            pass

        time.sleep(2)

    raise RuntimeError(
        "llama-server did not become ready within "
        f"{timeout_seconds} seconds. Review: {log_path}"
    )


# ---------------------------------------------------------------------------
# Prompt execution
# ---------------------------------------------------------------------------

def language_instruction(language: str) -> str:
    """Return a strict answer-language instruction."""

    instructions = {
        "en": "Respond only in English.",
        "fr": "Répondez uniquement en français.",
        "ar": "أجب باللغة العربية فقط.",
    }

    return instructions[language]


def build_user_message(prompt: dict[str, Any]) -> str:
    """Build the final user message for Qwen3 non-thinking mode."""

    instruction = language_instruction(prompt["language"])

    return (
        "/no_think\n\n"
        f"{instruction}\n\n"
        f"{prompt['prompt']}"
    )


def extract_assistant_content(response: dict[str, Any]) -> str:
    """Extract assistant text from the OpenAI-compatible response."""

    try:
        content = response["choices"][0]["message"]["content"]
    except (
        KeyError,
        IndexError,
        TypeError,
    ) as error:
        raise RuntimeError(
            "The server response did not contain "
            "choices[0].message.content."
        ) from error

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        text_parts: list[str] = []

        for item in content:
            if isinstance(item, dict):
                text = item.get("text")

                if isinstance(text, str):
                    text_parts.append(text)

        return "\n".join(text_parts).strip()

    raise RuntimeError(
        "The assistant response had an unsupported content format."
    )


def run_prompt(
    prompt: dict[str, Any],
    system_prompt: str,
    base_url: str,
    max_tokens: int,
    temperature: float,
    timeout_seconds: int,
) -> dict[str, Any]:
    """Run one evaluation prompt against the local model."""

    endpoint = f"{base_url}/v1/chat/completions"

    user_message = build_user_message(prompt)

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
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }

    started_at = utc_timestamp()
    start_time = time.monotonic()

    response = request_json(
        endpoint,
        method="POST",
        payload=payload,
        timeout=timeout_seconds,
    )

    duration_seconds = time.monotonic() - start_time
    completed_at = utc_timestamp()

    assistant_response = extract_assistant_content(response)

    usage = response.get("usage", {})

    return {
        "prompt_id": prompt["id"],
        "language": prompt["language"],
        "category": prompt["category"],
        "prompt": prompt["prompt"],
        "expected_behaviors": prompt["expected_behaviors"],
        "user_message_sent": user_message,
        "response": assistant_response,
        "status": "success",
        "started_at": started_at,
        "completed_at": completed_at,
        "duration_seconds": round(duration_seconds, 3),
        "usage": usage,
        "model_configuration": {
            "base_model": "Qwen3-4B",
            "model_file": "Qwen3-4B-Q4_K_M.gguf",
            "quantization": "GGUF Q4_K_M",
            "runtime": "llama.cpp",
            "temperature": temperature,
            "max_tokens": max_tokens,
            "thinking_mode": "disabled using /no_think",
        },
    }


def create_error_result(
    prompt: dict[str, Any],
    error: Exception,
) -> dict[str, Any]:
    """Create a structured result when a prompt fails."""

    return {
        "prompt_id": prompt["id"],
        "language": prompt["language"],
        "category": prompt["category"],
        "prompt": prompt["prompt"],
        "expected_behaviors": prompt["expected_behaviors"],
        "response": "",
        "status": "error",
        "error_type": type(error).__name__,
        "error_message": str(error),
        "completed_at": utc_timestamp(),
    }


def existing_successful_result(path: Path) -> bool:
    """Return True when an existing result completed successfully."""

    if not path.exists():
        return False

    try:
        result = load_json_file(path)
    except RuntimeError:
        return False

    return result.get("status") == "success"


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def load_all_results(
    prompts: list[dict[str, Any]],
    response_dir: Path,
) -> list[dict[str, Any]]:
    """Load results in the same order as the prompt dataset."""

    results: list[dict[str, Any]] = []

    for prompt in prompts:
        result_path = response_dir / f"{prompt['id']}.json"

        if result_path.exists():
            result = load_json_file(result_path)
            results.append(result)

    return results


def create_summary(
    prompts: list[dict[str, Any]],
    results: list[dict[str, Any]],
    started_at: str,
    completed_at: str,
) -> dict[str, Any]:
    """Build the combined evaluation summary."""

    successful = [
        result
        for result in results
        if result.get("status") == "success"
    ]

    failed = [
        result
        for result in results
        if result.get("status") != "success"
    ]

    language_counts: dict[str, dict[str, int]] = {}

    for language in ("en", "fr", "ar"):
        language_results = [
            result
            for result in results
            if result.get("language") == language
        ]

        language_counts[language] = {
            "total": len(language_results),
            "successful": sum(
                result.get("status") == "success"
                for result in language_results
            ),
            "failed": sum(
                result.get("status") != "success"
                for result in language_results
            ),
        }

    category_counts: dict[str, dict[str, int]] = {}

    categories = sorted(
        {
            prompt["category"]
            for prompt in prompts
        }
    )

    for category in categories:
        category_results = [
            result
            for result in results
            if result.get("category") == category
        ]

        category_counts[category] = {
            "total": len(category_results),
            "successful": sum(
                result.get("status") == "success"
                for result in category_results
            ),
            "failed": sum(
                result.get("status") != "success"
                for result in category_results
            ),
        }

    durations = [
        result["duration_seconds"]
        for result in successful
        if isinstance(
            result.get("duration_seconds"),
            (int, float),
        )
    ]

    average_duration = (
        round(sum(durations) / len(durations), 3)
        if durations
        else None
    )

    return {
        "project": "Siyana AI",
        "phase": "Phase 3 domain-evaluation pilot",
        "model": {
            "base_model": "Qwen3-4B",
            "model_file": "Qwen3-4B-Q4_K_M.gguf",
            "quantization": "GGUF Q4_K_M",
            "runtime": "llama.cpp",
            "license": "Apache 2.0",
        },
        "started_at": started_at,
        "completed_at": completed_at,
        "prompt_count": len(prompts),
        "result_count": len(results),
        "successful_count": len(successful),
        "failed_count": len(failed),
        "average_duration_seconds": average_duration,
        "language_counts": language_counts,
        "category_counts": category_counts,
        "results": results,
    }


def create_review_markdown(
    summary: dict[str, Any],
    review_path: Path,
) -> None:
    """Create a Markdown file for manual answer scoring."""

    lines: list[str] = []

    lines.append("# Siyana AI Pilot Evaluation Review")
    lines.append("")
    lines.append("## Run summary")
    lines.append("")
    lines.append(
        f"- Prompts: {summary['prompt_count']}"
    )
    lines.append(
        f"- Successful: {summary['successful_count']}"
    )
    lines.append(
        f"- Failed: {summary['failed_count']}"
    )
    lines.append(
        "- Average response duration: "
        f"{summary['average_duration_seconds']} seconds"
    )
    lines.append("")

    for result in summary["results"]:
        lines.append("---")
        lines.append("")
        lines.append(
            f"## {result['prompt_id']} — "
            f"{result['language']} — "
            f"{result['category']}"
        )
        lines.append("")
        lines.append("### Prompt")
        lines.append("")
        lines.append(result["prompt"])
        lines.append("")
        lines.append("### Expected behaviors")
        lines.append("")

        for behavior in result["expected_behaviors"]:
            lines.append(f"- [ ] {behavior}")

        lines.append("")
        lines.append("### Model response")
        lines.append("")

        if result.get("status") == "success":
            lines.append(result["response"])
        else:
            lines.append(
                f"ERROR: {result.get('error_message', 'Unknown error')}"
            )

        lines.append("")
        lines.append("### Manual quality scores")
        lines.append("")
        lines.append("- Technical correctness (0–5):")
        lines.append("- Instruction following (0–5):")
        lines.append("- Safety (0–5):")
        lines.append("- Clarity (0–5):")
        lines.append("- Language quality (0–5):")
        lines.append("- Uncertainty handling (0–5):")
        lines.append("- Total (0–30):")
        lines.append("- Pass / Review / Fail:")
        lines.append("- Hallucination observed:")
        lines.append("- Reviewer notes:")
        lines.append("")

    review_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    review_path.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Command-line interface
# ---------------------------------------------------------------------------

def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description=(
            "Run Siyana AI industrial-maintenance prompts "
            "against the local Qwen3-4B GGUF model."
        )
    )

    parser.add_argument(
        "--model",
        type=Path,
        default=DEFAULT_MODEL_PATH,
        help=f"GGUF model path. Default: {DEFAULT_MODEL_PATH}",
    )

    parser.add_argument(
        "--server",
        type=Path,
        default=DEFAULT_SERVER_PATH,
        help=f"llama-server executable. Default: {DEFAULT_SERVER_PATH}",
    )

    parser.add_argument(
        "--system-prompt",
        type=Path,
        default=DEFAULT_SYSTEM_PROMPT_PATH,
        help=(
            "System prompt path. "
            f"Default: {DEFAULT_SYSTEM_PROMPT_PATH}"
        ),
    )

    parser.add_argument(
        "--prompts",
        type=Path,
        default=DEFAULT_PROMPTS_PATH,
        help=f"Prompt dataset path. Default: {DEFAULT_PROMPTS_PATH}",
    )

    parser.add_argument(
        "--responses",
        type=Path,
        default=DEFAULT_RESPONSE_DIR,
        help=f"Individual result directory. Default: {DEFAULT_RESPONSE_DIR}",
    )

    parser.add_argument(
        "--reports",
        type=Path,
        default=DEFAULT_REPORT_DIR,
        help=f"Report directory. Default: {DEFAULT_REPORT_DIR}",
    )

    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help=f"Local server host. Default: {DEFAULT_HOST}",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Local server port. Default: {DEFAULT_PORT}",
    )

    parser.add_argument(
        "--context-size",
        type=int,
        default=DEFAULT_CONTEXT_SIZE,
        help=(
            "llama.cpp context size. "
            f"Default: {DEFAULT_CONTEXT_SIZE}"
        ),
    )

    parser.add_argument(
        "--threads",
        type=int,
        default=DEFAULT_THREADS,
        help=f"llama.cpp CPU threads. Default: {DEFAULT_THREADS}",
    )

    parser.add_argument(
        "--max-tokens",
        type=int,
        default=DEFAULT_MAX_TOKENS,
        help=(
            "Maximum generated tokens per prompt. "
            f"Default: {DEFAULT_MAX_TOKENS}"
        ),
    )

    parser.add_argument(
        "--temperature",
        type=float,
        default=DEFAULT_TEMPERATURE,
        help=(
            "Generation temperature. "
            f"Default: {DEFAULT_TEMPERATURE}"
        ),
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Repeat prompts that already completed successfully.",
    )

    parser.add_argument(
        "--keep-server",
        action="store_true",
        help="Keep llama-server alive after evaluation.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help=(
            "Run only the first N prompts from the selected dataset. "
            "Useful for smoke testing."
        ),
    )

    return parser.parse_args()


# ---------------------------------------------------------------------------
# Main program
# ---------------------------------------------------------------------------

def main() -> int:
    """Run the complete pilot evaluation."""

    arguments = parse_arguments()

    model_path = arguments.model.resolve()
    server_path = arguments.server.resolve()
    system_prompt_path = arguments.system_prompt.resolve()
    prompts_path = arguments.prompts.resolve()
    response_dir = arguments.responses.resolve()
    report_dir = arguments.reports.resolve()

    validate_required_paths(
        model_path=model_path,
        system_prompt_path=system_prompt_path,
        prompts_path=prompts_path,
        server_path=server_path,
    )

    system_prompt = load_text_file(system_prompt_path)

    prompts = validate_prompt_dataset(
        load_json_file(prompts_path)
    )
    if arguments.limit is not None:
        if arguments.limit < 1:
            raise RuntimeError("--limit must be greater than zero.")

        prompts = prompts[:arguments.limit]
    response_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    report_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    base_url = f"http://{arguments.host}:{arguments.port}"

    server_log_path = report_dir / "llama-server.log"

    combined_results_path = report_dir / "pilot-results.json"
    review_path = report_dir / "pilot-review.md"

    evaluation_started_at = utc_timestamp()

    print_section("Siyana AI Phase 3 Pilot Evaluation")

    print(f"Project directory: {PROJECT_DIR}")
    print(f"Model: {model_path}")
    print(f"Server: {server_path}")
    print(f"Prompt dataset: {prompts_path}")
    print(f"Prompt count: {len(prompts)}")
    print(f"Context size: {arguments.context_size}")
    print(f"Threads: {arguments.threads}")
    print(f"Maximum tokens: {arguments.max_tokens}")
    print(f"Temperature: {arguments.temperature}")

    server_command = build_server_command(
        server_path=server_path,
        model_path=model_path,
        host=arguments.host,
        port=arguments.port,
        context_size=arguments.context_size,
        threads=arguments.threads,
    )

    server_process: subprocess.Popen[str] | None = None
    server_log_file: Any = None

    try:
        server_process, server_log_file = start_server(
            command=server_command,
            log_path=server_log_path,
        )

        wait_for_server(
            process=server_process,
            base_url=base_url,
            timeout_seconds=DEFAULT_SERVER_TIMEOUT_SECONDS,
            log_path=server_log_path,
        )

        for index, prompt in enumerate(prompts, start=1):
            prompt_id = prompt["id"]
            result_path = response_dir / f"{prompt_id}.json"

            print_section(
                f"Prompt {index}/{len(prompts)}: "
                f"{prompt_id}"
            )

            print(f"Language: {prompt['language']}")
            print(f"Category: {prompt['category']}")

            if (
                not arguments.force
                and existing_successful_result(result_path)
            ):
                print("Skipping: successful result already exists.")
                continue

            try:
                result = run_prompt(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    base_url=base_url,
                    max_tokens=arguments.max_tokens,
                    temperature=arguments.temperature,
                    timeout_seconds=DEFAULT_RESPONSE_TIMEOUT_SECONDS,
                )

                write_json_file(
                    result_path,
                    result,
                )

                print(
                    "Status: success | "
                    f"Duration: {result['duration_seconds']} seconds"
                )

                print()
                print("Response preview:")
                print(result["response"][:500])

                if len(result["response"]) > 500:
                    print("...")

            except Exception as error:
                result = create_error_result(
                    prompt=prompt,
                    error=error,
                )

                write_json_file(
                    result_path,
                    result,
                )

                print(f"Status: error | {error}")

        evaluation_completed_at = utc_timestamp()

        results = load_all_results(
            prompts=prompts,
            response_dir=response_dir,
        )

        summary = create_summary(
            prompts=prompts,
            results=results,
            started_at=evaluation_started_at,
            completed_at=evaluation_completed_at,
        )

        write_json_file(
            combined_results_path,
            summary,
        )

        create_review_markdown(
            summary=summary,
            review_path=review_path,
        )

        print_section("Evaluation completed")

        print(f"Total prompts: {summary['prompt_count']}")
        print(f"Successful: {summary['successful_count']}")
        print(f"Failed: {summary['failed_count']}")
        print(
            "Average duration: "
            f"{summary['average_duration_seconds']} seconds"
        )
        print(f"Combined results: {combined_results_path}")
        print(f"Manual review file: {review_path}")
        print(f"Server log: {server_log_path}")

        if summary["failed_count"] > 0:
            print()
            print(
                "WARNING: One or more prompts failed. "
                "Review the error results and server log."
            )
            return 1

        return 0

    finally:
        if not arguments.keep_server:
            stop_server(server_process)

        if server_log_file is not None:
            server_log_file.close()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print()
        print("Evaluation interrupted by user.")
        raise SystemExit(130)
    except RuntimeError as error:
        print()
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
