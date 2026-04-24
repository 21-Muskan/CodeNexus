"""
Language Detector
-----------------
Detects the programming language of a code snippet using
regex heuristics and keyword patterns.
"""

import re
from typing import Optional


# --- Heuristic rule sets per language ---

_CPP_PATTERNS = [
    r"#include\s*[<\"]",
    r"\b(int|void|char|float|double|bool|long|short|unsigned)\s+\w+\s*[\(\{;]",
    r"\bstd::",
    r"\bcout\b",
    r"\bcin\b",
    r"->",
    r"\bdelete\b",
    r"\bnew\b",
    r"\bnamespace\b",
    r"\btemplate\s*<",
    r"//.*|/\*[\s\S]*?\*/",
]

_PYTHON_PATTERNS = [
    r"^\s*def\s+\w+\s*\(",
    r"^\s*class\s+\w+\s*[:\(]",
    r"^\s*import\s+\w+",
    r"^\s*from\s+\w+\s+import\b",
    r"^\s*elif\b",
    r"print\s*\(",
    r":\s*$",              # colon at end of line (if/for/while/def blocks)
    r"^\s*#",             # Python comments
    r"\bself\.",
    r"\bTrue\b|\bFalse\b|\bNone\b",
    r"\blen\(",
    r"\brange\(",
    r"^\s*@\w+",          # decorators
]

_JAVASCRIPT_PATTERNS = [
    r"\bconst\b|\blet\b|\bvar\b",
    r"\bfunction\s+\w+\s*\(",
    r"=>\s*\{",           # arrow functions
    r"console\.(log|error|warn)\s*\(",
    r"===|!==",
    r"\bdocument\.",
    r"\bwindow\.",
    r"\brequire\s*\(",
    r"\bmodule\.exports\b",
    r"async\s+function|await\b",
    r"\.then\s*\(",
    r"\.catch\s*\(",
    r"\bundefined\b",
]

_JAVA_PATTERNS = [
    r"\bpublic\s+(static\s+)?\w+\s+\w+\s*\(",
    r"\bSystem\.out\.print",
    r"\bimport\s+java\.",
    r"\bpublic\s+class\s+\w+",
    r"\bprivate\s+\w+\s+\w+",
    r"\bnew\s+\w+\s*\(",
    r"\bString\[\]\s+args\b",
    r"\bvoid\s+main\s*\(",
    r"\bthrows\s+\w+",
    r"\bfinal\s+\w+",
    r"\binterface\s+\w+",
    r"@Override",
]


def _score_language(code: str, patterns: list) -> int:
    """Count how many patterns match in the code."""
    score = 0
    for pattern in patterns:
        if re.search(pattern, code, re.MULTILINE):
            score += 1
    return score


def detect_language(code: str, hint: Optional[str] = None) -> str:
    """
    Detect the programming language of a code snippet.

    Args:
        code:  The source code string.
        hint:  Optional user-provided hint (e.g., from UI language selector).
               Values: "cpp", "python", "javascript", "java".
               If hint is "auto" or None, detection runs automatically.

    Returns:
        One of: "cpp", "python", "javascript", "java", "unknown".
    """
    if hint and hint.lower() not in ("auto", "unknown", ""):
        return hint.lower()

    if not code or not code.strip():
        return "unknown"

    scores = {
        "cpp":        _score_language(code, _CPP_PATTERNS),
        "python":     _score_language(code, _PYTHON_PATTERNS),
        "javascript": _score_language(code, _JAVASCRIPT_PATTERNS),
        "java":       _score_language(code, _JAVA_PATTERNS),
    }

    best_lang = max(scores, key=scores.get)

    # Require at least 1 pattern hit to make a call (relaxed from 2)
    if scores[best_lang] < 1:
        return "unknown"

    return best_lang


def language_display_name(lang: str) -> str:
    """Return a human-friendly display name for a language code."""
    names = {
        "cpp":        "C++",
        "python":     "Python",
        "javascript": "JavaScript",
        "java":       "Java",
        "unknown":    "Unknown",
    }
    return names.get(lang, lang.capitalize())


def language_to_streamlit_highlight(lang: str) -> str:
    """Return the Streamlit/Pygments language string for st.code()."""
    mapping = {
        "cpp":        "cpp",
        "python":     "python",
        "javascript": "javascript",
        "java":       "java",
        "unknown":    "text",
    }
    return mapping.get(lang, "text")
