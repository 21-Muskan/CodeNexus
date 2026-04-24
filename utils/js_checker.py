"""
JavaScript Static Analysis Wrapper
------------------------------------
Attempts to run ESLint on JavaScript code snippets. Gracefully degrades
to regex-based heuristic checks if Node.js or ESLint is not available.
"""

import os
import json
import subprocess
import tempfile


# Minimal ESLint config as JSON string (no .eslintrc required)
_ESLINT_CONFIG = {
    "env": {"browser": True, "es2021": True, "node": True},
    "parserOptions": {"ecmaVersion": 2021},
    "rules": {
        "no-undef": "warn",
        "no-unused-vars": "warn",
        "no-unreachable": "error",
        "eqeqeq": ["warn", "always"],
        "no-constant-condition": "warn",
        "no-dupe-keys": "error",
        "no-duplicate-case": "error",
        "use-isnan": "error",
        "valid-typeof": "error",
    },
}


def check_js_snippet(code: str) -> str:
    """
    Run ESLint on a JavaScript code snippet.

    Args:
        code: JavaScript code snippet as a string.

    Returns:
        Formatted string of errors/warnings, or empty string if none.
        Falls back to regex heuristics if ESLint/Node is unavailable.
    """
    js_file = None
    cfg_file = None

    try:
        # Write code to temp .js file
        with tempfile.NamedTemporaryFile(suffix=".js", delete=False, mode="w", encoding="utf-8") as f:
            f.write(code)
            js_file = f.name

        # Write eslint config to temp file
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w", encoding="utf-8") as f:
            json.dump(_ESLINT_CONFIG, f)
            cfg_file = f.name

        # Try running eslint
        result = subprocess.run(
            [
                "npx", "--yes", "eslint",
                "--no-eslintrc",
                "--config", cfg_file,
                "--format", "compact",
                js_file,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        raw = (result.stdout + result.stderr).strip()
        if not raw:
            return ""

        # Filter and clean output
        findings = []
        for line in raw.splitlines():
            if js_file and js_file in line:
                clean = line.replace(js_file, "<snippet>").strip()
                findings.append(clean)
            elif line.strip() and "npm warn" not in line.lower() and "npx" not in line.lower():
                findings.append(line.strip())

        return "\n".join(findings) if findings else ""

    except FileNotFoundError:
        # Node.js / npx not installed
        return _regex_check_js(code)

    except subprocess.TimeoutExpired:
        return "Warning: JavaScript static analysis timed out. Falling back to heuristics.\n" + _regex_check_js(code)

    except Exception as e:
        return f"Warning: ESLint unavailable ({e}). Heuristic analysis:\n" + _regex_check_js(code)

    finally:
        for p in [js_file, cfg_file]:
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass


def _regex_check_js(code: str) -> str:
    """
    Fallback: heuristic checks for common JS bugs using regex.
    """
    import re
    findings = []
    lines = code.splitlines()

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # == instead of === (loose equality)
        if re.search(r'\b==\b', stripped) and not re.search(r'===', stripped) and not stripped.startswith("//"):
            findings.append(f"<snippet>:{i}: [warning] Possible loose equality (== instead of ===)")

        # != instead of !==
        if re.search(r'\b!=\b', stripped) and not re.search(r'!==', stripped) and not stripped.startswith("//"):
            findings.append(f"<snippet>:{i}: [warning] Possible loose inequality (!= instead of !==)")

        # var instead of let/const
        if re.search(r'^\s*var\s+', line):
            findings.append(f"<snippet>:{i}: [warning] 'var' used — prefer 'let' or 'const'")

        # console.log left in code
        if re.search(r'console\.log\s*\(', stripped):
            findings.append(f"<snippet>:{i}: [info] console.log() statement found")

        # NaN comparison: x == NaN or x === NaN
        if re.search(r'===?\s*NaN|NaN\s*===?', stripped):
            findings.append(f"<snippet>:{i}: [error] NaN comparison — use isNaN() or Number.isNaN()")

        # Unreachable return (return followed by more non-comment code)
    return "\n".join(findings) if findings else ""
