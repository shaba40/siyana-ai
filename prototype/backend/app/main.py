#!/usr/bin/env python3

"""
Siyana AI local prototype backend.

Responsibilities:

1. Start the local llama.cpp server.
2. Serve the HTML/CSS/JavaScript frontend.
3. Expose a local API for industrial-maintenance questions.
4. Send prompts to Qwen3-4B through llama-server.
5. Keep all inference on the local computer.
6. Stop the model server when the application closes.

This Phase 4A version does not yet import machine manuals.
Local document retrieval will be added in Phase 4B.
"""

from __future__ import annotations
from prototype.backend.app.rag_api import router as rag_router
import asyncio
import json
import os
import signal
import subprocess
import time
import urllib.error
import urllib.request
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parents[3]

FRONTEND_DIR = PROJECT_DIR / "prototype" / "frontend"

MODEL_PATH = (
    PROJECT_DIR
    / "model"
    / "Qwen3-4B-Q4_K_M.gguf"
)

LLAMA_SERVER_PATH = (
    PROJECT_DIR
    / ".venv"
    / "bin"
    / "llama-server"
)

SYSTEM_PROMPT_PATH = (
    PROJECT_DIR
    / "config"
    / "system_prompt.txt"
)

LLAMA_HOST = "127.0.0.1"
LLAMA_PORT = 8080
LLAMA_BASE_URL = f"http://{LLAMA_HOST}:{LLAMA_PORT}"

LLAMA_CONTEXT_SIZE = 4096
LLAMA_THREADS = 4
LLAMA_STARTUP_TIMEOUT_SECONDS = 180
LLAMA_RESPONSE_TIMEOUT_SECONDS = 360

MAX_GENERATED_TOKENS = 600
DEFAULT_TEMPERATURE = 0.2


# ---------------------------------------------------------------------------
# Runtime state
# ---------------------------------------------------------------------------

runtime: dict[str, Any] = {
    "llama_process": None,
    "llama_log_file": None,
    "started_by_application": False,
}


# ---------------------------------------------------------------------------
# API models
# ---------------------------------------------------------------------------

SupportedLanguage = Literal["en", "fr", "ar"]


class ChatRequest(BaseModel):
    """Request submitted by the local Siyana AI interface."""

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


class ChatResponse(BaseModel):
    """Response returned to the local interface."""

    answer: str
    language: SupportedLanguage
    duration_seconds: float
    model: str
    offline: bool
    safety_notice: str


class HealthResponse(BaseModel):
    """Application and model-server health information."""

    application: str
    model_server: str
    model_file_exists: bool
    offline_inference: bool


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------

def load_system_prompt() -> str:
    """Load the Phase 3 safety-focused system prompt."""

    if not SYSTEM_PROMPT_PATH.exists():
        raise RuntimeError(
            f"System prompt was not found: {SYSTEM_PROMPT_PATH}"
        )

    return SYSTEM_PROMPT_PATH.read_text(
        encoding="utf-8"
    ).strip()


def validate_required_files() -> None:
    """Ensure required runtime files exist."""

    missing: list[str] = []

    if not MODEL_PATH.exists():
        missing.append(f"GGUF model: {MODEL_PATH}")

    if not LLAMA_SERVER_PATH.exists():
        missing.append(
            f"llama-server executable: {LLAMA_SERVER_PATH}"
        )

    if not SYSTEM_PROMPT_PATH.exists():
        missing.append(
            f"System prompt: {SYSTEM_PROMPT_PATH}"
        )

    if not FRONTEND_DIR.exists():
        missing.append(
            f"Frontend directory: {FRONTEND_DIR}"
        )

    if missing:
        formatted = "\n".join(
            f"- {item}"
            for item in missing
        )

        raise RuntimeError(
            "Required Siyana AI files are missing:\n"
            f"{formatted}"
        )

    if not os.access(LLAMA_SERVER_PATH, os.X_OK):
        raise RuntimeError(
            "llama-server exists but is not executable: "
            f"{LLAMA_SERVER_PATH}"
        )


