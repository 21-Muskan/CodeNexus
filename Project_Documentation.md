# CodeNexus — Comprehensive Project Documentation

## 🌟 Executive Summary
**CodeNexus** is a state-of-the-art AI Code Intelligence Platform designed to act as a 24/7 "Senior Developer" companion. Unlike basic AI chatbots that often produce "hallucinations" or syntactically incorrect code, CodeNexus employs a **Hybrid Intelligence** model. It combines the rigorous precision of **Static Analysis** with the deep reasoning of **Large Language Models (LLMs)** and the domain expertise of **Retrieval-Augmented Generation (RAG)**.

The project is built to identify bugs, secure vulnerabilities, detect maintainability "smells," and help the developer grow through advanced performance tracking.

---

## 🛠️ Detailed Technology Stack & Integration

| Component | Technology | Specific Role in the Flow |
| :--- | :--- | :--- |
| **User Interface** | [Streamlit](https://streamlit.io/) | Provides the interactive dashboard, file upload management, and real-time result rendering. |
| **Orchestration** | Python 3.10+ | Coordinates the flow between detection, static analysis, RAG, and the LLM via `CodeNexusAgent`. |
| **AI "Brain"** | Qwen2.5-72B-Instruct | High-parameter model (72B) used for logic verification, code correction, and explanation generation. |
| **API Layer** | Hugging Face Hub | Secure communication with the hosted LLM via the V1 Chat Completions endpoint. |
| **Domain Knowledge** | [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) | Connects the agent to local vector databases (e.g., C++ RDI documentation) using the FastMCP server. |
| **Mistake Analytics** | [Scikit-Learn](https://scikit-learn.org/) | Powering the Learning Tracker with **K-Means Clustering** and **PCA (Principal Component Analysis)**. |
| **Text Semantics** | [Sentence-Transformers](https://sbert.net/) | Converts error explanations into vector embeddings (`all-MiniLM-L6-v2`) for mathematical clustering. |
| **Visualizations** | [Plotly](https://plotly.com/python/) | Renders interactive 3D/2D scatter plots of developer mistake clusters on the Learning Tracker page. |

---

## 🏗️ The System Flow (The "Nexus Engine")

The system follows a strictly defined 10-step pipeline for every analysis request:

1.  **UI Submission**: User submits code via one of the 6 specialized tabs in Streamlit.
2.  **Language Identification**:
    *   **Primary**: Regex heuristics scan for specific keywords (`std::`, `def`, `interface`, `const`).
    *   **Fallback**: If ambiguous, the LLM is instructed to identify the language during the processing phase.
3.  **Static Analysis Routing**: The code is routed to a language-specific analyzer to find "confirmed" errors:
    *   **C++**: Invokes `cppcheck` (detects style, performance, and portability issues).
    *   **Python**: Runs `pyflakes` (semantic checking) and a built-in syntax check.
    *   **JavaScript**: Attempts `ESLint` (`no-undef`, `unreachable`) or falls back to regex-based heuristics for `==` vs `===`.
    *   **Java**: A custom heuristic engine checks for `NullPointerExceptions` and string comparison errors (`==` vs `.equals()`).
4.  **RAG Context Retrieval**:
    *   If the language is C++, the system queries the **MCP Server**'s vector database.
    *   It retrieves documentation relevant to the user's intent to provide "industry-standard" context.
5.  **Prompt Engineering**: A massive prompt is built containing: **Context + RAG Docs + Static findings + Numbered code**.
6.  **AI Reasoning Pass**: The LLM reviews the code line-by-line, using the static analysis results as ground truth for syntax, focusing its "brainpower" purely on logic.
7.  **JSON Generation**: The LLM must respond in a rigid JSON format (Bug Line, Explanation, Error Type, Corrected Code).
8.  **Result Formatting**: Streamlit parses the JSON and generates color-coded cards (Red/Yellow/Cyan).
9.  **Mistake Logging**: The result is logged into a persistent local storage for the Learning Tracker.
10. **Analytics Update**: The tracker re-clusters the historical data, updating the user's growth chart.

---

## 🧩 Feature Deep-Dive: How They Work

### 1. Single Snippet Analysis (The Core Debugger)
The main hub for quick fixes.
*   **Static Layer**: Checks for uninitialized variables and syntax errors.
*   **AI Layer**: Detects deep logic flaws (e.g., off-by-one errors in loops).
*   **Outcome**: Highlighting specific line numbers and providing a "One-Click" fix.

### 2. Batch Code Analysis (Efficiency at Scale)
Designed for processing hundreds of code samples at once (e.g., analyzing a whole repository or a bug database).
*   **Mechanism**: Uses Python `asyncio` and `httpx` to process snippets in parallel, drastically reducing wait times.
*   **Input**: Supports CSV files with optional "Language" and "Context" hints.

### 3. Personal Learning Tracker (AI Mentor)
*   **The "Magic"**: Instead of just showing a list of past bugs, it uses AI to "group" them.
*   **Technique**: Sentence embeddings turn text explanations into 384-dimensional vectors. K-Means clustering identifies the most common error groups (e.g., "Memory Leaks" or "Logic Flow Issues").
*   **Unique Point**: It provides a visual 2D map of your coding habits.

### 4. AI Test Case Generator
*   **SDET Persona**: The AI acts as a dedicated tester.
*   **Coverage**: It identifies and generates tests for:
    *   **Happy Paths**: Standard expected inputs.
    *   **Boundary Conditions**: Null values, empty lists, maximum integers.
    *   **Error Handling**: Ensuring the code fails gracefully.

### 5. Security Vulnerability Scanner
*   **Persona**: AppSec Engineer.
*   **Knowledge Base**: Mapped to **OWASP Top 10** and **CWE** standards.
*   **Checks**: It specifically targets SQL Injections, Hardcoded Secrets, and unsafe deserialization.

### 6. Code Smell Detector
*   **Maintainability Focus**: It uses static metrics to calculate "Cyclomatic Complexity" (how hard the code is to read).
*   **Refactoring**: It suggests replacements for "God Objects," "Spaghetti Logic," and "Magic Numbers," aligning the code with **SOLID** principles.

---

## 💎 Why CodeNexus Stands Out

1.  **Hybrid Verification**: By combining static tools with AI, we ensure that the "Corrected Code" we provide actually runs and isn't just "mostly correct."
2.  **Visual Educational Loop**: CodeNexus is the only tool that maps your progress visually using machine learning, turning debugging into a learning journey.
3.  **Local Context Aware**: Through its **Model Context Protocol (MCP)** integration, it can be customized with internal team documentation, making its advice highly specific and proprietary-compliant.
4.  **Premium UX**: Designed with a sleek, dark-mode developer aesthetic, integrating **JetBrains Mono** font and high-contrast color coding for maximum readability.
