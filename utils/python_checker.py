"""
Python Static Analysis Wrapper
------------------------------
Runs pyflakes on Python code snippets to find static analysis errors.
Uses the same interface as cpp_checker.py for easy swapping.
"""

import os
import subprocess
import sys
import tempfile


def check_python_snippet(code: str) -> str:
    """
    Run pyflakes on a Python code snippet and return formatted errors.

    Args:
        code: Python code snippet as a string.

    Returns:
        String containing formatted errors/warnings, or empty string if none.
        Falls back to a basic syntax check if pyflakes is unavailable.
    """
    # Write to a temporary .py file
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w", encoding="utf-8") as f:
        f.write(code)
        temp_path = f.name

    try:
        # --- Try pyflakes first ---
        result = subprocess.run(
            [sys.executable, "-m", "pyflakes", temp_path],
            capture_output=True,
            text=True,
            timeout=15,
        )

        raw_output = (result.stdout + result.stderr).strip()

        if not raw_output:
            # pyflakes found nothing; also do a syntax check via compile
            return _syntax_check(code)

        # Clean up temp path from output lines
        findings = []
        for line in raw_output.splitlines():
            if line.strip():
                clean = line.replace(temp_path, "<snippet>").strip()
                findings.append(clean)

        return "\n".join(findings)

    except FileNotFoundError:
        # pyflakes not installed — fall back to syntax check only
        return _syntax_check(code)

    except subprocess.TimeoutExpired:
        return "Warning: Python static analysis timed out."

    except Exception as e:
        return f"Warning: Python static analysis error: {e}"

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def _syntax_check(code: str) -> str:
    """
    Fallback: Use Python's built-in compile() for syntax error detection.

    Returns:
        Error string if syntax error found, empty string if clean.
    """
    try:
        compile(code, "<snippet>", "exec")
        return ""
    except SyntaxError as e:
        return f"<snippet>:{e.lineno}: [error] SyntaxError: {e.msg}"
    except Exception as e:
        return f"<snippet>: [error] {e}"
