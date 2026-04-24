import ast
import os
import textwrap
from typing import Dict, Any, Tuple
from utils.semantic_search import semantic_search

def calculate_python_complexity(code: str) -> int:
    """
    Calculates the Cyclomatic Complexity of a snippet of Python code.
    Base complexity is 1. Adds 1 for every decision point (If, For, While, And, Or, Except, With).
    Returns -1 if the code is invalid Python.
    """
    try:
        # We wrap it just in case it's a raw block that needs parsing
        tree = ast.parse(code)
    except SyntaxError:
        try:
            tree = ast.parse(textwrap.dedent(code))
        except SyntaxError:
            return -1

    complexity = 1
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.IfExp, ast.For, ast.While, ast.ExceptHandler, ast.With, ast.AsyncFor, ast.AsyncWith)):
            complexity += 1
        elif isinstance(node, ast.BoolOp):
            # A and B and C -> 2 decision points
            complexity += len(node.values) - 1
            
    return complexity

def detect_duplicates(code: str, threshold: float = 0.85) -> Tuple[bool, str]:
    """
    Uses the local semantic search index to find if identical or near-identical logic
    exists elsewhere in the codebase.
    Returns (is_duplicate, duplicate_context_string).
    """
    try:
        # Search for the same logic block
        results = semantic_search(code, top_k=2)
        
        # Semantic search will almost always return the exact snippet if it's currently indexed.
        # So we look at matches > threshold.
        duplicates = [r for r in results if r["similarity"] > threshold]
        
        if len(duplicates) > 0:
            msg = f"Found {len(duplicates)} similar code block(s) in the semantic index. (Top match: {duplicates[0]['file_path']}:L{duplicates[0]['start_line']} with {duplicates[0]['similarity']:.2f} similarity)"
            return True, msg
        else:
            return False, "No duplicates detected in the semantic index."
            
    except FileNotFoundError:
        return False, "Semantic index not found. Build the codebase index (Tab 7) to enable duplicate detection."
    except Exception as e:
        return False, f"Duplicate detection failed: {str(e)}"

def get_static_metrics(code: str, language: str) -> Dict[str, Any]:
    """Gather hybrid metrics before calling the LLM."""
    metrics_report = {}
    
    # AST Metrics
    if language == "python":
        comp = calculate_python_complexity(code)
        if comp == -1:
            metrics_report["Cyclomatic Complexity"] = "N/A (Syntax Error)"
        elif comp <= 5:
            metrics_report["Cyclomatic Complexity"] = f"{comp} (Low / Good)"
        elif comp <= 10:
            metrics_report["Cyclomatic Complexity"] = f"{comp} (Medium / Acceptable)"
        else:
            metrics_report["Cyclomatic Complexity"] = f"{comp} (High / Needs Refactoring)"
    else:
        # Very naive line-counting heuristics for other languages for now
        lines = len(code.splitlines())
        if lines > 50:
             metrics_report["Cyclomatic Complexity"] = "High (Estimated by Line Count)"
        else:
             metrics_report["Cyclomatic Complexity"] = "Low (Estimated by Line Count)"

    # Duplicate Detection
    is_dup, dup_msg = detect_duplicates(code)
    metrics_report["Duplication"] = dup_msg
    metrics_report["_is_duplicate"] = is_dup

    return metrics_report
