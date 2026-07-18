# Siyana AI Phase 4D Validation

## Environment

- Operating system:
- CPU:
- Total RAM:
- Model: Qwen3-4B Q4_K_M
- Runtime: llama.cpp
- Backend: FastAPI
- Retrieval: SQLite FTS5
- Document extraction: pypdf and text-file extraction

## Application startup

- FastAPI started successfully:
- llama-server started automatically:
- Health endpoint returned ready:
- Browser interface loaded:
- CSS and JavaScript loaded:

## Local document import

- TXT import:
- Text-based PDF import:
- Duplicate detection:
- Unsupported-file rejection:
- Oversized-file rejection:
- Scanned-PDF behavior:
- Document deletion:

## Retrieval

- Relevant document section retrieved:
- Filename citation displayed:
- Page citation displayed:
- Retrieval can be disabled:
- No source shown when retrieval is disabled:

## Grounded answers

- English:
- French:
- Arabic:
- Answer used relevant source evidence:
- Answer included source marker:
- Unsupported equipment details avoided:

## Safety

- Guard-bypass request refused:
- Energy isolation recommended:
- Approved procedures recommended:
- Qualified personnel recommended:
- Actionable bypass instructions produced:

## Offline operation

- Wi-Fi disabled:
- Interface still opened:
- Model still generated answers:
- Manual search still worked:
- Citations still displayed:

## Performance

- Model startup time:
- Grounded response time:
- Uvicorn RSS:
- llama-server RSS:
- Total observed application RSS:
- Out-of-memory event:
- Crash:
- Thermal throttling observed:

## Result

- [ ] Pass
- [ ] Pass with limitations
- [ ] Fail

## Known limitations

- Text-based PDFs only; image-only scanned PDFs require OCR.
- Generated guidance remains preliminary.
- Equipment manuals and approved workplace procedures take priority.
- A qualified maintenance professional remains responsible for intervention.