def request_json(
    url: str,
    *,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    timeout: int = 30,
) -> dict[str, Any]:
    """Send a JSON request to the local llama.cpp server."""

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
            f"Local model server returned HTTP "
            f"{error.code}: {body}"
        ) from error

    except urllib.error.URLError as error:
        raise RuntimeError(
            "Unable to communicate with the local "
            f"model server: {error.reason}"
        ) from error

    except json.JSONDecodeError as error:
        raise RuntimeError(
            "The local model server returned invalid JSON."
        ) from error


def model_server_is_ready() -> bool:
    """Return True when the local llama-server is healthy."""

    try:
        result = request_json(
            f"{LLAMA_BASE_URL}/health",
            timeout=3,
        )
    except RuntimeError:
        return False

    status = str(
        result.get("status", "")
    ).lower()

    return status in {"ok", "ready"}


# ---------------------------------------------------------------------------
# llama.cpp process management
# ---------------------------------------------------------------------------

def build_llama_server_command() -> list[str]:
    """Build the local llama-server command."""

    return [
        str(LLAMA_SERVER_PATH),
        "-m",
        str(MODEL_PATH),
        "--host",
        LLAMA_HOST,
        "--port",
        str(LLAMA_PORT),
        "-c",
        str(LLAMA_CONTEXT_SIZE),
        "-t",
        str(LLAMA_THREADS),
        "--jinja",
    ]


def start_llama_server() -> None:
    """Start llama-server unless it is already running."""

    if model_server_is_ready():
        print(
            "An existing llama-server instance is ready. "
            "The application will reuse it."
        )

        runtime["started_by_application"] = False
        return

    log_path = (
        PROJECT_DIR
        / "prototype"
        / "backend"
        / "llama-server.log"
    )

    log_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    log_file = log_path.open(
        "w",
        encoding="utf-8",
        buffering=1,
    )

    command = build_llama_server_command()

    print("Starting local llama-server:")
    print(" ".join(command))
    print(f"Model-server log: {log_path}")

    process = subprocess.Popen(
        command,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        text=True,
        start_new_session=True,
    )

    runtime["llama_process"] = process
    runtime["llama_log_file"] = log_file
    runtime["started_by_application"] = True

    deadline = (
        time.monotonic()
        + LLAMA_STARTUP_TIMEOUT_SECONDS
    )

    while time.monotonic() < deadline:
        return_code = process.poll()

        if return_code is not None:
            raise RuntimeError(
                "llama-server stopped before becoming ready. "
                f"Exit code: {return_code}. "
                f"Review: {log_path}"
            )

        if model_server_is_ready():
            print("Local Qwen3-4B model server is ready.")
            return

        time.sleep(2)

    raise RuntimeError(
        "llama-server did not become ready within "
        f"{LLAMA_STARTUP_TIMEOUT_SECONDS} seconds. "
        f"Review: {log_path}"
    )


def stop_llama_server() -> None:
    """Stop llama-server if this application started it."""

    process = runtime.get("llama_process")

    if not runtime.get("started_by_application"):
        return

    if process is None:
        return

    if process.poll() is not None:
        return

    print("Stopping local llama-server...")

    try:
        os.killpg(
            os.getpgid(process.pid),
            signal.SIGTERM,
        )

        process.wait(timeout=15)

    except subprocess.TimeoutExpired:
        os.killpg(
            os.getpgid(process.pid),
            signal.SIGKILL,
        )

        process.wait(timeout=5)

    except ProcessLookupError:
        pass

    log_file = runtime.get("llama_log_file")

    if log_file is not None:
        log_file.close()


# ---------------------------------------------------------------------------
# Prompt preparation
# ---------------------------------------------------------------------------

def language_instruction(language: SupportedLanguage) -> str:
    """Return a strict response-language instruction."""

    instructions = {
        "en": "Respond only in English.",
        "fr": "Répondez uniquement en français.",
        "ar": "أجب باللغة العربية فقط.",
    }

    return instructions[language]


