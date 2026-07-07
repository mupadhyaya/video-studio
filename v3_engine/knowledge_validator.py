"""
v3_engine/knowledge_validator.py

Validates lesson JSON content using Gemini API before video production.
Checks for:
  - Factually correct concepts
  - Code that is syntactically valid Python
  - Narration that matches the slide content
  - No hallucinated library names or incorrect API calls

Returns a validation report with any issues found.
"""

import json
import os
from pathlib import Path

from google import genai
from google.genai import types

REPO_ROOT = Path(__file__).parent.parent


def validate_lesson(lesson_json_path: str) -> dict:
    """
    Validate a lesson JSON file using Gemini.

    Args:
        lesson_json_path: Path to the lesson JSON.

    Returns:
        dict with keys:
          - 'passed': bool
          - 'issues': list of issue dicts {slide_index, severity, message, suggestion}
          - 'summary': str overall summary
    """
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("[validator] ⚠️  No GEMINI_API_KEY found — skipping validation.")
        return {"passed": True, "issues": [], "summary": "Skipped (no API key)"}

    client = genai.Client(api_key=api_key)
    model_name = "gemini-2.0-flash"

    with open(lesson_json_path) as f:
        lesson = json.load(f)

    slides = lesson.get("storyboard") or lesson.get("slides", [])
    lesson_title = lesson.get("meta_title") or lesson.get("title", "Unknown Lesson")

    print(f"[validator] 🔍 Validating: {lesson_title} ({len(slides)} slides)")

    prompt = f"""
You are an expert AI/ML educator and Python developer reviewing an educational video script.

Lesson: "{lesson_title}"
Number of slides: {len(slides)}

Below is the full lesson storyboard in JSON. Please review each slide and identify:

1. **Factual errors** — any incorrect AI/ML concept, wrong definition, or misleading explanation
2. **Code issues** — any Python code with syntax errors, wrong library names, or incorrect API usage
3. **Narration mismatches** — narration that doesn't match the slide's visual content
4. **Hallucinated references** — made-up function names, non-existent library methods, etc.

For each issue found, provide:
- slide_index (0-based integer)
- severity: "critical" | "warning" | "minor"
- message: clear description of the issue
- suggestion: how to fix it

Return your response as valid JSON in this exact format:
{{
  "passed": true/false,
  "issues": [
    {{
      "slide_index": 0,
      "severity": "critical",
      "message": "...",
      "suggestion": "..."
    }}
  ],
  "summary": "Overall assessment in 1-2 sentences."
}}

Set "passed" to false only if there are CRITICAL issues. Warnings and minor issues still pass.

Here is the storyboard:

{json.dumps(slides, indent=2, ensure_ascii=False)}
"""

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
        raw = response.text.strip()

        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        result = json.loads(raw.strip())

        issues = result.get("issues", [])
        passed = result.get("passed", True)
        summary = result.get("summary", "")

        print(f"[validator] {'✅ PASSED' if passed else '❌ FAILED'}: {summary}")
        if issues:
            for issue in issues:
                icon = "🔴" if issue["severity"] == "critical" else "🟡"
                print(f"  {icon} Slide {issue['slide_index']}: {issue['message']}")

        return result

    except Exception as e:
        print(f"[validator] ⚠️  Gemini validation error: {e}. Proceeding anyway.")
        return {"passed": True, "issues": [], "summary": f"Validation error: {e}"}


def apply_fixes(lesson_json_path: str, issues: list) -> bool:
    """
    For critical issues, ask Gemini to rewrite the affected slides.
    Updates the lesson JSON file in place.

    Args:
        lesson_json_path: Path to lesson JSON.
        issues: List of issue dicts from validate_lesson().

    Returns:
        True if any fixes were applied.
    """
    critical = [i for i in issues if i.get("severity") == "critical"]
    if not critical:
        return False

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return False

    client = genai.Client(api_key=api_key)
    model_name = "gemini-2.0-flash"

    with open(lesson_json_path) as f:
        lesson = json.load(f)

    slides = lesson.get("storyboard") or lesson.get("slides", [])
    modified = False

    for issue in critical:
        idx = issue.get("slide_index")
        if idx is None or idx >= len(slides):
            continue

        slide = slides[idx]
        print(f"[validator] 🔧 Fixing critical issue on slide {idx}...")

        fix_prompt = f"""
You are fixing a critical error in an AI/ML educational video slide.

Issue: {issue['message']}
Suggestion: {issue['suggestion']}

Current slide JSON:
{json.dumps(slide, indent=2, ensure_ascii=False)}

Please return the corrected slide JSON only, with the same keys and structure.
Fix ONLY the identified issue — don't change anything else.
Return valid JSON only, no markdown.
"""
        try:
            resp = client.models.generate_content(
                model=model_name,
                contents=fix_prompt,
            )
            raw = resp.text.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            fixed_slide = json.loads(raw.strip())
            slides[idx] = fixed_slide
            modified = True
            print(f"  ✅ Slide {idx} fixed.")
        except Exception as e:
            print(f"  ⚠️  Could not auto-fix slide {idx}: {e}")

    if modified:
        # Write back the fixed lesson
        key = "storyboard" if "storyboard" in lesson else "slides"
        lesson[key] = slides
        with open(lesson_json_path, "w") as f:
            json.dump(lesson, f, indent=2, ensure_ascii=False)
        print(f"[validator] ✅ Fixed lesson saved to {lesson_json_path}")

    return modified


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "rag_learning_series/lesson_012/lesson_012.json"
    result = validate_lesson(path)
    if not result["passed"] and result["issues"]:
        apply_fixes(path, result["issues"])
