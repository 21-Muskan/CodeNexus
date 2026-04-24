"""
Java Static Analysis Wrapper
-----------------------------
Performs heuristic static analysis on Java code snippets using regex and
AST-like pattern matching. Does NOT require a JDK or Maven installation.
Optionally invokes checkstyle if it is available on the system PATH.
"""

import os
import re
import subprocess
import tempfile


def check_java_snippet(code: str) -> str:
    """
    Analyze a Java code snippet for common bugs and style issues.

    Args:
        code: Java source code snippet as a string.

    Returns:
        Formatted string of issues found, or empty string if none.
    """
    findings = []

    # Try checkstyle first (optional, requires Java + checkstyle jar)
    checkstyle_result = _try_checkstyle(code)
    if checkstyle_result:
        findings.append(checkstyle_result)

    # Always run heuristic checks
    heuristic_result = _heuristic_check_java(code)
    if heuristic_result:
        findings.append(heuristic_result)

    return "\n".join(findings).strip()


def _try_checkstyle(code: str) -> str:
    """
    Try to run checkstyle if available. Returns empty string on failure.
    """
    java_file = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".java", delete=False, mode="w", encoding="utf-8") as f:
            f.write(code)
            java_file = f.name

        result = subprocess.run(
            ["checkstyle", "-c", "/google_checks.xml", java_file],
            capture_output=True,
            text=True,
            timeout=15,
        )
        raw = (result.stdout + result.stderr).strip()
        if not raw or "ERROR" not in raw.upper():
            return ""

        lines_out = []
        for line in raw.splitlines():
            if java_file and java_file in line:
                lines_out.append(line.replace(java_file, "<snippet>").strip())
        return "\n".join(lines_out)

    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        return ""
    finally:
        if java_file and os.path.exists(java_file):
            try:
                os.remove(java_file)
            except Exception:
                pass


def _heuristic_check_java(code: str) -> str:
    """
    Heuristic pattern-based checks for common Java bugs.
    """
    findings = []
    lines = code.splitlines()

    # Track brace balance
    open_braces = 0
    close_braces = 0

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # Skip full-line comments
        if stripped.startswith("//") or stripped.startswith("*"):
            continue

        # Brace counting
        open_braces  += stripped.count("{") - stripped.count("\\{")
        close_braces += stripped.count("}") - stripped.count("\\}")

        # Potential NullPointerException: calling method on uninitialized var
        null_assign = re.search(r'\b(\w+)\s*=\s*null\s*;', stripped)
        if null_assign:
            var_name = null_assign.group(1)
            # Check if used on next few lines
            context = "\n".join(lines[i:min(i+5, len(lines))])
            if re.search(rf'\b{re.escape(var_name)}\s*\.', context):
                findings.append(
                    f"<snippet>:{i}: [warning] '{var_name}' assigned null — potential NullPointerException"
                )

        # String comparison with == instead of .equals()
        if re.search(r'"[^"]*"\s*==|==\s*"[^"]*"', stripped):
            findings.append(
                f"<snippet>:{i}: [error] String compared with == — use .equals() instead"
            )

        # Catching generic Exception (bad practice)
        if re.search(r'catch\s*\(\s*Exception\s+\w+\s*\)', stripped):
            findings.append(
                f"<snippet>:{i}: [warning] Catching generic Exception — catch specific exceptions"
            )

        # Empty catch block
        if re.search(r'catch\s*\(.*\)\s*\{\s*\}', stripped):
            findings.append(
                f"<snippet>:{i}: [warning] Empty catch block — exception silently swallowed"
            )

        # Integer division assigned to double/float without cast
        if re.search(r'(double|float)\s+\w+\s*=\s*\d+\s*/\s*\d+\s*;', stripped):
            findings.append(
                f"<snippet>:{i}: [warning] Integer division result assigned to float/double — add cast (double)"
            )

        # Array access without bounds check (heuristic: arr[i] without if(i < arr.length))
        if re.search(r'\w+\[i\]', stripped) and "length" not in stripped and "size()" not in stripped:
            findings.append(
                f"<snippet>:{i}: [info] Array index access without visible bounds check"
            )

        # Missing semicolon at end of statement (very basic)
        is_statement = (
            not stripped.endswith("{")
            and not stripped.endswith("}")
            and not stripped.endswith("//")
            and not stripped.startswith("//")
            and not stripped.startswith("@")
            and not stripped.startswith("import")
            and not stripped.startswith("package")
            and len(stripped) > 2
            and re.match(r'^[\w\s\.\(\)"\']+$', stripped)
            and not stripped.endswith(";")
        )
        if is_statement:
            findings.append(
                f"<snippet>:{i}: [warning] Possible missing semicolon"
            )

    # Brace mismatch
    if open_braces != close_braces:
        findings.append(
            f"<snippet>: [error] Brace mismatch — {open_braces} open vs {close_braces} close braces"
        )

    return "\n".join(findings)
