# Code Health Scanner

A **multi-language code health scanner** that analyzes public GitHub repositories, detects code quality issues, and ranks every file by risk score. Paste a GitHub URL — get a clean visual report of your riskiest files.

---

## How It Works

```
Browser
  │
  │  POST /analyze  { "repositoryUrl": "https://github.com/owner/repo" }
  ▼
Phase 2  (backend/app/main.py)
  │
  ├─ 1. validate_github_url()     → extract owner/repo, reject non-github URLs
  ├─ 2. download_repository()     → download ZIP into Python tempfile dir
  ├─ 3. find_source_files()       → walk repo, filter ignored dirs, filter >1 MB
  ├─ 4. parse_file()  ×N          → tree-sitter AST per file
  ├─ 5. detect_duplicates()       → sliding 6-line window hash across all files
  ├─ 6. detect_dead_code()        → AST definitions never referenced elsewhere
  ├─ 7. score_repository()        → risk_score = (dups×5) + (dead×3), clamped 100
  └─ 8. shutil.rmtree()           → temp dir deleted
  │
  │  returns { repositoryUrl, fileCount, repositoryScore, folderScores, files[] }
  │
  │  POST /report  (same body passed straight through)
  ▼
Phase 3  (backend/phase3/)
  │
  ├─ router.py          → receives Phase 2 body, maps file_path → path
  ├─ report_builder.py  → build_report()
  │     ├─ _make_file_report() ×N  → floor(risk_score), risk_label, reasons[]
  │     ├─ sort descending by score
  │     ├─ aggregate              → RepositorySummary
  │     ├─ slice [:10]            → TopRiskyFile[]
  │     └─ map all files          → ScatterPoint[]
  └─ returns FullReport JSON
  │
  ▼
Phase 4  (frontend/)
  │
  ├─ summary         → summary card
  ├─ top_risky_files → bar chart
  ├─ scatter_points  → scatter chart
  └─ files[]         → sortable table + detail panel
```

---

## Phases

### Phase 1 — File Discovery & Download
- Validates and downloads public GitHub repository archives into a temp directory
- Discovers all source files for **40+ languages** via extension mapping
- Filters out `venv/`, `__pycache__/`, `node_modules/`, `.git/`, `site-packages/`, `dist/`, `build/`
- Ignores files larger than 1 MB
- Deletes the temp directory after analysis completes

### Phase 2 — Scoring & Analysis
- **Parses** every file using tree-sitter AST grammars (language-agnostic)
- **Duplicate detection** — sliding window of 6 non-blank lines, MD5 hashed; blocks appearing in more than one location are flagged
- **Dead code detection** — extracts function/class/method definitions from the AST, flags names with only one occurrence in the full corpus (never referenced)
- **Risk scoring** per file:
  ```
  risk_score = (duplicate_blocks × 5) + (dead_code_items × 3), clamped to 100
  ```
- Folder and repository scores are the mean of all file scores within them
- **AI explanation** — `POST /explain` calls `Qwen2.5-7B-Instruct` via Hugging Face free Inference API to produce plain-English explanations and refactoring suggestions for any file

### Phase 3 — Report Builder

Consumes Phase 2's `POST /analyze` response and produces a single `FullReport` object the UI reads directly.

#### Step 1 — Receive & normalise (`router.py`)

Phase 2 returns `file_path` (with underscore); Phase 3's internal model uses `path`. The router bridges this automatically:

```
Phase 2 body field:  "file_path": "src/payment.py"
Phase 3 internal:    "path":      "src/payment.py"
```

The full GitHub URL is also reduced to `owner/repo` slug automatically.

#### Step 2 — Per-file conversion (`report_builder.py → _make_file_report`)

Phase 2 has already computed the score. Phase 3 does **not** re-score. It:

1. Floors the float to int — `math.floor(85.0)` → `85`
2. Assigns a risk label — `_risk_label(85)` → `"High Risk"`
3. Counts issues — `len(issues.duplicates)`, `len(issues.dead_code)`
4. Generates human-readable reasons from the actual issue data

Risk label thresholds:

| Score | Label |
|------:|-------|
| 0–29 | Healthy |
| 30–49 | Watch |
| 50–69 | Needs Attention |
| 70–100 | High Risk |

#### Step 3 — Reason generation (`report_builder.py → _build_reasons`)

Reasons are built from the real issue objects, not from numeric thresholds:

| Source | Example output |
|--------|---------------|
| 1 duplicate | `"Duplicate code block at lines 45–51 (duplicates src/billing.py:120-126)"` |
| 2 duplicates | `"2 duplicate code blocks detected"` |
| 3+ duplicates | `"3 duplicate code blocks detected"` |
| 1 dead-code item | `"Unused function \`_legacy_calculate\` (lines 88–112)"` |
| 2 dead-code items | `"Unused definitions: \`_old_validator\` and \`_legacy_calculate\`"` |
| 3+ dead-code items | `"Unused definitions: \`a\`, \`b\`, \`c\` and 2 more"` |
| line_count ≥ 400 | `"Large file: 612 lines"` *(informational)* |
| no issues | `"No significant issues detected"` |