def build_user_message(request: ChatRequest) -> str:
    """Build the user message sent to Qwen3-4B."""

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

    lines.extend(
        [
            "",
            "Important:",
            (
                "Do not invent equipment-specific values, "
                "alarm meanings, diagnoses, or repair procedures."
            ),
            (
                "If essential information is missing, clearly "
                "identify what information is required."
            ),
        ]
    )

    return "\n".join(lines)


def extract_answer(response: dict[str, Any]) -> str:
    """Extract assistant text from the server response."""

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
            "The local model returned an unsupported "
            "response format."
        )

    answer = content.strip()

    if not answer:
        raise RuntimeError(
            "The local model returned an empty answer."
        )

    return answer


def localized_safety_notice(
    language: SupportedLanguage,
) -> str:
    """Return the interface safety notice."""

    notices = {
        "en": (
            "Preliminary guidance only. Follow the equipment "
            "manual and approved workplace procedures, and use "
            "qualified maintenance personnel."
        ),
        "fr": (
            "Conseils préliminaires uniquement. Respectez le "
            "manuel de l'équipement, les procédures approuvées "
            "et faites intervenir du personnel qualifié."
        ),
        "ar": (
            "هذه إرشادات أولية فقط. يجب اتباع دليل المعدة "
            "وإجراءات العمل المعتمدة والاستعانة بأشخاص مؤهلين."
        ),
    }

    return notices[language]


# ---------------------------------------------------------------------------
# FastAPI lifecycle
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start and stop the local model with the web application."""

    del app

    validate_required_files()

    await asyncio.to_thread(
        start_llama_server
    )

    try:
        yield
    finally:
        await asyncio.to_thread(
            stop_llama_server
        )


app = FastAPI(
    title="Siyana AI",
    description=(
        "Offline multilingual industrial-maintenance "
        "support prototype."
    ),
    version="0.1.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------

@app.get(
    "/api/health",
    response_model=HealthResponse,
)
async def health() -> HealthResponse:
    """Report application and model-server health."""

    ready = await asyncio.to_thread(
        model_server_is_ready
    )

    return HealthResponse(
        application="ready",
        model_server=(
            "ready"
            if ready
            else "unavailable"
        ),
        model_file_exists=MODEL_PATH.exists(),
        offline_inference=True,
    )


@app.post(
    "/api/chat",
    response_model=ChatResponse,
)
async def chat(
    request: ChatRequest,
) -> ChatResponse:
    """Generate one local industrial-support response."""

    if not model_server_is_ready():
        raise HTTPException(
            status_code=503,
            detail=(
                "The local model server is not ready. "
                "Review the backend terminal and model log."
            ),
        )

    system_prompt = load_system_prompt()
    user_message = build_user_message(request)

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
        "temperature": DEFAULT_TEMPERATURE,
        "max_tokens": MAX_GENERATED_TOKENS,
        "stream": False,
    }

    started = time.monotonic()

    try:
        response = await asyncio.to_thread(
            request_json,
            f"{LLAMA_BASE_URL}/v1/chat/completions",
            method="POST",
            payload=payload,
            timeout=LLAMA_RESPONSE_TIMEOUT_SECONDS,
        )

        answer = extract_answer(response)

    except RuntimeError as error:
        raise HTTPException(
            status_code=502,
            detail=str(error),
        ) from error

    duration = round(
        time.monotonic() - started,
        3,
    )

    return ChatResponse(
        answer=answer,
        language=request.language,
        duration_seconds=duration,
        model="Qwen3-4B Q4_K_M",
        offline=True,
        safety_notice=localized_safety_notice(
            request.language
        ),
    )

app.include_router(rag_router)

@app.get("/")
async def index() -> FileResponse:
    """Return the local application interface."""

    index_path = FRONTEND_DIR / "index.html"

    if not index_path.exists():
        raise HTTPException(
            status_code=500,
            detail="Frontend index.html was not found.",
        )

    return FileResponse(index_path)


# API routes must be defined before the root static mount.
app.mount(
    "/static",
    StaticFiles(directory=FRONTEND_DIR),
    name="static",
)
