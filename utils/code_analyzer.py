"""
Code Analyzer Utilities
-----------------------
Helper functions for preparing code for LLM analysis and parsing responses.
Now supports multi-language: C++, Python, JavaScript, Java.
"""

import json
import re


def add_line_numbers(code: str) -> str:
    """Add line numbers to each line of the code snippet."""
    lines = code.split("\n")
    numbered = [f"{i + 1}: {line}" for i, line in enumerate(lines)]
    return "\n".join(numbered)


# ─── Language-specific bug category templates ────────────────────────────────

_BUG_CATEGORIES = {
    "cpp": """\
**Bug categories to check:**
- Wrong/misspelled function names (e.g., readHumanSeniority vs readHumSensor, iMeans vs iMeas)
- Wrong argument order (e.g., iClamp(high, low) should be iClamp(low, high))
- Values exceeding documented ranges.
- Wrong API calls (e.g., use execute() instead of burst()).
- Variable mismatches.
- Lifecycle errors (e.g., RDI_END before RDI_BEGIN).
- Pin name typos (e.g., "D0" vs "DO").
- Buffer overflows, null pointer dereferences, memory leaks.
- Uninitialized variables.""",

    "python": """\
**Bug categories to check:**
- NameError: using undefined variable names.
- IndexError: off-by-one errors or out-of-range list access.
- TypeError: wrong type passed to function (e.g., str + int).
- Indentation bugs that break logic flow.
- Missing return values in functions.
- Mutable default arguments (e.g., def f(x=[])).
- Infinite loops due to missing increments.
- Using is instead of == for value comparison.
- Unreachable code after return statements.
- Shadowing built-in names (e.g., list = [...]).""",

    "javascript": """\
**Bug categories to check:**
- Undefined variables or missing declarations.
- Using == instead of === (type coercion bugs).
- NaN comparison bugs (use Number.isNaN(), not x === NaN).
- var hoisting causing unexpected behavior (prefer let/const).
- Off-by-one errors in loops.
- Missing await for async operations.
- Callback hell or unhandled promise rejections.
- Mutating function arguments (side effects).
- Incorrect this binding in callbacks.
- Accidental global variable creation (missing var/let/const).""",

    "java": """\
**Bug categories to check:**
- NullPointerException: calling method on null reference.
- ArrayIndexOutOfBoundsException: off-by-one or unbounded index.
- String comparison with == instead of .equals().
- Integer division losing precision (assign to double without cast).
- Resource leaks: streams/connections not closed.
- Catching generic Exception instead of specific exceptions.
- Empty catch blocks that silently swallow errors.
- Unchecked type casts (ClassCastException risk).
- Missing break in switch statements (fall-through).
- Using deprecated API methods.""",

    "unknown": """\
**Bug categories to check:**
- Logic errors and wrong variable usage.
- Off-by-one errors in loops or array access.
- Null/undefined/uninitialized variable dereference.
- Resource leaks (file handles, connections not closed).
- Type mismatch or implicit coercion bugs.
- Unreachable code.
- Missing error handling.""",
}

