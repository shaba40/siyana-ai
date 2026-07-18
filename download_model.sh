#!/usr/bin/env bash

set -euo pipefail

MODEL_DIRECTORY="model"
MODEL_FILENAME="Qwen3-4B-Q4_K_M.gguf"
MODEL_PATH="${MODEL_DIRECTORY}/${MODEL_FILENAME}"

MODEL_URL="https://huggingface.co/Qwen/Qwen3-4B-GGUF/resolve/main/Qwen3-4B-Q4_K_M.gguf?download=true"

EXPECTED_SHA256="7485fe6f11af29433bc51cab58009521f205840f5b4ae3a32fa7f92e8534fdf5"

mkdir -p "$MODEL_DIRECTORY"

verify_model() {
    local actual_sha256

    actual_sha256="$(
        sha256sum "$MODEL_PATH" |
        awk '{print $1}'
    )"

    if [ "$actual_sha256" != "$EXPECTED_SHA256" ]; then
        echo "ERROR: Model checksum verification failed."
        echo "Expected: $EXPECTED_SHA256"
        echo "Actual:   $actual_sha256"
        return 1
    fi

    echo "Model checksum verified."
    return 0
}

if [ -f "$MODEL_PATH" ]; then
    echo "Model already exists:"
    echo "$MODEL_PATH"

    if verify_model; then
        ls -lh "$MODEL_PATH"
        exit 0
    fi

    echo "Removing the invalid local file."
    rm -f "$MODEL_PATH"
fi

echo "Downloading Qwen3-4B Q4_K_M..."
echo "Source: Qwen/Qwen3-4B-GGUF"
echo "Destination: $MODEL_PATH"

if command -v curl > /dev/null 2>&1; then
    curl \
        --fail \
        --location \
        --continue-at - \
        --retry 5 \
        --retry-delay 3 \
        --output "$MODEL_PATH" \
        "$MODEL_URL"
elif command -v wget > /dev/null 2>&1; then
    wget \
        --continue \
        --output-document="$MODEL_PATH" \
        "$MODEL_URL"
else
    echo "ERROR: curl or wget is required."
    exit 1
fi

if ! verify_model; then
    rm -f "$MODEL_PATH"
    exit 1
fi

echo "Model downloaded successfully:"
ls -lh "$MODEL_PATH"
