# Siyana AI

Siyana AI is an offline multilingual industrial-maintenance assistant built
for the Africa Deep Tech Challenge 2026 Laptop LLM track.

The application runs Qwen3-4B Q4_K_M locally through llama.cpp and supports
English, French, and Arabic.

## Features

- Fully local CPU inference
- No cloud inference API
- English, French, and Arabic support
- Right-to-left Arabic interface
- Safety-focused industrial guidance
- Refusal of guard bypasses and unsafe maintenance requests
- Local PDF/TXT manual import
- SQLite FTS5 document search
- Grounded answers with filename and page citations
- Duplicate-document detection
- Local document deletion
- FastAPI backend
- HTML, CSS, and JavaScript frontend

## Selected model

```text
Repository: Qwen/Qwen3-4B-GGUF
File: Qwen3-4B-Q4_K_M.gguf
Quantization: GGUF Q4_K_M
Parameters: approximately 4B
Runtime: llama.cpp
License: Apache 2.0
```

## Target hardware

Siyana AI targets the ADTC Standard Laptop:

- Intel Core i5 10th–12th generation or AMD Ryzen 5 3000–5000
- 8 GB DDR4 RAM
- Integrated graphics only
- 256 GB SSD
- Ubuntu 22.04 LTS

## Setup

### Install system dependencies

```bash
sudo apt update

sudo apt install -y \
  build-essential \
  cmake \
  git \
  curl \
  ca-certificates \
  python3 \
  python3-pip \
  python3-venv \
  python3-dev
```

### Build llama.cpp

```bash
git clone \
  https://github.com/ggml-org/llama.cpp.git \
  "$HOME/Projects/llama.cpp"

cd "$HOME/Projects/llama.cpp"

cmake -B build -DCMAKE_BUILD_TYPE=Release

cmake --build build --config Release -j 4 \
  --target llama-cli llama-server llama-bench
```

### Create the Python environment

```bash
cd "$HOME/Projects/siyana-ai"

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements-prototype.txt
```

### Link the llama.cpp programs

```bash
ln -sf \
  "$HOME/Projects/llama.cpp/build/bin/llama-cli" \
  .venv/bin/llama-cli

ln -sf \
  "$HOME/Projects/llama.cpp/build/bin/llama-server" \
  .venv/bin/llama-server

ln -sf \
  "$HOME/Projects/llama.cpp/build/bin/llama-bench" \
  .venv/bin/llama-bench
```

### Download the model

```bash
bash download_model.sh
```

### Start the application

```bash
./scripts/start_siyana.sh
```

Open:

```text
http://127.0.0.1:8000
```

### Stop the application

```bash
./scripts/stop_siyana.sh
```

## Local machine manuals

The application supports:

- Text-based `.pdf` files
- Plain-text `.txt` files
- Files up to 25 MB in the current prototype

Manuals are processed, indexed, searched, and cited entirely on the local
computer.

Image-only scanned PDFs require OCR and are not supported in the current
version.

## Validation

Validate the repository:

```bash
python scripts/validate_project.py
```

Run the participant profiler:

```bash
mkdir -p evaluation/profiler

adtc-profiler run \
  --submission "$PWD" \
  --mode participant \
  --output evaluation/profiler/participant-report.json \
  --skip-accuracy
```

## Safety

Siyana AI refuses instructions for:

- Bypassing guards or safety interlocks
- Disabling emergency stops
- Working on energized equipment
- Opening pressurized systems
- Exceeding manufacturer limits
- Performing undocumented dangerous modifications

Generated guidance is preliminary and does not replace approved procedures,
official manufacturer documentation, or qualified maintenance personnel.

## Evaluation

The development evaluation contains 60 prompts:

- 20 English
- 20 French
- 20 Arabic

The categories include:

- Troubleshooting
- Preventive maintenance
- Enterprise productivity
- Industrial safety
- Insufficient information

All 60 prompts completed generation successfully during the recorded
development run.

## License and attribution

The selected Qwen3-4B model is distributed separately under its applicable
Apache 2.0 license.

The GGUF model weights, imported manuals, local databases, and development
secrets are not committed to this repository.