_FEW_SHOT_EXAMPLES = {
    "cpp": """\
**FEW-SHOT EXAMPLES:**

Example 1:
Code: `2: rdi.pmux(4).module("02").readHumanSeniority().execute();`
Output: {"bug_lines": [2], "explanations": ["readHumanSeniority -> readHumSensor"], "corrected_code": "rdi.pmux(4).module(\\"02\\").readHumSensor().execute();"}

Example 2:
Code: `3: iClamp(50 mA, -50 mA);`
Output: {"bug_lines": [3], "explanations": ["iClamp args swapped"], "corrected_code": "iClamp(-50 mA, 50 mA);"}""",

    "python": """\
**FEW-SHOT EXAMPLES:**

Example 1:
Code: `3: result = lenght(my_list)`
Output: {"error_types": ["NameError"], "bug_lines": [3], "explanations": ["NameError: 'lenght' should be 'len'"], "corrected_code": "result = len(my_list)"}

Example 2:
Code: `5: for i in range(len(arr)):\\n6:     print(arr[i+1])`
Output: {"error_types": ["IndexError"], "bug_lines": [6], "explanations": ["IndexError: arr[i+1] goes out of bounds on last iter"], "corrected_code": "    print(arr[i])"}""",

    "javascript": """\
**FEW-SHOT EXAMPLES:**

Example 1:
Code: `2: if (user.role == "admin") { ... }`
Output: {"error_types": ["Type Coercion"], "bug_lines": [2], "explanations": ["Use === not == to avoid type coercion"], "corrected_code": "if (user.role === \\"admin\\") { ... }"}

Example 2:
Code: `4: if (result === NaN) return;`
Output: {"error_types": ["Logic Error"], "bug_lines": [4], "explanations": ["NaN !== NaN; use Number.isNaN()"], "corrected_code": "if (Number.isNaN(result)) return;"}""",

    "java": """\
**FEW-SHOT EXAMPLES:**

Example 1:
Code: `5: if (name == "Alice") { ... }`
Output: {"bug_lines": [5], "explanations": ["String comparison with == — use .equals()"], "corrected_code": "if (name.equals(\\"Alice\\")) { ... }"}

Example 2:
Code: `8: double avg = total / count;`
Output: {"bug_lines": [8], "explanations": ["Integer division — add (double) cast"], "corrected_code": "double avg = (double) total / count;"}""",

    "unknown": """\
**FEW-SHOT EXAMPLES:**

Example 1:
Code: `3: result = x / 0`
Output: {"bug_lines": [3], "explanations": ["Division by zero error"], "corrected_code": "if x != 0: result = x / divisor"}""",
}

TEST_GEN_SYSTEM_PROMPT = """\
You are an expert Software Developer in Test (SDET).
Your job is to generate a comprehensive list of test case inputs for the provided code snippet.
Instead of heavy unit testing frameworks, the user wants simple input variable assignments (LeetCode style).
You must:
1. Provide raw input variables and the expected output for each test case.
2. Include boundary conditions, edge cases, and the "happy path".
3. Provide ONLY raw text/code representing the inputs (wrapped in standard markdown code blocks). Do not include conversational text outside of comments.
"""

def build_test_generation_prompt(code: str, language: str, context: str = "", rag_docs: str = "") -> str:
    prompt = f"""\
Please generate a list of test cases (just the input variables and expected output) for the following {language} code.
Provide the test cases in a simple, easy-to-read format.

Example format:
// Case 1: Standard usage
nums = [2, 7, 11, 15]
target = 9
// Expected: [0, 1]

// Case 2: Boundary condition (empty)
nums = []
target = 0
// Expected: []

CODE TO TEST:
```
{code}
```
"""

    if context.strip():
        prompt += f"\nDEVELOPER CONTEXT / INTENT:\n{context}\n"
        
    if rag_docs.strip():
        prompt += f"\nTESTING PATTERNS / KNOWLEDGE BASE DOCS:\n{rag_docs}\n"

    prompt += """
Ensure you cover:
- Standard usage (the "happy path")
- Boundary conditions and edge cases
- Potential failure modes (e.g. invalid inputs, nulls, out of bounds)

IMPORTANT: Output ONLY the test cases inside a single markdown code block. Do not explain the tests before or after the code block. Add comments INSIDE the code block if you need to explain your reasoning.
"""
    return prompt


SECURITY_SYSTEM_PROMPT = """\
You are an Expert Application Security Engineer. Your job is to strictly analyze the provided code for security vulnerabilities.
You MUST output your findings in ONLY valid JSON format.
Do NOT include any markdown formatting, backticks, or conversational text outside of the JSON structure.

The JSON array must contain objects with the following keys:
- "vulnerability": (string) The name of the vulnerability (e.g., "SQL Injection (CWE-89)").
- "severity": (string) Must be one of: "Critical", "High", "Medium", "Low".
- "explanation": (string) How an attacker could exploit this specific code.
- "remediation": (string) Secure code demonstrating the fix.

If no vulnerabilities are found, return:
[
  {
    "vulnerability": "None",
    "severity": "Low",
    "explanation": "No obvious security vulnerabilities detected.",
    "remediation": ""
  }
]
"""

def build_security_prompt(code: str, language: str, security_context: str) -> str:
    prompt = f"""\
Analyze the following {language} code snippet for security vulnerabilities.

### SECURITY KNOWLEDGE BASE (Context):
{security_context}

### CODE TO ANALYZE:
{code}
"""
    return prompt


