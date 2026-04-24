# 🌟 CodeNexus — AI Code Intelligence Platform

**Eliminating Coding Hallucinations with Agentic AI + Static Analysis + RAG.**

CodeNexus is a state-of-the-art AI Code Intelligence Platform designed to act as a 24/7 "Senior Developer" companion. Unlike standard AI chatbots that often produce "hallucinations" or syntactically incorrect code, CodeNexus employs a **Hybrid Intelligence** model. It combines the rigorous precision of **Static Analysis** with the deep reasoning of **Large Language Models (LLMs)** and the domain expertise of **Retrieval-Augmented Generation (RAG)**.

![CodeNexus UI - Analysis View](UI/1.png)
![CodeNexus UI - Home Dashboard](UI/2.png)

---

## 🚀 Key Features

CodeNexus provides a comprehensive suite of tools for robust software development:

1. **Single Snippet Analysis (The Core Debugger)**
   - Hybrid verification using Static Analysis (`cppcheck`, `pyflakes`, etc.) and AI logic checks.
   - Detects syntax errors, uninitialized variables, and deep logic flaws (e.g., off-by-one errors).
2. **Batch Code Analysis**
   - Process hundreds of code samples at once using Python `asyncio` and `httpx`.
   - Supports CSV file uploads with optional language and context hints.
3. **Personal Learning Tracker (AI Mentor)**
   - Uses **Sentence Embeddings** and **K-Means Clustering** to analyze your past mistakes.
   - Visualizes your coding habits on an interactive 2D map.
4. **AI Test Case Generator**
   - Automatically generates test cases covering Happy Paths, Boundary Conditions, and Error Handling.
5. **Security Vulnerability Scanner**
   - Mapped to **OWASP Top 10** and **CWE** standards to detect SQL Injections, Hardcoded Secrets, etc.
6. **Code Smell Detector**
   - Calculates Cyclomatic Complexity and suggests refactoring based on **SOLID** principles.

---

## 🛠️ Tech Stack

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Brain** | **Qwen 2.5 72B Instruct** | High-parameter model used for logic verification and correction. |
| **Orchestrator** | **FastMCP** (Python) | Manages the agent loop, RAG, and tool execution. |
| **Knowledge** | **LlamaIndex** + **HuggingFace** | Vector database for RAG context retrieval. |
| **Static Analysis**| **CppCheck**, **Pyflakes**, Custom Heuristics | Multi-language static code analysis. |
| **Analytics** | **Scikit-Learn**, **Sentence-Transformers** | Powers the Learning Tracker's clustering and embeddings. |
| **Visualizations** | **Plotly** | Renders interactive plots for the Learning Tracker. |
| **Frontend** | **Streamlit** | Interactive web UI for developers. |

---

## ⚡ Quick Start

### Prerequisites
- Python 3.10+
- `cppcheck` installed and added to your system PATH (for C++ analysis).
- A generic Hugging Face API Token.

### Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/CodeNexus.git
   cd CodeNexus
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment**
   Create a `.env` file in the root directory:
   ```ini
   HF_API_KEY=your_huggingface_api_key
   HF_MODEL_ID=Qwen/Qwen2.5-72B-Instruct
   MCP_SERVER_URL=http://localhost:8003/sse
   ```

### Usage

**1. Start the MCP Server (Knowledge Base)**
This server handles RAG and embedding models.
```bash
python mcp_server.py
```

**2. Launch the CodeNexus UI**
In a new terminal:
```bash
streamlit run app.py
```
Open `http://localhost:8501` in your browser.

---

## 🧠 How It Works (The "Nexus Engine")

1. **Input**: User submits code via the Streamlit UI.
2. **Static Check**: The code is routed to a language-specific analyzer (`cppcheck`, `pyflakes`, etc.).
3. **RAG Lookup**: For specific languages/domains, the agent queries the MCP Server's vector DB for relevant documentation.
4. **LLM Synthesis**: The Agent prompts Qwen-72B with:
   - *Context + RAG Docs + Static findings + Numbered code.*
5. **Output & Analytics**: Results are displayed in the UI, and errors are logged/clustered in the Personal Learning Tracker.

---

## 📂 Project Structure

- `codenexus_agent.py`: The core agent logic (LLM + RAG + Static Analysis integration).
- `mcp_server.py`: FastMCP server handling vector embeddings and document search.
- `app.py`: Main Streamlit frontend application.
- `utils/cpp_checker.py`: Python wrapper for invoking CppCheck.
- `utils/code_analyzer.py`: Prompt engineering and response parsing.
- `data/`: Input/Output CSVs and persistent storage for analytics.
- `Project_Documentation.md`: Detailed system architecture and feature breakdown.

---

## 🏆 Acknowledgements

Built with ❤️ using **FastMCP**, **LlamaIndex**, **Streamlit**, and **Scikit-Learn**.
