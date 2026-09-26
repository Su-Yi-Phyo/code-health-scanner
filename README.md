# Code Health Scanner

A **multi-language code health scanner** that analyzes public GitHub repositories, detects code quality issues, and ranks every file by risk score (0 = clean, 100 = maximally risky).

---

## Features

- **Multi-language support** — scans 40+ languages (Python, JavaScript, TypeScript, Java, Go, Rust, C/C++, Ruby, and more) via tree-sitter grammars
- **Duplication detection** — hash-based sliding-window algorithm flags duplicate code blocks across the repository
- **Dead code detection** — tree-sitter AST analysis identifies functions and classes never referenced elsewhere
- **Risk scoring** — each file receives a 0–100 risk score; scores roll up to folder and repository level
- **AI explanation agent** — `POST /explain` fetches any file and returns a plain-language explanation + refactoring suggestions powered by `Qwen/Qwen2.5-7B-Instruct` via the Hugging Face free Inference API
- **REST API** — FastAPI backend with `POST /analyze` and `POST /explain` endpoints; returns structured JSON
- **Interactive Swagger UI** — built-in API docs at `/docs`

---

## Risk Score

| Score | Meaning |
|-------|---------|
| 0 | Perfectly clean — no issues detected |
| 1–20 | Low risk — minor issues |
| 21–50 | Moderate risk — noticeable duplication or dead code |
| 51–80 | High risk — significant code quality problems |
| 81–100 | Critical — heavily unoptimized |

**Formula per file:**
```
risk_score = (duplicate_blocks × 5) + (dead_code_items × 3)
           = min(100, risk_score)
```
Folder and repository scores are the mean of all file scores within them.

---

## Project Structure

```
code-health-scanner/
├── .env                                    ← secrets (gitignored) — put HF_API_TOKEN here
├── backend/
│   ├── requirements.txt
│   └── app/
│       ├── main.py                         ← FastAPI entry point — all routes
│       ├── ai_agent/
│       │   └── explainer.py               ← AI explanation agent (POST /explain)
│       ├── analysis/
│       │   ├── github.py                   ← GitHub URL validation, repo download, raw file fetch
│       │   ├── scanner.py                  ← Multi-language file discovery
│       │   └── test_*.py                   ← Unit + integration tests
│       └── scoring_agent/
│           ├── parser.py                   ← Universal tree-sitter parser layer
│           ├── scorer.py                   ← Risk score aggregator
│           ├── test_scoring_agent.py       ← Scoring agent unit tests (35 checks)
│           └── detectors/
│               ├── duplication.py          ← Hash-based duplicate block detector
│               └── dead_code.py            ← AST-based dead code detector
└── frontend/
    └── index.html                          ← Single-page UI (coming soon)
```

---

## Supported Languages

`.py` Python · `.js` `.mjs` `.jsx` JavaScript · `.ts` TypeScript · `.tsx` TSX · `.java` Java · `.kt` Kotlin · `.scala` Scala · `.go` Go · `.rs` Rust · `.c` `.h` C · `.cpp` `.cc` `.hpp` C++ · `.cs` C# · `.rb` Ruby · `.php` PHP · `.swift` Swift · `.dart` Dart · `.lua` Lua · `.r` R · `.sh` Bash · `.hs` Haskell · `.ex` `.exs` Elixir · `.erl` Erlang · `.elm` Elm · `.ml` OCaml · `.json` JSON · `.toml` TOML · `.yaml` `.yml` YAML · `.sql` SQL · `.jl` Julia · `.nim` Nim · `.zig` Zig

---

## Getting Started

### 1. Install dependencies

```bash
pip install -r backend/requirements.txt
```

### 2. Configure environment

Create a `.env` file in the project root (already gitignored):

```
HF_API_TOKEN=hf_your_token_here
```

Get a free token at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) — read access is enough.
The server works without it, but `POST /explain` will return a graceful unavailable message.

### 3. Run unit tests

```bash
python backend/app/scoring_agent/test_scoring_agent.py
```

### 4. Start the API server

```bash
cd backend/app
python -m uvicorn main:app --reload --port 8000
```