SMELL_SYSTEM_PROMPT = """\
You are an Expert Software Architect and Clean Code Advocate.
Your job is to strictly analyze the provided code for "Code Smells" (e.g., God Objects, Long Methods, Magic Numbers, Uncommunicative Names, Duplicate Logic, Inappropriate Intimacy).
You MUST output your findings in ONLY valid JSON format.
Do NOT include any markdown formatting, backticks, or conversational text outside of the JSON array.

The JSON array must contain objects with the following keys:
- "smell": (string) The name of the code smell (e.g., "Long Method", "Magic Number").
- "severity": (string) Must be one of: "High", "Medium", "Low".
- "description": (string) Explanation of why this is a smell and how it harms maintainability.
- "refactoring": (string) A cleanly refactored version of the code snippet fixing this specific smell.

If the code is perfectly clean, return:
[
  {
    "smell": "None",
    "severity": "Low",
    "description": "Code appears clean and maintainable.",
    "refactoring": ""
  }
]
"""

def build_smell_prompt(code: str, language: str, metrics: dict) -> str:
    prompt = f"""\
Analyze the following {language} code snippet for Code Smells and maintainability issues.

### STATIC METRICS & FLAGS:
{str(metrics)}

### CODE TO FIX:
{code}
"""
    return prompt


CONCEPT_EXTRACTION_PROMPT = """\
You are an Expert Software Architect. Analyze the provided code snippet and extract high-level architectural concepts, design patterns, and entity types.
You MUST output your findings as a strict JSON array of strings. 
Do NOT include any markdown formatting or conversational text.

Examples of good tags:
["File I/O", "Authentication", "Singleton Pattern", "Database Connection", "REST API", "Data Processing", "React Component"]

Example output:
[
  "Memory Management",
  "Error Handling"
]
"""

def build_concept_prompt(code: str, language: str) -> str:
    return f"""\
Extract the key concepts and architecture tags for the following {language} code.

### CODE TO ANALYZE:
{code}
"""


def build_analysis_prompt(
    numbered_code: str,
    context: str,
    rag_docs: str = "",
    static_errors: str = "",
    language: str = "cpp",
) -> str:
    """
    Build the LLM prompt for bug detection with language-specific categories.

    Args:
        numbered_code: Line-numbered code string.
        context:       User's description of what the code should do.
        rag_docs:      Retrieved documentation from RAG.
        static_errors: Output from the static analyzer (CppCheck, pyflakes, etc.).
        language:      Detected language code: "cpp", "python", "javascript", "java", "unknown".

    Returns:
        Full prompt string ready to send to the LLM.
    """
    lang = language.lower() if language else "unknown"
    if lang not in _BUG_CATEGORIES:
        lang = "unknown"

    lang_display = {
        "cpp": "C++",
        "python": "Python",
        "javascript": "JavaScript",
        "java": "Java",
        "unknown": "General",
    }.get(lang, lang.upper())

    # Static analysis tool name for display
    static_tool = {
        "cpp": "CppCheck",
        "python": "pyflakes",
        "javascript": "ESLint",
        "java": "Checkstyle/Heuristic",
        "unknown": "Static Analyzer",
    }.get(lang, "Static Analyzer")

    rag_section = ""
    if rag_docs and rag_docs.strip():
        rag_section = f"""
**Relevant Documentation (from knowledge base):**
{rag_docs}
"""

    static_section = ""
    if static_errors and static_errors.strip():
        static_section = f"""
**Static Analysis Findings ({static_tool}):**
{static_errors}
(Note: Use these findings as strong evidence, but verify them against the context.)
"""

    bug_categories = _BUG_CATEGORIES.get(lang, _BUG_CATEGORIES["unknown"])
    few_shot = _FEW_SHOT_EXAMPLES.get(lang, _FEW_SHOT_EXAMPLES["unknown"])

    context_section = f"**Context (what the code should do):** {context}\n" if context and context.strip() else ""

    return f"""You are an expert {lang_display} code reviewer and bug detector. Your job is to find ALL bugs — including logic errors, runtime errors, and bad practices — and provide the corrected code.

**Language:** {lang_display}
{context_section}{rag_section}
{static_section}
**Code to analyze:**
```{lang}
{numbered_code}
```

{bug_categories}

{few_shot}

**CRITICAL RULES:**
1. You MUST thoroughly check EVERY line. Do not skip any line.
2. Do NOT say "no bugs" unless you are 100% certain after checking each line carefully.
3. Logic bugs, off-by-one errors, wrong variable names, type mismatches, and semantic errors ALL count as bugs — not just syntax errors.
4. If static analysis reported issues above, those are confirmed bugs — include them.
5. Provide a short 1-3 word `error_types` classification array for the bugs found (e.g., ["SyntaxError"] or ["Logic Error", "NullPointer"]).
6. Explanations MUST be under 15 words each.
7. Report the exact line number for each bug.
8. Provide the COMPLETE corrected code snippet in `corrected_code`. Fix ALL bugs.
9. Under `detected_language`, state the programming language you identified (e.g., "Python", "C++", "Java", "JavaScript").
10. Respond with ONLY valid JSON — no markdown, no commentary, nothing else.

{{"detected_language": "LanguageName", "error_types": ["Short Error Category Name"], "bug_lines": [line_numbers], "explanations": ["short explanation per bug"], "corrected_code": "full corrected code snippet"}}"""


