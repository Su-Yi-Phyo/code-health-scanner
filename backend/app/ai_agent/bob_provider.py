"""
bob_provider.py — IBM Bob Shell inference provider.

Invokes the locally-installed Bob Shell CLI to generate code-quality
explanations.  Falls back gracefully when Bob is unavailable, times out,
or returns unparseable output.

Public API
----------
explain_with_bob(file_path, language, source_code, duplicates, dead_code)
    -> dict with keys:
        "explanation"  : str
        "suggestions"  : list[str]
        "model_used"   : str   ("IBM Bob" on success)
        "_success"     : bool  (True only on a clean Bob response)
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BOB_TIMEOUT_SECONDS = 120

# Source text truncated to keep the prompt within Bob's context budget
MAX_SOURCE_CHARS = 3_000

_FAILURE_TEMPLATE: dict = {
    "explanation": "",
    "suggestions": [],
    "model_used": "none",
    "_success": False,
}


# ---------------------------------------------------------------------------
# Bob command locator
# ---------------------------------------------------------------------------

def _find_bob() -> str | None:
    """
    Return the Bob Shell command to use, or None if it cannot be found.

    Search order
    ------------
    1. ``bob.cmd`` on PATH (Windows CMD wrapper — passes args verbatim to node).
    2. ``bob``     on PATH (POSIX or Windows .exe).
    """
    cmd = shutil.which("bob.cmd") or shutil.which("bob")
    return cmd


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

def _build_prompt(
    file_path: str,
    language: str,
    source_code: str,
    duplicates: list[dict],
    dead_code: list[dict],
) -> str:
    """Build a Windows-safe single-line prompt sent to Bob."""

    duplicate_count = len(duplicates)
    dead_code_count = len(dead_code)

    # Flatten source code because multiline arguments are not reliably
    # preserved when Python invokes Bob through bob.cmd on Windows.
    truncated = source_code[:MAX_SOURCE_CHARS]
    source_flat = " ".join(truncated.split())

    findings = (
        f"Duplicate code instances: {duplicate_count}. "
        f"Dead code instances: {dead_code_count}. "
    )

    if duplicates:
        duplicate_lines = ", ".join(
            f"lines {d['line_start']}-{d['line_end']}"
            for d in duplicates[:5]
        )
        findings += f"Duplicate locations: {duplicate_lines}. "

    if dead_code:
        dead_names = ", ".join(
            str(d["name"]) for d in dead_code[:5]
        )
        findings += f"Unused definitions: {dead_names}. "

    return (
        "Review ONLY the following code. "
        "Do not inspect the workspace or other files. "
        "Do not ask for more context. "
        f"File: {file_path}. "
        f"Language: {language}. "
        f"Scanner findings: {findings}"
        f"Source code: {source_flat}. "
        "Give 3 to 5 short code-health observations. "
        "Each observation must be one concise sentence. "
        "Focus on what the code does and the quality issues supported by the scanner findings. "
        "Do not give detailed refactoring instructions. "
        "Return only the observations, one per line, each starting with a hyphen."
    )

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def explain_with_bob(
    file_path: str,
    language: str,
    source_code: str,
    duplicates: list[dict],
    dead_code: list[dict],
) -> dict:
    """
    Call Bob Shell to explain code quality issues.

    Returns a result dict.  ``_success`` is True only when Bob produced a
    valid, parseable response; callers should fall back to another provider
    when ``_success`` is False.
    """
    # --- Availability checks ------------------------------------------------
    api_key = os.environ.get("BOB_API_KEY", "")

    print(f"[BOB DEBUG] BOB_API_KEY present: {bool(api_key)}", flush=True)

    if not api_key:
        return {**_FAILURE_TEMPLATE, "explanation": "Bob unavailable: BOB_API_KEY is not set."}

    bob_cmd = _find_bob()

    print(f"[BOB DEBUG] Bob executable: {bob_cmd}", flush=True)

    if bob_cmd is None:
        return {**_FAILURE_TEMPLATE, "explanation": "Bob unavailable: 'bob' command not found on PATH."}

    # --- Build prompt -------------------------------------------------------
    prompt = _build_prompt(file_path, language, source_code, duplicates, dead_code)

    # --- Invoke Bob ---------------------------------------------------------
    # subprocess.run with a list never invokes a shell, so the prompt string
    # is passed verbatim as a single argv entry regardless of its content.
    # --disable-tool-groups subagent,mcp prevents Bob from inspecting the
    # workspace or spawning sub-agents; it answers from the prompt alone.
    cmd = [
        bob_cmd, "run",
        "--accept-license",
        "--format", "json",
        "--mode", "ask",
        "--disable-tool-groups", "subagent,mcp",
        prompt,
    ]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=BOB_TIMEOUT_SECONDS,
            env=os.environ,   # pass BOB_API_KEY and the rest of the environment
        )
    except subprocess.TimeoutExpired:
        print("[BOB DEBUG] Bob timed out.", flush=True)
        return {
            **_FAILURE_TEMPLATE,
            "explanation": f"Bob timed out after {BOB_TIMEOUT_SECONDS}s.",
        }

    except Exception as exc:  # noqa: BLE001
        print(
            f"[BOB DEBUG] Invocation exception: {type(exc).__name__}: {exc}",
            flush=True,
        )
        return {
            **_FAILURE_TEMPLATE,
            "explanation": f"Bob invocation error: {exc}",
        }

    print(f"[BOB DEBUG] Return code: {proc.returncode}", flush=True)
    print(f"[BOB DEBUG] stderr: {(proc.stderr or '')[:500]}", flush=True)
    print(f"[BOB DEBUG] stdout: {(proc.stdout or '')[:500]}", flush=True)

    if proc.returncode != 0:
        stderr_snippet = (proc.stderr or "").strip()[:300]
        return {
            **_FAILURE_TEMPLATE,
            "explanation": f"Bob returned exit code {proc.returncode}. {stderr_snippet}",
        }

    # --- Parse Bob's JSON envelope ------------------------------------------
    try:
        bob_json = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {
            **_FAILURE_TEMPLATE,
            "explanation": f"Bob returned non-JSON output: {proc.stdout[:200]}",
        }

    # Bob --format json wraps the reply in {"last_message": "..."}
    explanation: str = (bob_json.get("last_message", "") or "").strip()
    if not explanation:
        return {**_FAILURE_TEMPLATE, "explanation": "Bob returned an empty response."}

    return {
        "explanation": explanation,
        "suggestions": [],
        "model_used": "IBM Bob",
        "_success": True,
    }
