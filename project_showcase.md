# 🕷️ Bug Hunter Agent - Project Showcase & Judge's Guide

## 🚀 One-Line Pitch
**"An Agentic AI that doesn't just guess code fixes—it proves them using Static Analysis and RAG-based knowledge retrieval."**

---

## 🛠️ Tech Stack & Architecture

This project uses a **Compound AI System** architecture, combining deterministic tools with probabilistic LLMs for maximum accuracy.

| Component | Tech Stack | Role |
| :--- | :--- | :--- |
| **Orchestrator** | **Python 3.10+**, **FastMCP** | Managing the agent loop and tool calling. |
| **Brain (LLM)** | **Qwen 2.5 72B Instruct** | High-logic reasoning model (better than Llama 3.1 for code). |
| **Knowledge Base (RAG)** | **LlamaIndex**, **HuggingFace Embeddings** | Retrieving RDI/SmartRDI documentation context. |
| **Static Analysis** | **CppCheck** | Deterministic error checking (Catching bugs *before* the LLM). |
| **Frontend** | **Streamlit** | Interactive UI with diff viewers and batch processing. |
| **Communication** | **MCP (Model Context Protocol)** | Standardized protocol connecting the Agent to Tools. |

---

## 🧠 Logic Flow (How it Works)

The system works in a specific **Agentic Pipeline** for every single code snippet:

1.  **Context Retrieval (RAG)**
    *   **Input**: User's "Context" string (e.g., "Setup vector port 1").
    *   **Action**: The Agent calls the MCP tool `search_documents`.
    *   **Logic**: It converts the query into a vector embedding and finds the top 5 most relevant documentation chunks from the knowledge base.
    *   **Why**: This teaches the LLM proprietary APIs (like `rdi.smartVec()`) that it *never* saw during training.

2.  **Deterministic Verification (Static Analysis)**
    *   **Input**: The raw C++ code.
    *   **Action**: The Agent runs `CppCheck` on the snippet.
    *   **Logic**: It mathematically proves errors like "Buffer Overflow", "Null Pointer Dereference", or "Syntax Error".
    *   **Why**: LLMs can hallucinate; CppCheck *cannot*. This provides a "Ground Truth" layer.

3.  **Synthesized Reasoning (LLM Analysis)**
    *   **Input**: `Code` + `Context` + `RAG Docs` + `Static Analysis Findings`.
    *   **Prompting**: We use a dynamic few-shot prompt that incorporates all the above evidence.
    *   **Action**: The LLM (Qwen 72B) acts as a Judge, correcting the code based on the evidence.
    *   **Output**: Structured JSON containing `Bug Lines`, `Concise Explanation`, and `Corrected Code`.

4.  **Presentation (UI)**
    *   **Action**: Streamlit renders the JSON.
    *   **Feature**: A Diff Viewer shows the "Before" vs "After" code side-by-side for instant verification.

---

## 🏆 Why This Project Wins (Judging Criteria)

Here is how to sell this to the judges:

### 1. "It's not just a Wrapper"
*   **Pitch**: "Most AI coding tools just wrap GPT-4. We built a **System**. We integrated an industrial-grade static analyzer (`CppCheck`) and a local RAG server via MCP. The AI isn't just writing code; it's using tools like a human engineer."

### 2. "We Solved the Hallucination Problem"
*   **Pitch**: "LLMs often make up APIs. Our agent uses **RAG** to fetch the *exact* documentation for the `SmartRDI` library, ensuring it uses the correct function names (e.g., correcting `readHumanSeniority` to `readHumSensor`). We don't guess; we look it up."

### 3. "It Scales"
*   **Pitch**: "We built this with **Batch Processing** in mind. You can upload a CSV with 1,000 entries, and the agent will asynchronously process them using the MCP server, generating a report in minutes. It's enterprise-ready."

### 4. "It's Interactive"
*   **Pitch**: "We didn't stop at a CLI. The **Streamlit UI** allows developers to interact with the agent, see the rationale (RAG docs), and verify the fix with a visual diff. It fits into a developer's existing workflow."

---

## 🎤 Demo Script for Judges

1.  **Start with the Problem**: "Proprietary embedded APIs are hard. Developers make typos like `D0` vs `DO` or call functions in the wrong order."
2.  **Show the Solution**: Open the Streamlit UI.
3.  **Live Demo**: Paste a buggy snippet (e.g., the `D0` vs `DO` pin mismatch).
4.  **The "Magic" Moment**:
    *   Show the **Static Analysis** finding (CppCheck catching the issue).
    *   Show the **RAG Docs** (The agent finding the doc for that specific pin).
    *   Show the **Diff View** (The code automatically fixed).
5.  **Closing**: "This is Bug Hunter: An agent that knows your codebase better than you do."
