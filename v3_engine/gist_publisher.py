"""
v3_engine/gist_publisher.py

Publishes the final lesson code + architecture diagram to a GitHub Gist.
This runs after every lesson is compiled and serves as a permanent,
shareable code reference for viewers.
"""

import json
import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


def publish_lesson_to_gist(lesson_json_path: str) -> str | None:
    """
    Creates or updates a GitHub Gist with the lesson's code + architecture.

    Requires GITHUB_TOKEN environment variable (same token used in Actions).

    Args:
        lesson_json_path: Path to the lesson JSON file.

    Returns:
        The Gist URL if successful, None otherwise.
    """
    github_token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not github_token:
        print("[gist_publisher] ❌ No GITHUB_TOKEN found. Skipping Gist publish.")
        return None

    # Load lesson JSON
    with open(lesson_json_path) as f:
        lesson = json.load(f)

    lesson_title = lesson.get("title", "Untitled Lesson")
    lesson_id = Path(lesson_json_path).stem  # e.g. "lesson_012"

    # Collect all code snippets from slides
    all_code_blocks = []
    for slide in lesson.get("slides", []):
        content = slide.get("content", "")
        slide_type = slide.get("type", "")
        if slide_type == "code_demo" and content:
            all_code_blocks.append(
                f"# === Slide: {slide.get('title', 'Code')} ===\n{content}\n"
            )

    if not all_code_blocks:
        print("[gist_publisher] No code slides found in lesson. Skipping.")
        return None

    combined_code = "\n\n".join(all_code_blocks)

    # Build architecture summary from diagram slide
    arch_summary = ""
    for slide in lesson.get("slides", []):
        if slide.get("type") == "architecture_diagram":
            arch_summary = f"# Architecture: {slide.get('title', '')}\n\n"
            for item in slide.get("diagram_items", []):
                arch_summary += f"## {item.get('label', '')}\n{item.get('description', '')}\n\n"
            break

    readme_md = f"""# {lesson_title}

> Auto-generated from [video-studio](https://github.com/mupadhyaya/video-studio) · Lesson `{lesson_id}`

## Overview
{lesson.get('description', lesson_title)}

---
{arch_summary}
## Full Source Code
See `{lesson_id}_code.py` in this Gist.
"""

    # Build Gist payload
    gist_description = f"[video-studio] {lesson_title} - Code & Architecture"
    files = {
        f"{lesson_id}_code.py": {"content": combined_code},
        f"{lesson_id}_README.md": {"content": readme_md},
    }

    payload = json.dumps({
        "description": gist_description,
        "public": True,
        "files": files,
    })

    # Call GitHub API to create Gist
    curl_cmd = [
        "curl", "-s",
        "-H", f"Authorization: token {github_token}",
        "-H", "Content-Type: application/json",
        "-d", payload,
        "https://api.github.com/gists"
    ]

    result = subprocess.run(curl_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[gist_publisher] ❌ curl failed: {result.stderr}")
        return None

    response = json.loads(result.stdout)
    gist_url = response.get("html_url")

    if gist_url:
        print(f"[gist_publisher] ✅ Gist published: {gist_url}")
        return gist_url
    else:
        error = response.get("message", "Unknown error")
        print(f"[gist_publisher] ❌ GitHub API error: {error}")
        return None


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python gist_publisher.py <lesson.json>")
        sys.exit(1)
    url = publish_lesson_to_gist(sys.argv[1])
    if url:
        print(f"\n🔗 Gist URL: {url}")
