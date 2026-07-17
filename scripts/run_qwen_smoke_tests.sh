#!/usr/bin/env bash

set -euo pipefail

PROJECT_DIR="$HOME/Projects/siyana-ai"
MODEL="$PROJECT_DIR/model/Qwen3-4B-Q4_K_M.gguf"
PROMPT_DIR="$PROJECT_DIR/evaluation/qwen3-4b/prompts"
RESULT_DIR="$PROJECT_DIR/evaluation/qwen3-4b/results"
LLAMA_CLI="$PROJECT_DIR/.venv/bin/llama-cli"
#!/usr/bin/env bash

set -euo pipefail

PROJECT_DIR="$HOME/Projects/siyana-ai"
MODEL="$PROJECT_DIR/model/Qwen3-4B-Q4_K_M.gguf"
PROMPT_DIR="$PROJECT_DIR/evaluation/qwen3-4b/prompts"
RESULT_DIR="$PROJECT_DIR/evaluation/qwen3-4b/results"
LLAMA_CLI="$PROJECT_DIR/.venv/bin/llama-cli"

mkdir -p "$RESULT_DIR"

if [ ! -x "$LLAMA_CLI" ]; then
    echo "ERROR: llama-cli was not found or is not executable:"
    echo "$LLAMA_CLI"
    exit 1
fi

if [ ! -f "$MODEL" ]; then
    echo "ERROR: GGUF model was not found:"
    echo "$MODEL"
    exit 1
fi

for required_prompt in english french arabic safety; do
    if [ ! -f "$PROMPT_DIR/$required_prompt.txt" ]; then
        echo "ERROR: Missing prompt file:"
        echo "$PROMPT_DIR/$required_prompt.txt"
        exit 1
    fi
done

run_test() {
    local name="$1"
    local context="$2"
    local output_tokens="$3"
    local temperature="$4"

    local prompt_file="$PROMPT_DIR/$name.txt"
    local result_file="$RESULT_DIR/$name.txt"

    echo
    echo "========================================"
    echo "Running test: $name"
    echo "Prompt: $prompt_file"
    echo "Result: $result_file"
    echo "========================================"

    "$LLAMA_CLI" \
        -m "$MODEL" \
        --jinja \
        --single-turn \
        --simple-io \
        -c "$context" \
        -n "$output_tokens" \
        -t 4 \
        --temp "$temperature" \
        -f "$prompt_file" \
        2>&1 | tee "$result_file"

    echo
    echo "Completed test: $name"
    echo "Saved result: $result_file"
}

run_test "english" 2048 350 0.2
run_test "french" 2048 350 0.2
run_test "arabic" 2048 350 0.2
run_test "safety" 1024 250 0.1

echo
echo "========================================"
echo "All Qwen3-4B smoke tests completed"
echo "========================================"

ls -lh "$RESULT_DIR"
mkdir -p "$RESULT_DIR"

if [ ! -x "$LLAMA_CLI" ]; then
    echo "ERROR: llama-cli was not found at:"
    echo "$LLAMA_CLI"
    exit 1
fi

if [ ! -f "$MODEL" ]; then
    echo "ERROR: Model was not found at:"
    echo "$MODEL"
    exit 1
fi

run_test() {
    name="$1"
    prompt_file="$PROMPT_DIR/$name.txt"
    result_file="$RESULT_DIR/$name.txt"

    if [ ! -f "$prompt_file" ]; then
        echo "ERROR: Prompt file not found: $prompt_file"
        exit 1
    fi

    echo
    echo "========================================"
    echo "Running test: $name"
    echo "========================================"

    "$LLAMA_CLI" \
        -m "$MODEL" \
        --jinja \
        -c 2048 \
        -n 350 \
        -t 4 \
        --temp 0.2 \
        -f "$prompt_file" \
        --simple-io \
        2>&1 | tee "$result_file"

    echo
    echo "Saved result to: $result_file"
}

run_test "english"
run_test "french"
run_test "arabic"

# Use lower temperature for the safety-refusal test.
echo
echo "========================================"
echo "Running test: safety"
echo "========================================"

"$LLAMA_CLI" \
    -m "$MODEL" \
    --jinja \
    -c 1024 \
    -n 250 \
    -t 4 \
    --temp 0.1 \
    -f "$PROMPT_DIR/safety.txt" \
    --simple-io \
    2>&1 | tee "$RESULT_DIR/safety.txt"

echo
echo "========================================"
echo "All smoke tests completed"
echo "========================================"
echo "Results directory:"
echo "$RESULT_DIR"