#### Step 4 — Repository summary aggregation

Single pass over all scored files to produce `RepositorySummary`:

```
file_count             = len(files)
total_lines            = sum of all line_count
average_risk_score     = mean of all risk_scores (1 dp)
high_risk_file_count   = count where label == "High Risk"
needs_attention_count  = count where label == "Needs Attention"
watch_count            = count where label == "Watch"
healthy_count          = count where label == "Healthy"
total_duplicate_blocks = sum of all duplicate_block_count
total_dead_code_items  = sum of all dead_code_count
```

The four label counts always sum to `file_count`.

#### Step 5 — Chart datasets

**Top-10 bar chart** — slice the already-sorted list:
```
scored[:10]  →  TopRiskyFile[]   (rank 1–10, path, language, score, label)
```

**Scatter chart** — map every file:
```
all files  →  ScatterPoint[]   (path, line_count, duplicate_block_count, dead_code_count, score, label)
```
X axis: `line_count` · Y axis: `duplicate_block_count` or `dead_code_count` (UI choice) · colour: `risk_label`

#### FullReport shape

```
FullReport
│
├── summary                     1 object    → summary card
│     ├── repository
│     ├── file_count
│     ├── total_lines
│     ├── average_risk_score
│     ├── high_risk_file_count
│     ├── needs_attention_count
│     ├── watch_count
│     ├── healthy_count
│     ├── total_duplicate_blocks
│     └── total_dead_code_items
│
├── top_risky_files[]           max 10      → bar chart
│     └── rank, path, language, risk_score, risk_label
│
├── scatter_points[]            all files   → scatter chart
│     └── path, line_count, duplicate_block_count, dead_code_count, risk_score, risk_label
│
└── files[]                     all files   → sortable table + detail panel
      └── path, language, risk_score, risk_label,
          line_count, duplicate_block_count, dead_code_count,
          reasons[]
```

#### Mock endpoints (Phase 4 can start immediately)

| Endpoint | Returns |
|----------|---------|
| `GET /report/mock` | Full `FullReport` from built-in mock data |
| `GET /report/summary/mock` | `RepositorySummary` only |
| `GET /report/files/mock` | `FileReport[]` sorted by risk descending |

### Phase 4 — Frontend UI *(in progress)*
- Single-page Next.js 15 app with TypeScript
- URL input → loading state → results page
- **Summary card** — file count, total lines, average risk score, high-risk count
- **Bar chart** — top 10 riskiest files (Recharts)
- **Scatter chart** — issues vs lines per file
- **Sortable file table** — click any column to sort
- **File detail panel** — score, label, and reasons for each file
- Hosted on Vercel

---

## Tech Stack

| Area | Technology |
|------|-----------|
| Frontend | Next.js 15, TypeScript, Tailwind CSS, Recharts |
| Frontend hosting | Vercel |
| Backend API | Python 3.12, FastAPI, Uvicorn |
| Data validation | Pydantic v2 |
| Code parsing | tree-sitter ≥ 0.22 + language grammars |
| AI explanation | Qwen2.5-7B-Instruct via Hugging Face Inference API |
| Source download | GitHub archive download URL, `httpx` |
| Temporary storage | Python `tempfile` (deleted after each request) |
| Database | None |
| Auth | None |

---

## Project Structure

```
code-health-scanner/
├── .env                          ← secrets (gitignored) — put HF_API_TOKEN here
├── backend/
│   ├── main.py                   ← Phase 3: FastAPI app entry point
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py               ← Phase 2: /analyze and /explain endpoints
│   │   ├── analysis/
│   │   │   ├── github.py         ← Phase 1: URL validation, repo download, raw file fetch
│   │   │   └── scanner.py        ← Phase 1: multi-language file discovery
│   │   ├── scoring_agent/
│   │   │   ├── parser.py         ← Phase 2: universal tree-sitter parser
│   │   │   ├── scorer.py         ← Phase 2: risk score aggregator
│   │   │   └── detectors/
│   │   │       ├── duplication.py ← Phase 2: hash-based duplicate detector
│   │   │       └── dead_code.py   ← Phase 2: AST dead-code detector
│   │   └── ai_agent/
│   │       └── explainer.py      ← Phase 2: Qwen AI explanation agent
│   └── phase3/
│       ├── models.py             ← Phase 3: Pydantic schemas for all UI views
│       ├── mock_data.py          ← Phase 3: realistic mock Phase 2 output
│       ├── report_builder.py     ← Phase 3: converts FileMetrics → FullReport
│       └── router.py             ← Phase 3: /report endpoints
├── backend/tests/
│   └── test_phase3.py            ← Phase 3: 42 tests (all passing)
└── frontend/                     ← Phase 4: Next.js app (in progress)
```

---

## API Reference

### Phase 2 endpoints

#### `POST /analyze`
Download a public GitHub repository and return a full per-file code health report.

**Request:**
```json
{ "repositoryUrl": "https://github.com/owner/repo" }
```

