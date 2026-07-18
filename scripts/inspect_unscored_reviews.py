from pathlib import Path
import re

path = Path('evaluation/domain/full-reports/full-review.md')
text = path.read_text(encoding='utf-8')
sections = re.split(r'(?=^## [A-Z]{2}-(?:TR|PM|EP|SF|II)-\d{3} —)', text, flags=re.MULTILINE)
for sec in sections:
    if not sec.strip().startswith('## '):
        continue
    m = re.match(r'## ([A-Z]{2}-(?:TR|PM|EP|SF|II)-\d{3}) — ([a-z]{2}) — ([a-z_]+)', sec)
    if not m:
        continue
    pid, lang, cat = m.groups()
    scores = {}
    for label in ['Technical correctness (0–5)', 'Instruction following (0–5)', 'Safety (0–5)', 'Clarity (0–5)', 'Language quality (0–5)', 'Uncertainty handling (0–5)', 'Total (0–30)', 'Pass / Review / Fail', 'Hallucination observed']:
        pat = re.search(rf'^- {re.escape(label)}:\s*(.*)$', sec, flags=re.MULTILINE)
        scores[label] = pat.group(1).strip() if pat else None
    filled = all(scores[label] not in (None, '') for label in scores)
    if not filled:
        first_lines = sec.splitlines()
        response_idx = next((i for i, line in enumerate(first_lines) if line.startswith('### Model response')), None)
        snippet = ''
        if response_idx is not None:
            snippet_lines = first_lines[response_idx+1:response_idx+6]
            snippet = ' | '.join(line.strip() for line in snippet_lines if line.strip())
        print(f'{pid} {lang} {cat} | {snippet}')
