"""
explainer.py — AI-powered code explanation and suggestion agent.

Calls a free Hugging Face serverless Inference API model to explain code
quality problems in plain language and return concrete refactoring suggestions.

Models are tried in order; the first one that responds successfully is used.
This makes the agent resilient to any single model being unavailable.

Requires HF_API_TOKEN environment variable (free token from
huggingface.co/settings/tokens).

Public API
----------
explain_issues(file_path, language, source_code, duplicates, dead_code, hf_token)
    -> dict with keys:
        "explanation"  : str
        "suggestions"  : list[str]
        "model_used"   : str
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Models tried in order — first one that succeeds is used.
# All are free on the HF Serverless Inference API (hf-inference provider).
CANDIDATE_MODELS = [
    "mistralai/Mistral-7B-Instruct-v0.3",
    "HuggingFaceH4/zephyr-7b-beta",
    "microsoft/Phi-3-mini-4k-instruct",
]

# Source text truncated to this many characters to stay within token budget
MAX_SOURCE_CHARS = 4_000

# Maximum tokens the model may generate
MAX_NEW_TOKENS = 600


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

def _build_messages(
    file_path: str,
    language: str,
    source_code: str,
    duplicates: list[dict],
    dead_code: list[dict],
) -> list[dict]:
    """Build the chat messages list."""

    system_message = {
        "role": "system",
        "content": (
            "You are a senior software engineer specializing in code quality and refactoring. "
            "When shown source code, you explain code quality problems clearly in plain language "
            "and give concrete, actionable suggestions to improve the code. "
            "Always respond with exactly two sections:\n"
            "## Explanation\n"
            "<one paragraph describing the quality issues found and why they matter>\n\n"
            "## Suggestions\n"
            "<a numbered list, one item per actionable improvement>"
        ),
    }

    issues_lines: list[str] = []

    if duplicates:
        issues_lines.append("Duplicate code blocks detected:")
        for i, d in enumerate(duplicates, 1):
            issues_lines.append(
                f"  {i}. Lines {d['line_start']}–{d['line_end']} "
                f"duplicates {d['duplicate_of']}"
            )
    else:
        issues_lines.append("No duplicate code blocks detected by the scanner.")

    issues_lines.append("")

    if dead_code:
        issues_lines.append("Dead code (unused definitions) detected:")
        for i, dc in enumerate(dead_code, 1):
            issues_lines.append(
                f"  {i}. {dc['kind']} `{dc['name']}` "
                f"(lines {dc['line_start']}–{dc['line_end']}) — never referenced"
            )
    else:
        issues_lines.append("No dead code detected by the scanner.")

    truncated_source = source_code[:MAX_SOURCE_CHARS]
    if len(source_code) > MAX_SOURCE_CHARS:
        truncated_source += "\n... [source truncated]"

    user_message = {
        "role": "user",
        "content": (
            f"File: {file_path}\n"
            f"Language: {language}\n\n"
            "Scanner findings:\n"
            + "\n".join(issues_lines)
            + f"\n\nSource code:\n```{language}\n{truncated_source}\n```\n\n"
            "Please explain the code quality issues in this file and provide "
            "specific suggestions to improve it."
        ),
    }

    return [system_message, user_message]


# ---------------------------------------------------------------------------
# Response parser
# ---------------------------------------------------------------------------

def _parse_response(raw_text: str) -> dict:
    """
    Split the model response into explanation and suggestions.
    Expects '## Suggestions' as a section delimiter.
    Falls back to putting the full text in explanation when absent.
    """
    parts = re.split(r"##\s*suggestions", raw_text, maxsplit=1, flags=re.IGNORECASE)

    if len(parts) == 2:
        explanation_raw, suggestions_raw = parts

        explanation = re.sub(
            r"^##\s*explanation\s*", "", explanation_raw, flags=re.IGNORECASE
        ).strip()

        suggestions: list[str] = []
        for line in suggestions_raw.splitlines():
            line = line.strip()
            if not line:
                continue
            cleaned = re.sub(r"^[-*]|\d+\.\s*", "", line, count=1).strip()
            if cleaned:
                suggestions.append(cleaned)

        return {"explanation": explanation, "suggestions": suggestions}

    return {"explanation": raw_text.strip(), "suggestions": []}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def explain_issues(
    file_path: str,
    language: str,
    source_code: str,
    duplicates: list[dict],
    dead_code: list[dict],
    hf_token: str = "",
) -> dict:
    """
    Explain code quality issues and suggest improvements.

    Parameters
    ----------
    file_path   : relative path of the file (used in the prompt)
    language    : detected language string e.g. "python"
    source_code : full source text of the file
    duplicates  : list of DuplicateIssue dicts from the scanner
    dead_code   : list of DeadCodeIssue dicts from the scanner
    hf_token    : Hugging Face user access token (HF_API_TOKEN env var)

    Returns
    -------
    dict with keys "explanation" (str), "suggestions" (list[str]), "model_used" (str)
    """
    if not hf_token:
        return {
            "explanation": (
                "AI explanation unavailable: HF_API_TOKEN is not set. "
                "Add HF_API_TOKEN to your .env file — get a free token at "
                "huggingface.co/settings/tokens."
            ),
            "suggestions": [],
            "model_used": "none",
        }

    try:
        from huggingface_hub import InferenceClient

        # Use hf-inference provider — available to all free HF tokens.
        client = InferenceClient(provider="hf-inference", api_key=hf_token)
        messages = _build_messages(file_path, language, source_code, duplicates, dead_code)

        last_exc: Exception | None = None
        for model_id in CANDIDATE_MODELS:
            try:
                response = client.chat.completions.create(
                    model=model_id,
                    messages=messages,
                    max_tokens=MAX_NEW_TOKENS,
                )
                raw_text: str = response.choices[0].message.content or ""
                result = _parse_response(raw_text)
                result["model_used"] = f"Hugging Face / {model_id}"
                return result
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                continue

        return {
            "explanation": f"AI request failed: {last_exc}",
            "suggestions": [],
            "model_used": "none",
        }

    except Exception as exc:  # noqa: BLE001
        return {
            "explanation": f"AI request failed: {exc}",
            "suggestions": [],
            "model_used": "none",
        }
