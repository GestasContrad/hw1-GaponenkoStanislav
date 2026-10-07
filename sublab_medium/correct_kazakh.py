"""Sublab Medium - one Kazakh-correction task, six models.

Six models, one prompt, eight sentences. What you are producing is evidence:
a table that says which models repaired which kind of damage, and what each one
charged you for the attempt.

Fill in every `TODO`. Keep the function signatures.
"""
from __future__ import annotations
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sublab_easy.registration_bot import (RATES_PER_MTOK,  # noqa: E402
                                          ask_once, estimate_cost)

DATA = Path(__file__).resolve().parent.parent / "data" / "kazakh_errors.json"

# Every model you must run. Keep the order - it is the order of your table.
MODELS = [
    ("openrouter", "google/gemma-4-26b-a4b-it:free"),
    ("openrouter", "qwen/qwen3.8-27b"),
    ("openrouter", "deepseek/deepseek-v4-flash-0731"),
    ("openai", "gpt-5.6-luna"),
    ("openai", "gpt-5.6-terra"),
    ("openai", "gpt-5.6-sol"),
]


def load_sentences() -> list[dict]:
    """The eight corrupted sentences and their published originals."""
    return json.loads(DATA.read_text(encoding="utf-8"))["sentences"]


def build_prompt(corrupted: str) -> str:
    return f"""You are an expert editor for the Kazakh language.
The following Kazakh text contains deliberate errors. These may include wrong letters (e.g., Russian Cyrillic lookalikes), letters from the wrong alphabet (e.g., Latin homoglyphs), missing hyphens, joined words, or doubled letters.

Text to correct:
{corrupted}

You must return EXACTLY this JSON structure and nothing else:
{{"corrected": "the fully corrected string", "changes": ["description of change 1", "description of change 2"]}}
"""


def parse_response(text: str) -> dict:
    try:
        #delim
        start_idx = text.find('{')
        end_idx = text.rfind('}')

        if start_idx == -1 or end_idx == -1:
            raise ValueError(f"No JSON object found in response: {text}")

        json_str = text[start_idx: end_idx + 1]
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to decode JSON: {text}") from e


def correct_with(model: str, corrupted: str, via: str) -> dict:
    prompt = build_prompt(corrupted)
    reply = ask_once(prompt, model=model, via=via)

    parsed = parse_response(reply["text"])

    return {
        "corrected": parsed.get("corrected", ""),
        "changes": parsed.get("changes", []),
        "input_tokens": reply["input_tokens"],
        "output_tokens": reply["output_tokens"],
        "model": reply["model"]
    }


def score_correction(returned: str, expected: str) -> dict:
    exact = (returned == expected)

    # Count to the end of the shortest
    char_diff = sum(1 for a, b in zip(returned, expected) if a != b)
    char_diff += abs(len(returned) - len(expected))

    return {
        "exact": exact,
        "char_diff": char_diff
    }


def run_all() -> list[dict]:
    """Every model against every sentence. One row per (model, sentence)."""
    rows = []
    for via, model in MODELS:
        for s in load_sentences():
            try:
                r = correct_with(model, s["corrupted"], via)
            except Exception as exc:            # a model failing IS a result
                rows.append({"model": model, "id": s["id"],
                             "errors": s["errors"], "failed": repr(exc)})
                continue
            rate_in, rate_out = RATES_PER_MTOK[model]
            rows.append({
                "model": model,
                "id": s["id"],
                "errors": s["errors"],
                "corrected": r["corrected"],
                "changes": r["changes"],
                **score_correction(r["corrected"], s["correct"]),
                "cost": estimate_cost(r["input_tokens"], r["output_tokens"],
                                      rate_in, rate_out),
                "input_tokens": r["input_tokens"],
                "output_tokens": r["output_tokens"],
            })
    return rows


def summarise(rows: list[dict]) -> None:
    """Per-model totals, to paste into SUBMISSION.md."""
    print(f"{'model':38}{'exact':>7}{'failed':>8}{'tokens':>9}{'cost $':>10}")
    print("-" * 72)
    for _, model in MODELS:
        mine = [r for r in rows if r["model"] == model]
        exact = sum(1 for r in mine if r.get("exact"))
        failed = sum(1 for r in mine if r.get("failed"))
        toks = sum(r.get("input_tokens", 0) + r.get("output_tokens", 0) for r in mine)
        cost = sum(r.get("cost", 0.0) for r in mine)
        print(f"{model:38}{exact:>7}{failed:>8}{toks:>9}{cost:>10.5f}")


if __name__ == "__main__":
    out = run_all()
    summarise(out)
    dest = Path(__file__).resolve().parent.parent / "outputs"
    dest.mkdir(exist_ok=True)
    (dest / "corrections.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwrote outputs/corrections.json ({len(out)} rows)")
