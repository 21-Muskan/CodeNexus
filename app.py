"""
CodeNexus — Streamlit UI
-------------------------
AI-Powered Code Intelligence: Bug Detection · Batch Analysis ·
Learning Tracker · Test Generation · Security Scanner · Code Smells.
"""

import streamlit as st
import pandas as pd
import asyncio
import os
import json
from io import BytesIO
from codenexus_agent import CodeNexusAgent, MCP_SERVER_URL, HF_MODEL_ID
from utils.language_detector import detect_language, language_display_name, language_to_streamlit_highlight

# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CodeNexus — AI Code Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* ── Base ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background: #0a0e1a; }
    .main .block-container { padding-top: 0; max-width: 1200px; }

    /* ── Hero Banner ── */
    .hero-banner {
        background: linear-gradient(135deg, #0d1b3e 0%, #0a1628 40%, #12082a 100%);
        border: 1px solid #1e2d50;
        border-radius: 16px;
        padding: 2.2rem 2.5rem 1.8rem;
        margin-bottom: 1.5rem;
        position: relative;
        overflow: hidden;
    }
    .hero-banner::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: linear-gradient(90deg, #4f8ef7, #a855f7, #4f8ef7);
        background-size: 200% 100%;
        animation: shimmer 3s linear infinite;
    }
    @keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
    .hero-title {
        font-family: 'JetBrains Mono', monospace;
        font-size: 2.4rem; font-weight: 700; margin: 0;
        background: linear-gradient(90deg, #6ea8fe, #c084fc, #6ea8fe);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-size: 200% auto;
    }
    .hero-sub {
        color: #8b9cc8; font-size: 0.95rem;
        margin-top: 0.4rem; font-weight: 400;
    }
    .hero-chips { margin-top: 1rem; display: flex; gap: 0.5rem; flex-wrap: wrap; }
    .chip {
        background: rgba(79,142,247,0.1); border: 1px solid rgba(79,142,247,0.3);
        color: #6ea8fe; border-radius: 20px;
        padding: 3px 12px; font-size: 0.75rem; font-weight: 600;
        letter-spacing: 0.04em;
    }
    .chip.purple { background: rgba(168,85,247,0.1); border-color: rgba(168,85,247,0.3); color: #c084fc; }
    .chip.green  { background: rgba(52,211,153,0.1); border-color: rgba(52,211,153,0.3); color: #34d399; }
    .chip.red    { background: rgba(248,113,113,0.1); border-color: rgba(248,113,113,0.3); color: #f87171; }
    .chip.yellow { background: rgba(251,191,36,0.1);  border-color: rgba(251,191,36,0.3);  color: #fbbf24; }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1117 0%, #0a0e1a 100%);
        border-right: 1px solid #1a2332;
    }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 { color: #c9d1d9; font-family: 'Inter', sans-serif; }
    .sidebar-logo {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.4rem; font-weight: 700;
        background: linear-gradient(90deg, #6ea8fe, #c084fc);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .sidebar-feature-card {
        background: #111827; border: 1px solid #1f2937;
        border-radius: 8px; padding: 0.6rem 0.8rem;
        margin-bottom: 0.4rem; cursor: default;
        transition: border-color 0.2s;
    }
    .sidebar-feature-card:hover { border-color: #374151; }
    .sf-icon { font-size: 1rem; margin-right: 6px; }
    .sf-label { color: #9ca3af; font-size: 0.8rem; font-weight: 500; }

    /* ── Headings ── */
    h1 { color: #e5e7eb !important; }
    h2, h3 { color: #d1d5db; font-family: 'Inter', sans-serif; }
    p, li, .stMarkdown { color: #9ca3af; }

    /* ── Tab Bar ── */
    .stTabs [data-baseweb="tab-list"] {
        background: #111827;
        border-radius: 10px; gap: 2px; padding: 4px;
        border: 1px solid #1f2937;
    }
    .stTabs [data-baseweb="tab"] {
        color: #6b7280; border-radius: 7px;
        font-weight: 500; font-size: 0.85rem;
        padding: 8px 14px;
        transition: background 0.15s, color 0.15s;
    }
    .stTabs [data-baseweb="tab"]:hover { background: #1f2937; color: #e5e7eb; }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #1e3a5f, #2d1b69) !important;
        color: #93c5fd !important;
        border-bottom-color: transparent !important;
    }

    /* ── Buttons ── */
    .stButton > button {
        background: linear-gradient(135deg, #1d4ed8, #7c3aed);
        color: #fff; border: none; border-radius: 8px;
        font-weight: 600; font-size: 0.9rem; letter-spacing: 0.02em;
        padding: 0.5rem 1.4rem;
        transition: all 0.2s ease; box-shadow: 0 2px 8px rgba(29,78,216,0.3);
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #2563eb, #8b5cf6);
        transform: translateY(-1px); box-shadow: 0 6px 20px rgba(29,78,216,0.45);
    }
    .stButton > button[kind="secondary"] {
        background: #1f2937; border: 1px solid #374151; color: #9ca3af;
        box-shadow: none;
    }
    .stButton > button[kind="secondary"]:hover {
        background: #374151; color: #e5e7eb; transform: none;
    }

    /* ── Inputs ── */
    .stTextArea textarea, .stTextInput input {
        background: #111827 !important; color: #e5e7eb !important;
        border: 1px solid #1f2937 !important; border-radius: 8px !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.85rem !important;
    }
    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 2px rgba(59,130,246,0.2) !important;
    }

    /* ── Selectbox ── */
    [data-testid="stSelectbox"] > div > div {
        background: #111827; border: 1px solid #1f2937; border-radius: 8px; color: #e5e7eb;
    }

    /* ── Language badges ── */
    .lang-badge {
        display: inline-block; padding: 2px 10px;
        border-radius: 20px; font-size: 0.72rem; font-weight: 700;
        text-transform: uppercase; letter-spacing: 0.06em;
    }
    .lang-cpp        { background: rgba(79,142,247,0.15); color: #6ea8fe; border: 1px solid rgba(79,142,247,0.3); }
    .lang-python     { background: rgba(52,211,153,0.12); color: #34d399; border: 1px solid rgba(52,211,153,0.3); }
    .lang-javascript { background: rgba(251,191,36,0.12); color: #fbbf24; border: 1px solid rgba(251,191,36,0.3); }
    .lang-java       { background: rgba(248,113,113,0.12); color: #f87171; border: 1px solid rgba(248,113,113,0.3); }
    .lang-unknown    { background: #1c2030; color: #6b7280; border: 1px solid #374151; }

    /* ── Result cards ── */
    .result-card {
        background: #111827; border: 1px solid #1f2937;
        border-radius: 10px; padding: 1.2rem 1.4rem; margin-bottom: 1rem;
    }
    .result-card.success { border-left: 3px solid #34d399; }
    .result-card.error   { border-left: 3px solid #f87171; }
    .result-card.warning { border-left: 3px solid #fbbf24; }
    .result-card.info    { border-left: 3px solid #6ea8fe; }

    .section-header {
        color: #e5e7eb; font-size: 1.05rem; font-weight: 600;
        margin-bottom: 0.8rem; padding-bottom: 0.4rem;
        border-bottom: 1px solid #1f2937;
    }

    /* ── Code blocks ── */
    .stCode, pre { border: 1px solid #1f2937 !important; border-radius: 8px !important; }

    /* ── Metrics ── */
    [data-testid="stMetricValue"] { color: #93c5fd !important; font-weight: 700; }
    [data-testid="stMetricLabel"] { color: #6b7280 !important; }

    /* ── Divider ── */
    hr { border-color: #1f2937 !important; }

    /* ── Alerts ── */
    .stAlert { border-radius: 8px !important; border: 1px solid #1f2937 !important; }
    .stSuccess { background: rgba(52,211,153,0.08) !important; }
    .stError   { background: rgba(248,113,113,0.08) !important; }
    .stWarning { background: rgba(251,191,36,0.08) !important; }
    .stInfo    { background: rgba(79,142,247,0.08) !important; }

    /* ── Progress bar ── */
    [data-testid="stProgressBar"] > div { background: linear-gradient(90deg,#3b82f6,#8b5cf6) !important; border-radius: 4px; }

    /* ── Dataframe ── */
    [data-testid="stDataFrame"] { border: 1px solid #1f2937; border-radius: 8px; overflow: hidden; }

    /* ── Expander ── */
    [data-testid="stExpander"] { background: #111827 !important; border: 1px solid #1f2937 !important; border-radius: 8px !important; }
    [data-testid="stExpander"] summary { color: #9ca3af !important; }
</style>
""", unsafe_allow_html=True)


# ─── Language colour helper ───────────────────────────────────────────────────
_LANG_BADGE_CLASS = {
    "cpp": "lang-cpp", "python": "lang-python",
    "javascript": "lang-javascript", "java": "lang-java", "unknown": "lang-unknown",
}

def _lang_badge(lang_code: str) -> str:
    css_class = _LANG_BADGE_CLASS.get(lang_code, "lang-unknown")
    name = language_display_name(lang_code)
    return f'<span class="lang-badge {css_class}">{name}</span>'


# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-logo">⚡ CodeNexus</div>', unsafe_allow_html=True)
    st.caption("AI-Powered Code Intelligence")
    st.markdown("---")

    st.markdown("### 🌐 Language")
    LANGUAGE_OPTIONS = {
        "🔍 Auto-Detect": "auto",
        "C++": "cpp",
        "Python": "python",
        "JavaScript": "javascript",
        "Java": "java",
    }
    selected_lang_label = st.selectbox(
        "Select Language",
        list(LANGUAGE_OPTIONS.keys()),
        index=0,
        help="Auto-detect from code, or pin a specific language.",
    )
    selected_lang = LANGUAGE_OPTIONS[selected_lang_label]
    model_id   = HF_MODEL_ID
    server_url = MCP_SERVER_URL

    st.markdown("---")
    st.markdown("### 🗂️ Features")
    features = [
        ("🧩", "Snippet Analysis",   "Analyze a code snippet for bugs"),
        ("📂", "Batch Analysis",     "Upload a CSV for bulk scanning"),
        ("📈", "Learning Tracker",   "Track & cluster your mistakes"),
        ("🧪", "Test Generator",     "Auto-generate edge-case tests"),
        ("🛡️", "Security Scanner",  "OWASP / CWE vulnerability scan"),
        ("🧼", "Code Smell Detector","Detect smells & get refactors"),
    ]
    for icon, label, desc in features:
        st.markdown(
            f'<div class="sidebar-feature-card"><span class="sf-icon">{icon}</span>'
            f'<span class="sf-label"><strong style="color:#d1d5db">{label}</strong><br>{desc}</span></div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.caption(f"🤖 Model: `{HF_MODEL_ID.split('/')[-1]}`")
    st.caption("v4.0 · Multi-Language · Agentic RAG")


# ─── Hero Banner ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-banner">
  <div class="hero-title">⚡ CodeNexus</div>
  <div class="hero-sub">Agentic RAG Bug Detector — Static Analysis · LLM Reasoning · Security · Quality</div>
  <div class="hero-chips">
    <span class="chip">🧩 Bug Detection</span>
    <span class="chip purple">🛡️ Security Scan</span>
    <span class="chip green">📈 Learning Tracker</span>
    <span class="chip yellow">🧪 Test Generator</span>
    <span class="chip red">🧼 Code Smells</span>
    <span class="chip">📂 Batch Analysis</span>
  </div>
</div>
""", unsafe_allow_html=True)


# ─── Tabs ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🧩 Snippet Analysis",
    "📂 Batch Analysis",
    "📈 Learning Tracker",
    "🧪 Test Generator",
    "🛡️ Security Scanner",
    "🧼 Code Smells",
])


# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — Single Snippet Analysis
# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    st.markdown('<div class="section-header">🧩 Single Snippet Analysis</div>', unsafe_allow_html=True)
    st.markdown("<small style='color:#6b7280'>Paste any code snippet — CodeNexus runs static analysis + LLM reasoning to find bugs, explain them, and suggest a fix.</small>", unsafe_allow_html=True)
    st.write("")

    # Language indicator
    if selected_lang == "auto":
        st.caption("💡 Language will be auto-detected from your code")
    else:
        st.markdown(f"Selected language: {_lang_badge(selected_lang)}", unsafe_allow_html=True)

    _default_snippets = {
        "auto": """// C++ Example
void test() {
    int array[10];
    array[10] = 0;  // Buffer overflow
}""",
        "cpp": """// C++ Example
void test() {
    int array[10];
    array[10] = 0;  // Buffer overflow
}""",
        "python": """# Python Example
def calculate_average(numbers):
    total = 0
    for i in range(len(numbers) + 1):   # off-by-one
        total += numbers[i]
    return total / len(numbers)""",
        "javascript": """// JavaScript Example
function checkUser(user) {
    if (user.role == "admin") {   // loose equality
        return true;
    }
    if (result === NaN) return;   // NaN bug
}""",
        "java": """// Java Example
public class Example {
    public static void main(String[] args) {
        String name = null;
        if (name == "Alice") {   // wrong comparison
            System.out.println("Hello!");
        }
    }
}""",
    }

    highlight_lang = language_to_streamlit_highlight(selected_lang) if selected_lang != "auto" else "cpp"
    code_input = st.text_area(
        "Source Code",
        height=300,
        placeholder="Paste your code here...",
        value=_default_snippets.get(selected_lang, _default_snippets["auto"]),
    )

    # Auto-detect preview
    if selected_lang == "auto" and code_input.strip():
        preview_lang = detect_language(code_input)
        st.markdown(f"🔍 **Detected language:** {_lang_badge(preview_lang)}", unsafe_allow_html=True)
        highlight_lang = language_to_streamlit_highlight(preview_lang)
    elif selected_lang != "auto":
        highlight_lang = language_to_streamlit_highlight(selected_lang)
    else:
        highlight_lang = "text"

    if st.button("🚀 Analyze Snippet", type="primary", key="analyze_snippet"):
        if not code_input.strip():
            st.warning("⚠️ Please provide code to analyze.")
        else:
            eff_lang = detect_language(code_input, hint=selected_lang)
            lang_name = language_display_name(eff_lang)
            hl = language_to_streamlit_highlight(eff_lang)

            with st.spinner(f"⚡ Analyzing {lang_name} code… (Static Analysis → LLM)"):
                try:
                    agent = CodeNexusAgent(server_url)
                    result = asyncio.run(
                        agent.analyze_single_snippet(code_input, "", language_hint=selected_lang)
                    )
                    st.success("✅ Analysis Complete!")

                    result_lang = result.get("Language", lang_name)
                    error_type  = result.get("Error Type", "Bug")

                    # Meta row
                    st.markdown(
                        f"**Language:** {_lang_badge(eff_lang)} &nbsp;&nbsp;|&nbsp;&nbsp; "
                        f"**Error Type:** <span style='background:rgba(248,113,113,0.15);color:#f87171;"
                        f"padding:2px 10px;border-radius:20px;font-size:0.75rem;font-weight:700;border:1px solid rgba(248,113,113,0.3)'>{error_type}</span>",
                        unsafe_allow_html=True,
                    )
                    st.write("")

                    bugs = result.get("Bug Line")
                    if bugs:
                        st.markdown(f'<div class="result-card error">❌ <strong>Bug(s) found at line(s): {bugs}</strong><br><br>{result.get("Explanation","")}</div>', unsafe_allow_html=True)

                        # Save to learning history
                        import csv, datetime, uuid
                        os.makedirs("data", exist_ok=True)
                        history_path = "data/user_history.csv"
                        file_exists = os.path.isfile(history_path)
                        with open(history_path, mode="a", newline="", encoding="utf-8") as f:
                            writer = csv.writer(f)
                            if not file_exists:
                                writer.writerow(["Timestamp", "ID", "Code", "Language", "Error Type", "Explanation", "Corrected Code"])
                            uid = str(uuid.uuid4())[:8]
                            writer.writerow([
                                datetime.datetime.now().isoformat(), uid, code_input,
                                lang_name, error_type, result.get("Explanation"),
                                result.get("Corrected Code", "")
                            ])
                        st.toast("Mistake saved to your Learning Tracker! 💾", icon="📈")
                    else:
                        st.markdown(f'<div class="result-card success">✅ <strong>No bugs detected.</strong><br><br>{result.get("Explanation","")}</div>', unsafe_allow_html=True)

                    # Code comparison
                    st.markdown("### 🛠️ Code Comparison")
                    corrected_code = result.get("Corrected Code", "")
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.caption("📄 Original Code")
                        st.code(code_input, language=hl)
                    with col_b:
                        st.caption("✅ Suggested Fix")
                        if corrected_code:
                            st.code(corrected_code, language=hl)
                        else:
                            st.info("No correction needed — code looks clean.")

                    # Evidence
                    with st.expander("🔍 Evidence & Debug Info"):
                        st.markdown(f"**Effective Language:** {lang_name}")
                        if eff_lang != "cpp":
                            st.info("ℹ️ RAG search was skipped — the knowledge base only contains C++ docs. "
                                    "For Python/JS/Java, the LLM uses its own knowledge + static analysis only.")
                        else:
                            rag_docs = result.get("RAG Docs", [])
                            st.markdown("**RAG Documents Retrieved:**")
                            if rag_docs:
                                for i, doc in enumerate(rag_docs):
                                    st.markdown(f"**Doc {i+1}** (Score: {doc.get('score', 0):.3f})")
                                    st.code(doc.get("text", "")[:300] + "...", language="text")
                            else:
                                st.warning("No relevant C++ docs found.")

                        st.markdown("**Static Analysis Output:**")
                        from utils.language_detector import detect_language as _dl
                        from codenexus_agent import run_static_analysis
                        _eff = _dl(code_input, hint=selected_lang)
                        _static = run_static_analysis(code_input, _eff)
                        if _static:
                            st.code(_static, language="text")
                        else:
                            st.success("Static analyzer found no issues.")

                except Exception as e:
                    st.error(f"Analysis failed: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — Batch CSV Analysis
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    st.markdown('<div class="section-header">📂 Batch Code Analysis</div>', unsafe_allow_html=True)
    st.markdown("<small style='color:#6b7280'>Upload a CSV with columns <code>ID</code> and <code>Code</code> (and optionally <code>Language</code> or <code>Context</code>). The sidebar language applies globally; a per-row <code>Language</code> column overrides it.</small>", unsafe_allow_html=True)
    st.write("")

    uploaded_file = st.file_uploader(
        "Upload CSV", type="csv", key="batch_upload",
        help="Required columns: ID, Code. Optional: Language, Context",
    )

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.dataframe(df.head(), use_container_width=True)

        meta_col1, meta_col2 = st.columns(2)
        meta_col1.metric("Total Entries", len(df))
        if "Language" in df.columns:
            meta_col2.metric("Languages Found", df["Language"].nunique())

        if "Language" in df.columns:
            st.markdown("**Language distribution in CSV:**")
            st.bar_chart(df["Language"].value_counts())

        if st.button("▶️ Run Batch Analysis", type="primary", key="run_batch"):
            progress_bar  = st.progress(0)
            status_text   = st.empty()
            results       = []
            agent         = CodeNexusAgent(server_url)
            output_placeholder = st.empty()

            async def run_batch():
                from fastmcp import Client
                async with Client(server_url) as mcp_client:
                    for index, row in df.iterrows():
                        # Per-row language override
                        row_lang = row.get("Language")
                        if pd.isna(row_lang) or str(row_lang).lower() in ("nan", "", "unknown"):
                            row_lang = selected_lang
                        else:
                            row_lang = str(row_lang).strip()
                        status_text.text(
                            f"Analyzing ID {row['ID']} ({index + 1}/{len(df)}) — "
                            f"Language: {language_display_name(detect_language(str(row.get('Code', '')), hint=row_lang))}…"
                        )
                        res = await agent.analyze_entry(
                            mcp_client,
                            str(row["ID"]),
                            str(row.get("Code", "")),
                            str(row.get("Context", "")),
                            language_hint=row_lang,
                        )
                        csv_res = {k: v for k, v in res.items() if k != "RAG Docs"}
                        results.append(csv_res)
                        progress_bar.progress((index + 1) / len(df))
                        output_placeholder.dataframe(pd.DataFrame(results).tail(3), use_container_width=True)

            asyncio.run(run_batch())
            status_text.success("🎉 Batch Processing Complete!")

            final_df = pd.DataFrame(results)
            st.dataframe(final_df, use_container_width=True)

            if "Language" in final_df.columns:
                st.markdown("### 📊 Language Breakdown")
                st.bar_chart(final_df["Language"].value_counts())

            csv_bytes = final_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="⬇️ Download Results CSV",
                data=csv_bytes,
                file_name="codenexus_results.csv",
                mime="text/csv",
            )


# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — Personal Learning Tracker
# ─────────────────────────────────────────────────────────────────────────────
with tab3:
    st.markdown('<div class="section-header">📈 Personal Learning Tracker</div>', unsafe_allow_html=True)
    st.markdown("<small style='color:#6b7280'>Uses NLP + K-Means clustering to discover patterns in your coding mistakes over time. Analyze snippets in the Snippet Analysis tab to build your profile.</small>", unsafe_allow_html=True)
    st.write("")

    history_path = "data/user_history.csv"

    header_col1, header_col2 = st.columns([5, 1])
    with header_col2:
        if st.button("🗑️ Clear History", key="clear_history", help="Reset your learning progress"):
            if os.path.exists(history_path):
                os.remove(history_path)
                st.success("History cleared!")
                st.rerun()

    if not os.path.exists(history_path):
        st.markdown("""
<div class="result-card info">
  👋 <strong>Welcome to your Learning Tracker!</strong><br><br>
  You haven't logged any mistakes yet. Head over to the <strong>Snippet Analysis</strong> tab,
  analyze some buggy code, and your mistakes will automatically appear here for clustering & analysis.
</div>
""", unsafe_allow_html=True)
    else:
        ana_df = pd.read_csv(history_path)

        stat_col1, stat_col2, stat_col3 = st.columns(3)
        stat_col1.metric("Total Mistakes Logged", len(ana_df))
        if "Language" in ana_df.columns:
            stat_col2.metric("Languages Seen", ana_df["Language"].nunique())
        if "Error Type" in ana_df.columns:
            stat_col3.metric("Unique Error Types", ana_df["Error Type"].nunique())

        st.markdown("#### 📋 Recent Mistakes")
        st.dataframe(
            ana_df.tail(5)[["Timestamp", "Language", "Error Type", "Explanation"]].iloc[::-1],
            use_container_width=True,
        )

        if len(ana_df) < 2:
            st.warning("⚠️ Keep analyzing! You need at least 2 logged mistakes to run semantic clustering.")
        else:
            st.markdown("---")
            if st.button("🧠 Analyze My Mistakes", type="primary", key="cluster_mistakes"):
                with st.spinner("Generating Embeddings & Clustering…"):
                    try:
                        from utils.analytics import generate_bug_clusters
                        import plotly.express as px

                        results_c = generate_bug_clusters(ana_df)
                        cluster_df = results_c["df"]
                        top_types  = results_c["top_types"]
                        summary    = results_c["cluster_summary"]

                        if len(cluster_df) == 0:
                            st.success("✅ No bugs were detected in this dataset to cluster!")
                        else:
                            st.success(f"Clustered {len(cluster_df)} mistakes into {len(cluster_df['Cluster'].unique())} semantic groups!")

                            colA, colB = st.columns([2, 1])
                            with colA:
                                st.subheader("Your Personal Mistake Profile")
                                fig_scatter = px.scatter(
                                    cluster_df, x="x", y="y", color="Cluster",
                                    hover_data=["Language", "Error Type", "Explanation"],
                                    title="Mistakes Clustered by Similarity",
                                    labels={"x": "PCA 1", "y": "PCA 2"},
                                    color_discrete_sequence=px.colors.qualitative.Vivid,
                                )
                                fig_scatter.update_traces(marker=dict(size=11, opacity=0.85, line=dict(width=1, color='DarkSlateGrey')))
                                fig_scatter.update_layout(
                                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(17,24,39,0.8)',
                                    font=dict(color='#9ca3af'),
                                )
                                st.plotly_chart(fig_scatter, use_container_width=True)

                            with colB:
                                st.subheader("Most Frequent Errors")
                                if not top_types.empty:
                                    fig_bar = px.bar(
                                        x=top_types.values, y=top_types.index, orientation='h',
                                        title="Tags You Struggle With",
                                        labels={'x': "Count", 'y': "Error Type"},
                                        color_discrete_sequence=["#6ea8fe"],
                                    )
                                    fig_bar.update_layout(
                                        yaxis={'categoryorder': 'total ascending'},
                                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(17,24,39,0.8)',
                                        font=dict(color='#9ca3af'),
                                    )
                                    st.plotly_chart(fig_bar, use_container_width=True)
                                else:
                                    st.info("No explicit 'Error Type' tags found.")

                            st.markdown("### 🔍 Cluster Summaries")
                            for cluster_id, examples in summary.items():
                                with st.expander(f"**{cluster_id} — Example Mistakes**"):
                                    for ex in examples:
                                        st.markdown(f"- {ex}")

                    except ImportError as e:
                        st.error(f"Missing dependency: `{str(e)}`")
                    except Exception as e:
                        st.error(f"Analytics failed: {str(e)}")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 4 — AI Test Case Generator
# ─────────────────────────────────────────────────────────────────────────────
with tab4:
    st.markdown('<div class="section-header">🧪 AI Test Case Generator</div>', unsafe_allow_html=True)
    st.markdown("<small style='color:#6b7280'>Generate robust test cases covering boundary conditions, edge cases, and the happy path — for any function or class you paste.</small>", unsafe_allow_html=True)
    st.write("")

    test_col1, test_col2 = st.columns([1, 3])
    with test_col1:
        test_lang_hint = st.selectbox(
            "Target Language",
            ["auto", "python", "cpp", "javascript", "java"],
            index=0,
            key="test_lang_hint",
        )

    test_code_input = st.text_area(
        "Paste the function or class you want to test:",
        height=260,
        placeholder="def divide(a, b):\n    return a / b",
        key="test_code_input",
    )

    if st.button("⚙️ Generate Test Cases", type="primary", key="gen_tests"):
        if not test_code_input.strip():
            st.warning("⚠️ Please provide code to generate test cases for.")
        else:
            eff_lang = detect_language(test_code_input, hint=test_lang_hint)
            lang_name = language_display_name(eff_lang)
            hl = language_to_streamlit_highlight(eff_lang)

            with st.spinner(f"🧠 Generating test cases for {lang_name}…"):
                try:
                    agent = CodeNexusAgent(server_url)
                    test_suite_raw = asyncio.run(
                        agent.generate_test_cases(test_code_input, context="", language_hint=eff_lang)
                    )

                    st.success("✅ Test Cases Generated!")
                    st.markdown(f"**Language:** {_lang_badge(eff_lang)}", unsafe_allow_html=True)
                    st.write("")

                    # Strip markdown fences if LLM wrapped the output
                    clean_code = test_suite_raw
                    if clean_code.startswith("```"):
                        parts = clean_code.split("```")
                        if len(parts) >= 3:
                            block = parts[1]
                            if "\n" in block:
                                first_line, rest = block.split("\n", 1)
                                clean_code = rest if first_line.strip().isalnum() else block
                            else:
                                clean_code = block

                    st.code(clean_code.strip(), language=hl)

                except Exception as e:
                    st.error(f"❌ Test generation failed: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 5 — Security Vulnerability Scanner
# ─────────────────────────────────────────────────────────────────────────────
with tab5:
    st.markdown('<div class="section-header">🛡️ Security Vulnerability Scanner</div>', unsafe_allow_html=True)
    st.markdown("<small style='color:#6b7280'>Analyze code against the OWASP Top 10 and common CWEs using a specialized security RAG index. Detects injection flaws, buffer overflows, and unsafe practices.</small>", unsafe_allow_html=True)
    st.write("")

    sec_col1, sec_col2 = st.columns([1, 3])
    with sec_col1:
        sec_lang_hint = st.selectbox(
            "Target Language",
            ["auto", "python", "cpp", "javascript", "java"],
            index=0,
            key="sec_lang_hint",
        )

    sec_code_input = st.text_area(
        "Paste the code to scan for security vulnerabilities:",
        height=260,
        placeholder='cursor.execute("SELECT * FROM users WHERE username = \'" + user_input + "\'")',
        key="sec_code_input",
    )

    if st.button("🚨 Run Security Audit", type="primary", key="sec_audit"):
        if not sec_code_input.strip():
            st.warning("⚠️ Please provide code to scan.")
        else:
            eff_lang = detect_language(sec_code_input, hint=sec_lang_hint)
            lang_name = language_display_name(eff_lang)
            hl = language_to_streamlit_highlight(eff_lang)

            with st.spinner(f"🛡️ Scanning {lang_name} code for vulnerabilities…"):
                try:
                    agent = CodeNexusAgent(server_url)
                    vulns = asyncio.run(
                        agent.scan_for_vulnerabilities(sec_code_input, language_hint=eff_lang)
                    )

                    if not vulns or (len(vulns) == 1 and vulns[0].get("vulnerability", "").lower() == "none"):
                        st.markdown('<div class="result-card success">✅ <strong>No obvious security vulnerabilities detected.</strong> Code looks safe!</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="result-card error">⚠️ Found <strong>{len(vulns)}</strong> potential vulnerabilit{"y" if len(vulns) == 1 else "ies"}.</div>', unsafe_allow_html=True)
                        st.write("")

                        for i, vuln in enumerate(vulns):
                            sev = vuln.get("severity", "Medium").capitalize()
                            sev_color_map = {"Critical": "#f87171", "High": "#fb923c", "Medium": "#fbbf24", "Low": "#34d399"}
                            sev_color = sev_color_map.get(sev, "#6ea8fe")

                            with st.container():
                                st.markdown(
                                    f"**{i+1}. {vuln.get('vulnerability', 'Unknown Vulnerability')}** &nbsp;"
                                    f"<span style='background:rgba(0,0,0,0.2);color:{sev_color};"
                                    f"padding:2px 10px;border-radius:20px;font-size:0.75rem;"
                                    f"font-weight:700;border:1px solid {sev_color}40'>{sev}</span>",
                                    unsafe_allow_html=True,
                                )
                                with st.expander("🔎 Exploit Explanation", expanded=True):
                                    st.write(vuln.get("explanation", "No explanation provided."))
                                with st.expander("🔧 Remediation / Secure Code", expanded=True):
                                    rem_code = vuln.get("remediation", "")
                                    if rem_code:
                                        st.code(rem_code, language=hl)
                                    else:
                                        st.info("No remediation code provided.")
                                st.markdown("---")

                except Exception as e:
                    st.error(f"❌ Security audit failed: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 6 — Code Smell Detector
# ─────────────────────────────────────────────────────────────────────────────
with tab6:
    st.markdown('<div class="section-header">🧼 Code Smell Detector</div>', unsafe_allow_html=True)
    st.markdown("<small style='color:#6b7280'>Automated Senior Engineer Review: detect God Classes, Long Methods, Duplicate Code, and high Cyclomatic Complexity — get clean refactored suggestions.</small>", unsafe_allow_html=True)
    st.write("")

    smell_col1, smell_col2 = st.columns([1, 3])
    with smell_col1:
        smell_lang_hint = st.selectbox(
            "Target Language",
            ["auto", "python", "cpp", "javascript", "java"],
            index=0,
            key="smell_lang_hint",
        )

    smell_code_input = st.text_area(
        "Paste code to analyze for maintainability and smells:",
        height=260,
        placeholder="def do_everything():\n    # 50 lines of nested loops here...",
        key="smell_code_input",
    )

    if st.button("🧼 Analyze Code Quality", type="primary", key="smell_analyze"):
        if not smell_code_input.strip():
            st.warning("⚠️ Please provide code to analyze.")
        else:
            eff_lang = detect_language(smell_code_input, hint=smell_lang_hint)
            lang_name = language_display_name(eff_lang)
            hl = language_to_streamlit_highlight(eff_lang)

            with st.spinner(f"🧼 Analyzing {lang_name} complexity and smells…"):
                try:
                    agent = CodeNexusAgent(server_url)
                    response = asyncio.run(
                        agent.detect_code_smells(smell_code_input, language_hint=eff_lang)
                    )

                    metrics = response.get("metrics", {})
                    smells  = response.get("smells", [])

                    st.markdown(f"**Language:** {_lang_badge(eff_lang)}", unsafe_allow_html=True)
                    st.write("")
                    st.subheader("📊 Static Complexity Metrics")
                    met_col1, met_col2 = st.columns(2)
                    with met_col1:
                        c_val = metrics.get("Cyclomatic Complexity", "N/A")
                        st.metric("Cyclomatic Complexity",
                                  c_val.split(" ")[0] if " " in str(c_val) else c_val,
                                  delta="High" if "High" in str(c_val) else None,
                                  delta_color="inverse")
                    with met_col2:
                        is_dup = metrics.get("_is_duplicate", False)
                        msg    = metrics.get("Duplication", "Checked")
                        st.metric("Duplicate Code", "Yes ⚠️" if is_dup else "No ✅",
                                  delta="Found" if is_dup else "Clean",
                                  delta_color="inverse")
                        st.caption(msg)

                    st.markdown("---")
                    st.subheader("🤖 LLM Refactoring Suggestions")

                    if not smells or (len(smells) == 1 and smells[0].get("smell", "").lower() == "none"):
                        st.markdown('<div class="result-card success">✅ <strong>Code is clean and maintainable!</strong> No significant code smells detected.</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="result-card warning">⚠️ Found <strong>{len(smells)}</strong> Code Smell{"s" if len(smells) > 1 else ""}.</div>', unsafe_allow_html=True)
                        st.write("")

                        for i, smell in enumerate(smells):
                            sev = smell.get("severity", "Medium").capitalize()
                            sev_color_map = {"High": "#f87171", "Medium": "#fbbf24", "Low": "#34d399"}
                            sev_color = sev_color_map.get(sev, "#6ea8fe")

                            st.markdown(
                                f"**{i+1}. {smell.get('smell', 'Code Smell')}** &nbsp;"
                                f"<span style='background:rgba(0,0,0,0.2);color:{sev_color};"
                                f"padding:2px 10px;border-radius:20px;font-size:0.75rem;"
                                f"font-weight:700;border:1px solid {sev_color}40'>{sev}</span>",
                                unsafe_allow_html=True,
                            )
                            with st.expander("❓ Why is this a smell?", expanded=True):
                                st.write(smell.get("description", "No description provided."))
                            with st.expander("✨ Clean Refactored Code", expanded=True):
                                rem_code = smell.get("refactoring", "")
                                if rem_code:
                                    st.code(rem_code, language=hl)
                                else:
                                    st.info("No refactoring code provided.")
                            st.markdown("---")

                except Exception as e:
                    st.error(f"❌ Smell analysis failed: {e}")
