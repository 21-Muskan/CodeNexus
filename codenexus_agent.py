"""
Bug Hunter Agent Client (Agentic RAG Edition — Multi-Language)
--------------------------------------------------------------
MCP client that connects to the MCP server, uses `search_documents`
to fetch relevant documentation (RAG), runs language-appropriate static
analysis, then calls the Hugging Face Inference API to analyze code for bugs.

Supported languages: C++, Python, JavaScript, Java (auto-detected or user-specified).
"""

import os
import ast
import csv
import json
import asyncio
import argparse
import httpx
import pandas as pd
from dotenv import load_dotenv
from fastmcp import Client
from utils.code_analyzer import (
    add_line_numbers,
    build_analysis_prompt,
    parse_llm_response,
    format_rag_docs,
)
from utils.cpp_checker import check_code_snippet as check_cpp
from utils.python_checker import check_python_snippet
from utils.js_checker import check_js_snippet
from utils.java_checker import check_java_snippet
from utils.language_detector import detect_language, language_display_name

# Load environment variables
load_dotenv()

HF_API_KEY  = os.getenv("HF_API_KEY")
HF_MODEL_ID = os.getenv("HF_MODEL_ID", "Qwen/Qwen2.5-72B-Instruct")
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8003/sse")

# HF Router API endpoint (unified endpoint)
HF_API_URL = "https://router.huggingface.co/v1/chat/completions"


# ─── Static Analysis Router ──────────────────────────────────────────────────

def run_static_analysis(code: str, language: str) -> str:
    """
    Route code to the appropriate static analyzer based on detected language.

    Args:
        code:     Source code string.
        language: Detected language code ("cpp", "python", "javascript", "java").

    Returns:
        Static analysis findings as a formatted string, or empty string if none.
    """
    if language == "cpp":
        return check_cpp(code)
    elif language == "python":
        return check_python_snippet(code)
    elif language == "javascript":
        return check_js_snippet(code)
    elif language == "java":
        return check_java_snippet(code)
    else:
        # Unknown language — try Python syntax check as generic sanity check
        return check_python_snippet(code) or ""


# ─── Main Agent ──────────────────────────────────────────────────────────────