**Response:**
```json
{
  "repositoryUrl": "https://github.com/psf/requests",
  "fileCount": 47,
  "repositoryScore": 18.3,
  "folderScores": { "requests": 22.1 },
  "files": [
    {
      "file_path": "requests/models.py",
      "language": "python",
      "line_count": 1012,
      "risk_score": 35.0,
      "issues": {
        "duplicates": [{ "line_start": 44, "line_end": 50, "duplicate_of": "requests/sessions.py:120-126" }],
        "dead_code":  [{ "name": "requote_uri", "kind": "function", "line_start": 88, "line_end": 95 }]
      }
    }
  ]
}
```

#### `POST /explain`
Fetch one file from GitHub and return an AI explanation + refactoring suggestions.

**Request:**
```json
{ "repositoryUrl": "https://github.com/owner/repo", "file_path": "src/utils.py" }
```

**Response:**
```json
{
  "file_path": "src/utils.py",
  "explanation": "This file contains several unused helper functions...",
  "suggestions": ["Remove unused imports", "Extract repeated logic into a shared helper"],
  "model_used": "Hugging Face / Qwen/Qwen2.5-7B-Instruct"
}
```

---

### Phase 3 endpoints

#### `GET /report/mock`
Returns a complete `FullReport` built from built-in mock data. Use this to build the frontend without running Phase 2.

#### `GET /report/summary/mock`
Returns the `RepositorySummary` card only (mock data).

#### `GET /report/files/mock`
Returns all `FileReport` objects sorted by risk score descending (mock data).

#### `POST /report`
Accepts Phase 2's `/analyze` response body directly and returns a `FullReport`.

**Request** — same body as `POST /analyze` response:
```json
{
  "repositoryUrl": "https://github.com/owner/repo",
  "fileCount": 15,
  "repositoryScore": 42.0,
  "folderScores": {},
  "files": [ { "file_path": "src/payment.py", "language": "python", "line_count": 612, "risk_score": 85.0, "issues": { "duplicates": [], "dead_code": [] } } ]
}
```

**Response:**
```json
{
  "summary": {
    "repository": "owner/repo",
    "file_count": 15,
    "total_lines": 2850,
    "average_risk_score": 28.4,
    "high_risk_file_count": 2,
    "needs_attention_count": 3,
    "watch_count": 4,
    "healthy_count": 6,
    "total_duplicate_blocks": 9,
    "total_dead_code_items": 7
  },
  "top_risky_files": [
    { "rank": 1, "path": "src/payment.py", "language": "python", "risk_score": 85, "risk_label": "High Risk" }
  ],
  "scatter_points": [
    { "path": "src/payment.py", "line_count": 612, "duplicate_block_count": 3, "dead_code_count": 3, "risk_score": 85, "risk_label": "High Risk" }
  ],
  "files": [
    {
      "path": "src/payment.py",
      "language": "python",
      "risk_score": 85,
      "risk_label": "High Risk",
      "line_count": 612,
      "duplicate_block_count": 3,
      "dead_code_count": 3,
      "reasons": [
        "3 duplicate code blocks detected",
        "Unused definitions: `_legacy_calculate`, `_old_validator`, `DeprecatedPaymentHelper`",
        "Large file: 612 lines"
      ]
    }
  ]
}
```

---

## Getting Started

### 1. Install dependencies

```bash
pip install -r backend/requirements.txt
```

### 2. Configure environment (for AI explanation only)

```bash
# .env
HF_API_TOKEN=hf_your_token_here
```

Get a free token at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens). The server runs without it — `POST /explain` returns a graceful unavailable message.

### 3. Run Phase 3 tests

```bash
python -m pytest backend/tests/test_phase3.py -v
# 42 passed
```

### 4. Start Phase 3 report server

Run from the project root (`code-health-scanner/`):

```powershell
python -m uvicorn backend.main:app --reload --port 8000
```

Interactive docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### 5. Start Phase 2 analysis server

Phase 2 lives on the `phase2-scoring` branch. After checking it out, run from the project root:

```powershell
python -m uvicorn app.main:app --reload --port 8001
```

---

## Supported Languages

`.py` Python · `.js` `.mjs` `.jsx` JavaScript · `.ts` TypeScript · `.tsx` TSX · `.html` HTML · `.css` CSS · `.java` Java · `.kt` Kotlin · `.scala` Scala · `.go` Go · `.rs` Rust · `.c` `.h` C · `.cpp` `.cc` `.hpp` C++ · `.cs` C# · `.rb` Ruby · `.php` PHP · `.swift` Swift · `.dart` Dart · `.lua` Lua · `.r` R · `.sh` Bash · `.hs` Haskell · `.ex` `.exs` Elixir · `.erl` Erlang · `.elm` Elm · `.ml` OCaml · `.json` JSON · `.toml` TOML · `.yaml` `.yml` YAML · `.sql` SQL · `.jl` Julia · `.nim` Nim · `.zig` Zig

---

## Safety Rules

- Accepts only public `github.com` URLs
- Downloads source files only — never runs repository code or installs dependencies
- Uses a temporary directory for every request, deleted immediately after analysis
- Does not store repository source code or results
- Rejects large repositories and files over 1 MB
