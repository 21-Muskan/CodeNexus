"""
CppCheck Static Analysis Wrapper
--------------------------------
Runs cppcheck on code snippets to find static analysis errors.
"""

import os
import subprocess
import tempfile
import re

def check_code_snippet(code: str) -> str:
    """Run cppcheck on a code snippet and return formatted errors.
    
    Args:
        code: C++ code snippet.
        
    Returns:
        String containing formatted errors/warnings, or empty string if none.
    """
    # Create a temporary file with .cpp extension
    with tempfile.NamedTemporaryFile(suffix=".cpp", delete=False, mode="w") as f:
        f.write(code)
        temp_path = f.name

    try:
        # Run cppcheck
        # --enable=style,warning,performance,portability: Enable useful checks
        # --inconclusive: Report even if not 100% sure (good for snippets)
        # --template: Custom output format
        # --suppress=missingInclude: Don't fail on missing headers (since it's a snippet)
        cmd = [
            "cppcheck",
            "--enable=style,warning,performance,portability",
            "--inconclusive",
            "--template={line}: [{severity}] {message}",
            "--suppress=missingInclude",
            "--suppress=unusedFunction",  # Snippets often have unused functions
            temp_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # stderr contains the issues usually
        output = result.stderr.strip()
        
        # Filter and format output
        findings = []
        for line in output.split('\n'):
            if line.strip() and not line.startswith("Checking"):
                # Clean up the output (remove filename if present)
                # The template is {line}: [{severity}] {message}
                # But sometimes it might include path
                clean_line = line.replace(temp_path, "").strip()
                findings.append(clean_line)
                
        return "\n".join(findings) if findings else ""
        
    except Exception as e:
        return f"Error running cppcheck: {e}"
        
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