class CodeNexusAgent:
    """Agentic AI client: MCP tools + LLM + multi-language static analysis."""

    def __init__(self, server_url: str = MCP_SERVER_URL):
        self.server_url = server_url

    async def search_docs(self, mcp_client: Client, query: str) -> list:
        """Call MCP search_documents to retrieve relevant documentation."""
        try:
            result = await mcp_client.call_tool("search_documents", {"query": query})
            content_list = result.content if hasattr(result, "content") else []

            if content_list and len(content_list) > 0:
                raw_text = (
                    content_list[0].text
                    if hasattr(content_list[0], "text")
                    else str(content_list[0])
                )
                try:
                    docs = json.loads(raw_text) if isinstance(raw_text, str) else raw_text
                    if isinstance(docs, list):
                        return docs
                except (json.JSONDecodeError, ValueError):
                    try:
                        docs = ast.literal_eval(raw_text)
                        if isinstance(docs, list):
                            return docs
                    except Exception:
                        pass
            return []
        except Exception as e:
            print(f"    [WARN] search_documents failed: {e}")
            return []

    def call_llm(self, prompt: str) -> str:
        """Call Hugging Face Inference API via httpx."""
        headers = {
            "Authorization": f"Bearer {HF_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": HF_MODEL_ID,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 2048,   # Increased: LLM needs room for multi-bug explanations
            "temperature": 0.1,
        }

        with httpx.Client(timeout=120.0) as client:
            resp = client.post(HF_API_URL, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"]

            if isinstance(data, list) and len(data) > 0:
                return data[0].get("generated_text", str(data[0]))

            raise RuntimeError(f"Unexpected HF API response format: {json.dumps(data)[:200]}")

    async def analyze_entry(
        self,
        mcp_client: Client,
        entry_id: str,
        code: str,
        context: str,
        language_hint: str = "auto",
    ) -> dict:
        """
        Analyze a single code entry using RAG + language-specific Static Analysis + LLM.

        Args:
            mcp_client:    Connected FastMCP client.
            entry_id:      Unique ID for this entry (for tracking).
            code:          Source code snippet.
            context:       Natural language description of intent.
            language_hint: User-specified language or "auto" for detection.

        Returns:
            Dict with keys: ID, Language, Bug Line, Explanation, Corrected Code, RAG Docs.
        """
        try:
            # Step 1: Detect / confirm language
            language = detect_language(code, hint=language_hint)
            lang_name = language_display_name(language)
            print(f"    -> Language detected: {lang_name}")

            # Step 2: RAG — only useful for C++ (knowledge base is C++/RDI-specific).
            # For other languages the RAG docs are irrelevant and actively CONFUSE the LLM.
            rag_results = []
            rag_text = ""
            if language == "cpp":
                print(f"    -> Searching knowledge base for: '{context[:60]}...'")
                rag_results = await self.search_docs(mcp_client, context)
                # Filter out low-relevance docs (score < 0.5) to reduce noise
                rag_results = [d for d in rag_results if d.get("score", 0) >= 0.5]
                rag_text = format_rag_docs(rag_results, max_docs=5)
                print(
                    f"    -> Retrieved {len(rag_results)} relevant docs"
                    if rag_results
                    else "    -> No relevant docs found (score < 0.5)"
                )
            else:
                print(f"    -> Skipping RAG (knowledge base is C++-specific; language={lang_name})")

            # Step 3: Run language-specific static analysis
            print(f"    -> Running static analysis ({lang_name})...")
            static_errors = run_static_analysis(code, language)
            if static_errors:
                print(f"    -> Static analyzer detected issues:\n{static_errors}")
            else:
                print(f"    -> Static analysis passed (no issues found)")

            # Step 4: Add line numbers
            numbered_code = add_line_numbers(code)

            # Step 5: Build language-aware enriched prompt
            prompt = build_analysis_prompt(
                numbered_code, context, rag_text, static_errors, language=language
            )

            # Step 6: Call LLM
            print(f"    -> Calling LLM ({HF_MODEL_ID})...")
            response_text = self.call_llm(prompt)

            # Step 7: Parse response
            result = parse_llm_response(response_text)

            bug_lines    = result.get("bug_lines", [])
            explanations = result.get("explanations", [])
            corrected    = result.get("corrected_code", "")
            error_types  = result.get("error_types", [])
            llm_lang     = result.get("detected_language")

            # Fallback to LLM language detection if static was unknown
            final_lang = lang_name
            if language == "unknown" and llm_lang:
                final_lang = f"{llm_lang} (AI)"

            return {
                "ID":             entry_id,
                "Language":       final_lang,
                "Error Type":     "; ".join(error_types) if error_types else "Bug",
                "Bug Line":       ",".join(str(l) for l in bug_lines) if bug_lines else "",
                "Explanation":    "; ".join(explanations) if explanations else "No bugs detected",
                "Corrected Code": corrected,
                "RAG Docs":       rag_results,
            }

        except Exception as e:
            print(f"    ERROR: {e}")
            return {
                "ID":             entry_id,
                "Language":       language_display_name(detect_language(code, hint=None if str(language_hint).lower() == "nan" else language_hint)),
                "Error Type":     "System Error",
                "Bug Line":       "",
                "Explanation":    f"Error: {str(e)}",
                "Corrected Code": "",
                "RAG Docs":       [],
            }

    async def analyze_single_snippet(
        self, code: str, context: str = "", language_hint: str = "auto"
    ) -> dict:
        """Analyze a single snippet without ID (for UI use)."""
        async with Client(self.server_url) as mcp_client:
            return await self.analyze_entry(
                mcp_client, "UI_Request", code, context, language_hint=language_hint
            )

    async def chat_interaction(self, messages: list) -> str:
        """
        Handle a multi-turn chat interaction.
        `messages` is a list of dicts: [{"role": "user", "content": "..."}, ...]
        """
        from utils.code_analyzer import CHAT_SYSTEM_PROMPT
        
        # Build payload with system prompt included as first message
        payload_messages = [{"role": "system", "content": CHAT_SYSTEM_PROMPT}] + messages
        
        headers = {
            "Authorization": f"Bearer {HF_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": HF_MODEL_ID,
            "messages": payload_messages,
            "max_tokens": 2048,
            "temperature": 0.2, # slightly more creative for chat
        }

        print(f"    -> Calling Chat LLM ({HF_MODEL_ID})...")
        with httpx.Client(timeout=120.0) as client:
            resp = client.post(HF_API_URL, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"]
            raise RuntimeError(f"Unexpected API response format: {json.dumps(data)[:200]}")

    async def generate_test_cases(self, code: str, context: str = "", language_hint: str = "auto") -> str:
        """
        Generate a comprehensive suite of unit tests for the provided code snippet.
        """
        from utils.code_analyzer import TEST_GEN_SYSTEM_PROMPT, build_test_generation_prompt, format_rag_docs
        from utils.language_detector import detect_language
        from fastmcp import Client

        eff_lang = detect_language(code, hint=language_hint)
        
        rag_text = ""
        if eff_lang == "cpp" and context and self.server_url:
            try:
                async with Client(self.server_url) as mcp_client:
                    print("    -> Searching knowledge base for test patterns...")
                    rag_results = await self.search_docs(mcp_client, context)
                    rag_results = [d for d in rag_results if d.get("score", 0) >= 0.5]
                    rag_text = format_rag_docs(rag_results, max_docs=3)
            except Exception as e:
                print(f"    -> Warning: RAG query failed for test gen: {e}")

        user_prompt = build_test_generation_prompt(code, eff_lang, context, rag_text)

        messages = [
            {"role": "system", "content": TEST_GEN_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]

        headers = {
            "Authorization": f"Bearer {HF_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": HF_MODEL_ID,
            "messages": messages,
            "max_tokens": 2048,
            "temperature": 0.1, # Low temperature for accurate code generation
        }

        print(f"    -> Calling LLM for test generation ({HF_MODEL_ID})...")
        with httpx.Client(timeout=120.0) as client:
            resp = client.post(HF_API_URL, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"]
            raise RuntimeError(f"Unexpected API response format for test gen: {json.dumps(data)[:200]}")

    async def scan_for_vulnerabilities(self, code: str, language_hint: str = "auto") -> list:
        """
        Scan code for security vulnerabilities using the specialized RAG knowledge base.
        """
        from utils.code_analyzer import SECURITY_SYSTEM_PROMPT, build_security_prompt
        from utils.language_detector import detect_language
        from utils.security_rag import get_security_context
        
        eff_lang = detect_language(code, hint=language_hint)
        
        # Get security context from RAG
        print("    -> Searching security knowledge base...")
        security_context = get_security_context(code)
        
        user_prompt = build_security_prompt(code, eff_lang, security_context)
        
        messages = [
            {"role": "system", "content": SECURITY_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]
        
        headers = {
            "Authorization": f"Bearer {HF_API_KEY}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": HF_MODEL_ID,
            "messages": messages,
            "max_tokens": 1024,
            "temperature": 0.1,
            "response_format": {"type": "json_object"}
        }
        
        print(f"    -> Calling LLM for security scan ({HF_MODEL_ID})...")
        with httpx.Client(timeout=120.0) as client:
            resp = client.post(HF_API_URL, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            
            if "choices" in data and len(data["choices"]) > 0:
                content = data["choices"][0]["message"]["content"]
                try:
                    # Clean up purely to ensure we parse properly if the LLM output markdown blocks
                    if content.startswith("```json"):
                        content = content[7:-3]
                    elif content.startswith("```"):
                        content = content[3:-3]
                    
                    parsed = json.loads(content.strip())
                    # Ensure it's a list
                    if isinstance(parsed, dict):
                        if "vulnerabilities" in parsed:
                            parsed = parsed["vulnerabilities"]
                        else:
                            parsed = [parsed]
                    return parsed
                except json.JSONDecodeError as e:
                    print(f"Failed to parse LLM security output as JSON: {e}")
                    print(f"Raw output:\\n{content}")
                    raise RuntimeError("LLM failed to output valid JSON for security scan.")
            raise RuntimeError(f"Unexpected API response format for security scan: {json.dumps(data)[:200]}")

    async def detect_code_smells(self, code: str, language_hint: str = "auto") -> dict:
        """
        Analyze code for maintainability issues combining static metrics and LLM heuristic refactoring.
        """
        from utils.code_analyzer import SMELL_SYSTEM_PROMPT, build_smell_prompt
        from utils.language_detector import detect_language
        from utils.code_smells import get_static_metrics
        
        eff_lang = detect_language(code, hint=language_hint)
        
        print("    -> Calculating static code metrics...")
        metrics = get_static_metrics(code, eff_lang)
        
        user_prompt = build_smell_prompt(code, eff_lang, metrics)
        
        messages = [
            {"role": "system", "content": SMELL_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]
        
        headers = {
            "Authorization": f"Bearer {HF_API_KEY}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": HF_MODEL_ID,
            "messages": messages,
            "max_tokens": 1500,
            "temperature": 0.2, # Slightly creative for refactoring
            "response_format": {"type": "json_object"}
        }
        
        print(f"    -> Calling LLM for refactoring suggestions ({HF_MODEL_ID})...")
        with httpx.Client(timeout=120.0) as client:
            resp = client.post(HF_API_URL, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            
            if "choices" in data and len(data["choices"]) > 0:
                content = data["choices"][0]["message"]["content"]
                try:
                    if content.startswith("```json"):
                        content = content[7:-3]
                    elif content.startswith("```"):
                        content = content[3:-3]
                    
                    parsed = json.loads(content.strip())
                    
                    if isinstance(parsed, dict) and "smells" in parsed:
                        parsed = parsed["smells"]
                    elif isinstance(parsed, dict):
                        parsed = [parsed]
                        
                    return {
                        "metrics": metrics,
                        "smells": parsed
                    }
                except json.JSONDecodeError as e:
                    print(f"Failed to parse LLM smell output as JSON: {e}")
                    print(f"Raw output:\\n{content}")
                    raise RuntimeError("LLM failed to output valid JSON for code smells.")
            raise RuntimeError(f"Unexpected API response format for code smells: {json.dumps(data)[:200]}")

    async def extract_concepts(self, code: str, language_hint: str = "auto") -> list:
        """
        Extract architectural concepts and tags from a code snippet.
        """
        from utils.code_analyzer import CONCEPT_EXTRACTION_PROMPT, build_concept_prompt
        from utils.language_detector import detect_language
        
        eff_lang = detect_language(code, hint=language_hint)
        user_prompt = build_concept_prompt(code, eff_lang)
        
        messages = [
            {"role": "system", "content": CONCEPT_EXTRACTION_PROMPT},
            {"role": "user", "content": user_prompt}
        ]
        
        headers = {
            "Authorization": f"Bearer {HF_API_KEY}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": HF_MODEL_ID,
            "messages": messages,
            "max_tokens": 512,
            "temperature": 0.1,
            "response_format": {"type": "json_object"}
        }
        
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(HF_API_URL, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            
            if "choices" in data and len(data["choices"]) > 0:
                content = data["choices"][0]["message"]["content"]
                try:
                    if content.startswith("```json"):
                        content = content[7:-3]
                    elif content.startswith("```"):
                        content = content[3:-3]
                    
                    parsed = json.loads(content.strip())
                    
                    if isinstance(parsed, dict) and "concepts" in parsed:
                        return parsed["concepts"]
                    elif isinstance(parsed, list):
                        return parsed
                    return []
                except json.JSONDecodeError as e:
                    print(f"Failed to parse LLM concept output as JSON: {e}")
                    return []
            raise RuntimeError("Unexpected API response format for concept extraction.")

    async def process_csv(
        self,
        input_file: str,
        output_file: str = "data/output.csv",
        language_hint: str = "auto",
    ):
        """Process the input CSV and write results to output CSV."""
        print(f"\n{'='*60}")
        print(f"  CodeNexus Bug Hunter — Multi-Language Agentic Analyzer")
        print(f"{'='*60}")
        print(f"  Input:    {input_file}")
        print(f"  Output:   {output_file}")
        print(f"  Language: {language_hint.upper()}")
        print(f"  MCP:      {self.server_url}")
        print(f"  LLM:      {HF_MODEL_ID}")
        print(f"{'='*60}\n")

        df = pd.read_csv(input_file)
        print(f"Loaded {len(df)} entries from {input_file}\n")

        results = []

        async with Client(self.server_url) as mcp_client:
            print("Connected to MCP server!")
            tools = await mcp_client.list_tools()
            print(f"Available MCP tools: {[t.name for t in tools]}\n")

            for index, row in df.iterrows():
                entry_id = str(row["ID"])
                context  = str(row.get("Context", ""))
                code     = str(row.get("Code", ""))

                # Per-row language hint: if CSV has a "Language" column, use it
                row_lang = row.get("Language")
                if pd.isna(row_lang) or str(row_lang).lower() in ("nan", "", "unknown"):
                    row_lang = language_hint
                else:
                    row_lang = str(row_lang).strip()

                print(f"[{index + 1}/{len(df)}] Analyzing ID={entry_id}...")

                result = await self.analyze_entry(
                    mcp_client, entry_id, code, context, language_hint=row_lang
                )

                csv_result = {k: v for k, v in result.items() if k != "RAG Docs"}
                results.append(csv_result)

                if result["Bug Line"]:
                    print(f"    >> [{result['Language']}] Bugs at line(s): {result['Bug Line']}")
                    print(f"       {result['Explanation'][:120]}...")
                else:
                    print(f"    >> [{result['Language']}] No bugs detected")
                print()

        # Write results
        output_df = pd.DataFrame(results)
        os.makedirs(
            os.path.dirname(output_file) if os.path.dirname(output_file) else ".", exist_ok=True
        )
        columns = ["ID", "Language", "Bug Line", "Explanation", "Corrected Code"]
        cols_to_use = [c for c in columns if c in output_df.columns]
        output_df[cols_to_use].to_csv(output_file, index=False, quoting=csv.QUOTE_NONNUMERIC)

        # Summary
        bugs_found = sum(1 for r in results if r["Bug Line"])
        lang_counts = {}
        for r in results:
            lang_counts[r.get("Language", "Unknown")] = lang_counts.get(r.get("Language", "Unknown"), 0) + 1

        print(f"\n{'='*60}")
        print(f"  Analysis Complete!")
        print(f"{'='*60}")
        print(f"  Total entries:    {len(results)}")
        print(f"  Bugs detected in: {bugs_found} entries")
        for lang, count in lang_counts.items():
            print(f"  {lang} snippets:   {count}")
        print(f"  Results saved to: {output_file}")
        print(f"{'='*60}\n")

        return output_file


def main():
    parser = argparse.ArgumentParser(description="CodeNexus Bug Hunter — Multi-Language Agentic AI")
    parser.add_argument("--input",    required=True,              help="Input CSV file path")
    parser.add_argument("--output",   default="data/output.csv",  help="Output CSV file path")
    parser.add_argument("--server",   default=MCP_SERVER_URL,     help="MCP server SSE URL")
    parser.add_argument("--language", default="auto",
                        choices=["auto", "cpp", "python", "javascript", "java"],
                        help="Force a specific language (default: auto-detect)")

    args = parser.parse_args()
    agent = CodeNexusAgent(args.server)
    asyncio.run(agent.process_csv(args.input, args.output, language_hint=args.language))


if __name__ == "__main__":
    main()
