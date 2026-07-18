# Technical Report — Siyana AI

## Submission identity

- **Project:** Siyana AI
- **Team / Devpost project ID:** siyana-ai
- **Primary domain:** Corporate / Enterprise
- **Cross-disciplinary pairing:** Industrial engineering and maintenance
- **Selected model:** Qwen3-4B Q4_K_M
- **Runtime:** llama.cpp
- **Inference mode:** Local CPU inference
- **Target:** ADTC Standard Laptop
- **Languages:** English, French, and Arabic

## Problem

Small factories and manufacturing SMEs often operate with limited maintenance
staff, paper records, fragmented technical documentation, and unreliable
internet connectivity.

When industrial equipment develops a fault, technicians may spend valuable
time searching through large manuals or relying on cloud tools that require
internet access, API fees, and the transfer of potentially sensitive machine
and production information.

Siyana AI is an offline multilingual industrial-maintenance assistant. The
application helps users organize machine symptoms, review possible causes,
identify safe preliminary checks, recognize stop-work conditions, and search
local machine manuals.

Siyana AI does not replace qualified technicians, approved workplace
procedures, safety engineers, or official manufacturer documentation.

## Target users

The intended users include:

- Factory maintenance technicians
- Machine operators
- Technical trainees
- Maintenance supervisors
- Small manufacturing companies
- SMEs operating in limited-connectivity environments

## Why local inference matters

Industrial-maintenance questions may include machine identifiers, alarm
messages, operating conditions, maintenance history, and internal production
information.

Local inference provides:

- Operation without internet connectivity
- No recurring cloud-inference fee
- Reduced exposure of operational information
- Predictable access during network outages
- Availability on ordinary commodity laptops
- Local search over machine manuals
- Control over imported documents and stored data

## System architecture

```text
Browser interface
    |
    | Local HTTP requests
    v
FastAPI backend
    |
    +---- SQLite FTS5 manual search
    |
    +---- Local PDF/TXT extraction
    |
    v
llama-server
    |
    v
Qwen3-4B Q4_K_M GGUF
```

Questions, manuals, document indexes, retrieved passages, prompts, and
generated responses remain on the local computer.

## Model selection

### Selected model

- Base model: Qwen3-4B
- GGUF repository: Qwen/Qwen3-4B-GGUF
- File: Qwen3-4B-Q4_K_M.gguf
- Parameters: approximately 4 billion
- Quantization: GGUF Q4_K_M
- Runtime: llama.cpp
- License: Apache 2.0

### Selection rationale

Qwen3-4B Q4_K_M was selected because it:

- Loaded and executed successfully through llama.cpp
- Produced usable English, French, and Arabic responses
- Followed structured industrial-maintenance instructions
- Supported non-thinking mode for concise output
- Refused tested guard-bypass requests
- Ran without cloud inference
- Used a permissive Apache 2.0 license
- Offered a practical quality-to-memory balance

A wider candidate comparison was deferred to prioritize domain evaluation,
safety engineering, optimization, documentation, retrieval, and prototype
development.

## Quantization decision

Q4_K_M was selected as a balance between:

- Model quality
- Storage footprint
- Peak memory
- CPU inference speed
- Multilingual performance
- Compatibility with the 8 GB target laptop

Higher-precision formats would require more memory and storage. More
aggressive quantization could reduce multilingual and technical-answer
quality.

## Standard Laptop constraints

Siyana AI is designed for the published ADTC Standard Laptop profile:

- Intel Core i5 10th–12th generation or AMD Ryzen 5 3000–5000
- 8 GB DDR4 RAM
- Integrated graphics only
- 256 GB SSD
- Ubuntu 22.04 LTS
- CPU-based llama.cpp inference

The application does not require CUDA, an NVIDIA GPU, a cloud inference API,
or persistent internet connectivity.

## Runtime configuration

The prototype uses conservative defaults:

- One model-server process
- Four CPU threads during baseline testing
- 4096-token context
- Temperature of 0.2
- Qwen thinking disabled with `/no_think`
- Up to five retrieved manual sections by default
- Limited retrieved-text character budget
- One expected interactive user
- 25 MB manual-upload limit

These settings reduce memory pressure and keep responses reasonably concise.

## Safety design

The system prompt prohibits instructions for:

- Bypassing machine guards
- Defeating safety interlocks
- Disabling emergency-stop systems
- Working on energized electrical equipment
- Opening pressurized pneumatic or hydraulic systems
- Exceeding manufacturer limits
- Modifying safety PLC logic without authorization
- Continuing production under dangerous unexplained conditions

For unsafe requests, Siyana AI is instructed to:

1. Refuse the unsafe action.
2. Explain the hazard briefly.
3. Recommend machine shutdown.
4. Require hazardous-energy isolation.
5. Recommend approved workplace procedures.
6. Escalate to qualified and authorized personnel.

## Multilingual domain evaluation

A structured 60-prompt dataset was created:

- 20 English prompts
- 20 French prompts
- 20 Arabic prompts

Each language contained:

- 5 troubleshooting prompts
- 5 preventive-maintenance prompts
- 4 enterprise-productivity prompts
- 3 safety prompts
- 3 insufficient-information prompts

The automated development run completed with:

- 60 prompts processed
- 60 successful generations
- 0 generation failures
- Average development response duration of 52.616 seconds

The evaluation covered:

- Technical usefulness
- Instruction following
- Safety behavior
- Clarity
- Language quality
- Uncertainty handling
- Hallucination risk
- Missing-information behavior

These are self-reported development results, not official third-party
accuracy scores. Successful generation means the model completed the request
without an execution error; it does not automatically mean the answer was
perfect.

## African-language functionality

Siyana AI includes meaningful Arabic functionality through:

- Arabic interface content
- Right-to-left browser presentation
- Arabic questions and responses
- Twenty Arabic evaluation prompts
- Arabic safety-sensitive tests
- Arabic insufficient-information tests
- Arabic industrial-maintenance guidance

This functionality is intended to improve accessibility for Arabic-speaking
technicians and SMEs in North Africa.

## Local manual retrieval

Siyana AI supports local import of:

- Text-based PDF documents
- Plain-text TXT documents

The retrieval workflow:

1. Validates file type and size.
2. Calculates a SHA-256 fingerprint.
3. Detects duplicate documents.
4. Extracts text locally.
5. Divides text into overlapping sections.
6. Stores document metadata in SQLite.
7. Indexes content with SQLite FTS5.
8. Retrieves relevant sections using BM25 ranking.
9. Sends only limited relevant excerpts to the model.
10. Displays filename and page citations.

No imported manual is uploaded to an external service.

### Retrieval limitations

- Image-only scanned PDFs require OCR, which is not included.
- Extraction quality depends on the PDF text layer.
- Lexical retrieval may miss semantically related terminology.
- Retrieved content is not automatically technically authoritative.
- Users must verify guidance against official documentation.
- Users are responsible for importing legally obtained documents.

## Application interface

The local web application provides:

- Local-model health status
- English, French, and Arabic modes
- Right-to-left Arabic layout
- Machine name and model fields
- Question and additional-context fields
- Local PDF/TXT manual import
- Imported-document listing and deletion
- Retrieval enable/disable control
- Retrieved-source limit
- Structured response display
- Filename and page citation cards
- Local-model and response-duration metadata
- Safety notices

## Offline operation

The selected model, backend, frontend, SQLite database, imported manuals,
document search, and response generation operate locally.

Network access is required only for initial installation and model download.
After setup, inference does not require an external API.

## Development benchmarks

Development measurements were performed through Ubuntu under Windows
Subsystem for Linux. WSL measurements may differ from native Ubuntu because
of virtualization, filesystem behavior, CPU scheduling, and memory reporting.

Initial interactive observations included approximately:

- Prompt processing: 50.1 tokens per second
- Text generation: 10.0 tokens per second

Formal participant-profiler results are stored, when successfully generated,
at:

```text
evaluation/profiler/participant-report.json
```

Official competition measurements will be performed on the published ADTC
Standard Laptop and may differ from development results.
### ADTC participant profiler

### ADTC participant profiler

- Peak RSS: 4287.84 MB
- Steady-state RSS: 4164.24 MB
- Generation throughput: 11.19 tokens/second
- Prompt-processing throughput: Not reported by the local profiler environment
- First-token latency: 10055.74 ms
- CPU utilization: 50.9% (p99)
- Thermal information: Not reported by the local profiler environment
- Profiler mode: Participant, accuracy skipped
## Reproduction

### Download the selected model

```bash
bash download_model.sh
```

### Activate the Python environment

```bash
source .venv/bin/activate
```

### Start Siyana AI

```bash
./scripts/start_siyana.sh
```

Open:

```text
http://127.0.0.1:8000
```

### Stop Siyana AI

```bash
./scripts/stop_siyana.sh
```

### Validate the repository

```bash
python scripts/validate_project.py
```

### Run the participant profiler

```bash
mkdir -p evaluation/profiler

adtc-profiler run \
  --submission "$PWD" \
  --mode participant \
  --output evaluation/profiler/participant-report.json \
  --skip-accuracy
```

## Known limitations

- Generated guidance is preliminary.
- Model output may contain errors or omissions.
- Siyana AI does not replace qualified maintenance personnel.
- Machine-specific values must come from approved documentation.
- Image-only PDFs require OCR.
- Lexical retrieval may miss related terminology.
- Arabic terminology may require review for specialized equipment.
- Local benchmark values may differ from official hardware results.
- The prototype expects one interactive user and one model server.
- Imported manuals must be legally obtained and authorized for local use.

## Future improvements

Potential improvements include:

- Local OCR for scanned manuals
- Hybrid lexical and embedding retrieval
- Better Arabic industrial terminology
- Equipment-specific profiles
- Local maintenance-history storage
- Local work-order generation
- Improved citation verification
- Automated application testing
- Native Ubuntu 22.04 packaging
- Faster startup and lower memory usage

## Conclusion

Siyana AI demonstrates an end-to-end, offline, multilingual industrial
maintenance application on commodity hardware.

The project combines:

- Quantized local inference
- Multilingual industrial support
- Safety-focused prompting
- Local manual retrieval
- SQLite full-text search
- Evidence-based citations
- Privacy-preserving offline operation
- A lightweight interactive interface

The system is designed for the constraints of ordinary laptops used by
African SMEs and industrial technicians.