### 5. Use the API

**Swagger UI** — open [http://localhost:8000/docs](http://localhost:8000/docs) in your browser for an interactive interface to both endpoints.

**Step 1 — Analyze a repository:**
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"repositoryUrl": "https://github.com/psf/requests"}'
```

**Step 2 — Explain a high-risk file** (use `repositoryUrl` + `file_path` from the analyze response):
```bash
curl -X POST http://localhost:8000/explain \
  -H "Content-Type: application/json" \
  -d '{"repositoryUrl": "https://github.com/psf/requests", "file_path": "src/requests/utils.py"}'
```

---

## API Reference

### `GET /`
Health check. Returns `{"message": "Code Health Scanner is running"}`.

### `POST /analyze`

**Request body:**
```json
{
  "repositoryUrl": "https://github.com/owner/repo"
}
```

**Response:**
```json
{
  "repositoryUrl":   "https://github.com/psf/requests",
  "fileCount":       47,
  "repositoryScore": 18.3,
  "folderScores": {
    "requests": 22.1,
    "tests":    8.5
  },
  "files": [
    {
      "file_path":  "requests/models.py",
      "language":   "python",
      "line_count": 1012,
      "risk_score": 35.0,
      "issues": {
        "duplicates": [
          {
            "line_start":    44,
            "line_end":      50,
            "duplicate_of":  "requests/sessions.py:120-126"
          }
        ],
        "dead_code": [
          {
            "name":       "requote_uri",
            "kind":       "function",
            "line_start": 88,
            "line_end":   95
          }
        ]
      }
    }
  ]
}
```

**Error responses:**
| Status | Reason |
|--------|--------|
| `422` | Invalid or non-GitHub URL, missing field |
| `500` | Download failure or unexpected error |

---

### `POST /explain`

Fetches a single file from GitHub and returns an AI-generated plain-language explanation
of its code quality issues plus concrete refactoring suggestions.

The caller provides only `repositoryUrl` and `file_path` — both are already present in the
`POST /analyze` response. The backend re-fetches just that one file via GitHub's raw content
API and calls **`Qwen/Qwen2.5-7B-Instruct`** via the Hugging Face free Inference API.

Requires `HF_API_TOKEN` in your `.env` file. Returns 200 with a graceful message when unset.

**Request body:**
| Field | Type | Description |
|-------|------|-------------|
| `repositoryUrl` | string | Same GitHub URL used in `/analyze` |
| `file_path` | string | Relative file path from the `/analyze` response, e.g. `"src/requests/utils.py"` |

**curl:**
```bash
curl -X POST http://localhost:8000/explain \
  -H "Content-Type: application/json" \
  -d '{"repositoryUrl": "https://github.com/psf/requests", "file_path": "src/requests/utils.py"}'
```

**Response:**
```json
{
  "file_path": "src/requests/utils.py",
  "explanation": "This file contains several utility functions with some code quality concerns. There are unused imports that add unnecessary complexity, and a few helper functions that appear unreferenced elsewhere in the codebase.",
  "suggestions": [
    "Remove unused imports to reduce noise and improve readability.",
    "Extract repeated logic into a shared helper to eliminate duplication.",
    "Add docstrings to public functions to clarify intent for future maintainers."
  ],
  "model_used": "Hugging Face / Qwen/Qwen2.5-7B-Instruct"
}
```

**Error responses:**
| Status | Reason |
|--------|--------|
| `404` | `file_path` not found in the repository |
| `422` | Invalid or non-GitHub URL |
| `500` | File fetch failure or unexpected error |

---

## Requirements

- Python 3.11+
- Internet access (downloads the target repository from GitHub)
- Dependencies: see `backend/requirements.txt` — `fastapi`, `uvicorn`, `httpx`, `python-dotenv`, `huggingface_hub`, `tree-sitter>=0.22`, and individual `tree-sitter-*` language packages
- **`HF_API_TOKEN`** in `.env` — free Hugging Face token for `POST /explain` ([get one here](https://huggingface.co/settings/tokens)); server runs without it but `/explain` returns a graceful unavailable message