def parse_llm_response(response: str) -> dict:
    """Parse the LLM response into structured bug data."""
    default = {"detected_language": "", "error_types": [], "bug_lines": [], "explanations": [], "corrected_code": ""}

    if not response or not response.strip():
        return default

    text = response.strip()

    # Try to extract JSON from markdown code fences if present
    json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if json_match:
        text = json_match.group(1).strip()

    # Try to find a JSON object in the text
    json_obj_match = re.search(r"\{.*\}", text, re.DOTALL)
    if json_obj_match:
        text = json_obj_match.group(0)

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return _fallback_parse(response)

    detected_lang = data.get("detected_language", "")
    error_types = data.get("error_types", [])
    bug_lines = data.get("bug_lines", [])
    explanations = data.get("explanations", [])
    corrected_code = data.get("corrected_code", "")

    # Ensure it's never missing the key
    if not error_types and bug_lines:
        error_types = ["Bug"]

    # Ensure bug_lines are strings
    bug_lines = [str(line) for line in bug_lines]

    # Truncate long explanations
    explanations = [_truncate(e, max_words=15) for e in explanations]

    # Ensure lists are same length
    while len(explanations) < len(bug_lines):
        explanations.append("Bug detected")
    while len(bug_lines) < len(explanations):
        bug_lines.append("")

    return {
        "detected_language": detected_lang,
        "error_types": error_types,
        "bug_lines": bug_lines,
        "explanations": explanations,
        "corrected_code": corrected_code
    }


def _truncate(text: str, max_words: int = 15) -> str:
    """Truncate explanation to max_words."""
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words])


def _fallback_parse(response: str) -> dict:
    """Fallback parser when JSON extraction fails."""
    error_types = []
    bug_lines = []
    explanations = []
    corrected_code = ""

    # Extremely naive fallback for error types
    if "syntax" in response.lower():
        error_types.append("SyntaxError")
    elif "logic" in response.lower():
        error_types.append("Logic Error")
    else:
        error_types.append("Bug")

    line_pattern = re.compile(
        r"[Ll]ine\s+(\d+)\s*[:\-\u2013]\s*(.+?)(?:\n|$)", re.MULTILINE
    )
    for match in line_pattern.finditer(response):
        bug_lines.append(match.group(1))
        explanations.append(match.group(2).strip())

    # Try to find corrected code block
    code_match = re.search(
        r"Corrected Code:?\s*```(?:cpp|c|python|java|javascript|js)?\n?(.*?)```",
        response,
        re.DOTALL | re.IGNORECASE,
    )
    if code_match:
        corrected_code = code_match.group(1).strip()

    return {
        "detected_language": "",
        "error_types": error_types,
        "bug_lines": bug_lines,
        "explanations": explanations,
        "corrected_code": corrected_code
    }


def format_rag_docs(rag_results: list, max_docs: int = 5) -> str:
    """Format RAG search results into a clean documentation string."""
    if not rag_results:
        return ""

    sorted_docs = sorted(rag_results, key=lambda x: x.get("score", 0), reverse=True)
    top_docs = sorted_docs[:max_docs]

    parts = []
    for i, doc in enumerate(top_docs, 1):
        text = doc.get("text", "").strip()
        score = doc.get("score", 0)
        if text:
            parts.append(f"[Doc {i} (relevance: {score:.3f})]:\n{text}")

    return "\n\n".join(parts)
