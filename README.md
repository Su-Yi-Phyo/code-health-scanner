# Code Health Scanner

A **multi-language code health scanner** that analyzes public GitHub repositories, detects code quality issues, and ranks every file by risk score (0 = clean, 100 = maximally risky).

---

## Features

- **Multi-language support** — scans 40+ languages (Python, JavaScript, TypeScript, Java, Go, Rust, C/C++, Ruby, and more) via tree-sitter grammars
- **Duplication detection** — hash-based sliding-window algorithm flags duplicate code blocks across the repository
- **Dead code detection** — tree-sitter AST analysis identifies functions and classes never referenced elsewhere
- **Risk scoring** — each file receives a 0–100 risk score; scores roll up to folder and repository level
- **REST API** — FastAPI backend with a single `POST /analyze` endpoint; returns structured JSON
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
├── backend/
│   ├── requirements.txt
│   └── app/
│       ├── main.py                         ← FastAPI entry point (canonical)
│       ├── analysis/
│       │   ├── github.py                   ← GitHub URL validation + repo download
│       │   ├── scanner.py                  ← Multi-language file discovery
│       │   ├── ast_analyzer.py             ← Compat shim (delegates to scoring_agent)
│       │   ├── main.py                     ← Legacy re-export alias
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

### 2. Run unit tests

```bash
python backend/app/scoring_agent/test_scoring_agent.py
```

### 3. Start the API server

```bash
cd backend/app
uvicorn main:app --reload --port 8000
```

### 4. Analyze a repository

**Swagger UI** — open [http://localhost:8000/docs](http://localhost:8000/docs) in your browser.

**curl:**
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"repositoryUrl": "https://github.com/psf/requests"}'
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

## Requirements

- Python 3.11+
- Internet access (downloads the target repository from GitHub)
- Dependencies: `fastapi`, `uvicorn`, `httpx`, `tree-sitter>=0.22`, and individual `tree-sitter-*` language packages (see `requirements.txt`)
