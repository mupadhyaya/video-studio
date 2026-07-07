"""
v3_engine/vscode_recorder.py

VS Code automation for V3 pipeline.

Opens VS Code with the lesson's code, gives it a moment to load,
then screen-records while using osascript to run the code via
VS Code's integrated terminal (Cmd+` then python <file>).

This produces a much more professional-looking recording than a raw terminal.
"""

import os
import subprocess
import tempfile
import time
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
PYTHON_BIN = str(REPO_ROOT / ".venv" / "bin" / "python")
PIP_BIN = str(REPO_ROOT / ".venv" / "bin" / "pip3")


def _auto_install_deps(code: str) -> list[str]:
    """Auto-install any missing imports before recording."""
    import re
    IMPORT_TO_PKG = {
        "langchain_core": "langchain-core",
        "langchain_community": "langchain-community",
        "langchain": "langchain",
        "langchain_openai": "langchain-openai",
        "faiss": "faiss-cpu",
        "sklearn": "scikit-learn",
        "cv2": "opencv-python",
        "PIL": "Pillow",
        "bs4": "beautifulsoup4",
        "yaml": "pyyaml",
        "dotenv": "python-dotenv",
    }
    pattern = re.compile(r"^\s*(?:import|from)\s+([\w\.]+)", re.MULTILINE)
    modules = set(m.split(".")[0] for m in pattern.findall(code))
    installed = []
    for module in modules:
        check = subprocess.run([PYTHON_BIN, "-c", f"import {module}"], capture_output=True)
        if check.returncode != 0:
            pkg = IMPORT_TO_PKG.get(module, module.replace("_", "-"))
            print(f"  [vscode_recorder] 📦 Installing: {pkg}")
            result = subprocess.run([PIP_BIN, "install", pkg, "-q"], capture_output=True, timeout=120)
            if result.returncode == 0:
                installed.append(pkg)
    return installed


def record_vscode_session(
    code: str,
    lesson_title: str,
    output_path: str,
    recording_duration: int = None,
) -> bool:
    """
    Open VS Code with the code file and screen-record the execution.

    Strategy:
    1. Write code to a temp .py file
    2. Open VS Code on that file
    3. Wait for VS Code to fully load
    4. Start screen recording
    5. Use osascript to open VS Code integrated terminal and run the file
    6. Wait for execution to finish
    7. Stop recording

    Args:
        code: Python code to write and run.
        lesson_title: Used as the VS Code window title / file comment.
        output_path: Where to save the .mov recording.
        recording_duration: Seconds to record. Auto-estimated if None.

    Returns:
        True if recording was saved.
    """
    # ── Pre-flight: install missing deps ─────────────────────────────────
    print(f"  [vscode_recorder] 🔍 Checking dependencies...")
    _auto_install_deps(code)

    # ── Write code file ───────────────────────────────────────────────────
    safe_title = lesson_title.replace("'", "").replace('"', "").replace("/", "-")
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".py",
        prefix="v3_lesson_",
        dir="/tmp",
        delete=False
    ) as f:
        header = f"# {lesson_title}\n# Understanding AIML — Video Demo\n\n"
        f.write(header + code)
        temp_script = f.name

    # ── Estimate recording duration ───────────────────────────────────────
    line_count = len(code.splitlines())
    if recording_duration is None:
        recording_duration = max(15, line_count // 2 + 10)

    print(f"  [vscode_recorder] 📄 Code: {temp_script}")
    print(f"  [vscode_recorder] ⏱️  Recording {recording_duration}s")

    # ── Open VS Code ──────────────────────────────────────────────────────
    vscode_bin = _find_vscode()
    if vscode_bin:
        subprocess.Popen([vscode_bin, temp_script])
        print(f"  [vscode_recorder] 💻 VS Code opened")
        time.sleep(4)  # Let VS Code fully load
    else:
        # Fallback to terminal if VS Code not found
        print("  [vscode_recorder] ⚠️  VS Code not found — falling back to Terminal")
        from v3_engine.live_recorder import record_code_execution
        return record_code_execution(code, lesson_title, output_path)

    # ── Start screen recording ────────────────────────────────────────────
    print(f"  [vscode_recorder] 🔴 Recording started -> {output_path}")
    recorder = subprocess.Popen(
        ["screencapture", "-V", str(recording_duration), output_path]
    )

    # ── Wait a moment then trigger VS Code terminal ───────────────────────
    time.sleep(2)

    # Use osascript to open VS Code integrated terminal and run the file
    run_in_vscode_applescript = f"""
tell application "Visual Studio Code"
    activate
end tell
delay 1
tell application "System Events"
    tell process "Code"
        -- Open integrated terminal with Ctrl+`
        keystroke "`" using {{control down}}
        delay 1.5
        -- Type the run command
        keystroke "{PYTHON_BIN} {temp_script}"
        key code 36  -- Enter
    end tell
end tell
"""
    subprocess.Popen(["osascript", "-e", run_in_vscode_applescript])

    # ── Wait for recording to finish ──────────────────────────────────────
    recorder.wait()

    # ── Clean up ──────────────────────────────────────────────────────────
    try:
        os.remove(temp_script)
    except Exception:
        pass

    if Path(output_path).exists():
        size_mb = Path(output_path).stat().st_size / (1024 * 1024)
        print(f"  [vscode_recorder] ✅ Saved ({size_mb:.1f} MB): {output_path}")
        return True
    else:
        print(f"  [vscode_recorder] ❌ Recording not found at {output_path}")
        return False


def _find_vscode() -> str | None:
    """Find VS Code binary on macOS."""
    candidates = [
        "/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code",
        "/usr/local/bin/code",
        "/opt/homebrew/bin/code",
    ]
    for path in candidates:
        if Path(path).exists():
            return path
    # Try which
    result = subprocess.run(["which", "code"], capture_output=True, text=True)
    if result.returncode == 0:
        return result.stdout.strip()
    return None


if __name__ == "__main__":
    test_code = '''
import time

print("=== RAG Retriever Chain Demo ===")
print()

# Simulate building a retriever
class SimpleRetriever:
    def __init__(self, documents):
        self.documents = documents
        print(f"✅ Loaded {len(documents)} documents into the retriever")

    def retrieve(self, query, top_k=3):
        print(f"\\n🔍 Querying: '{query}'")
        time.sleep(0.5)
        results = self.documents[:top_k]
        print(f"📄 Retrieved {len(results)} relevant chunks:")
        for i, doc in enumerate(results, 1):
            print(f"  [{i}] {doc[:60]}...")
        return results

docs = [
    "RAG combines retrieval systems with generative models to ground responses in facts.",
    "The retriever component uses vector embeddings to find semantically similar chunks.",
    "FAISS is a popular library for efficient approximate nearest neighbour search.",
    "LangChain's VectorStoreRetriever wraps any vector store with a retriever interface.",
]

retriever = SimpleRetriever(docs)
results = retriever.retrieve("How does RAG work?")

print("\\n✅ RAG retrieval pipeline complete!")
'''
    success = record_vscode_session(
        code=test_code,
        lesson_title="Lesson 12 — RAG Retriever Chain",
        output_path="/tmp/v3_vscode_test.mov",
    )
    print(f"\nResult: {'✅ PASSED' if success else '❌ FAILED'}")
