import json
import re
from datetime import datetime
from typing import Dict, List, Optional

import streamlit as st


# Utils
def slugify(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "prompt"


def estimate_tokens(text: str) -> int:
    return max(1, (len(text) + 3) // 4)


def read_uploaded_file(uploaded_file) -> str:
    try:
        content = uploaded_file.read().decode("utf-8")
        return f"\n--- File: {uploaded_file.name} ---\n{content}\n--- End of file ---\n"
    except Exception as e:
        return f"\n[Error reading file: {e}]\n"


# Task configurations (optimized for token efficiency)
TASK_SPECS = {
    "Create Dashboard": {
        "role": "Senior analytics engineer & dashboard designer",
        "goal": "Design decision-focused dashboard from context",
        "guidelines": [
            "Identify personas & key decisions",
            "Define 5-8 KPIs: name, formula, grain, owner",
            "Specify visuals, layout, filters, interactions",
            "List data sources & quality notes",
            "Include performance/accessibility notes",
            "Provide implementation plan (queries/pseudo-SQL)",
        ],
    },
    "Analyze Code": {
        "role": "Principal software engineer & code reviewer",
        "goal": "Analyze code, produce actionable findings",
        "guidelines": [
            "Summarize responsibilities, flow, dependencies",
            "List bugs/security/performance issues: severity + fix",
            "Recommend refactors: rationale + complexity",
            "Propose tests (given/when/then)",
            "Call out risks, trade-offs, unknowns",
        ],
    },
    "Rewrite Code": {
        "role": "Senior software engineer",
        "goal": "Improve code: readability, safety, performance",
        "guidelines": [
            "Preserve API/semantics unless instructed",
            "Use modern idioms, secure patterns",
            "Validate inputs, improve error handling",
            "Add minimal docstrings (no verbosity)",
            "Provide tests + migration notes if needed",
        ],
    },
}


JSON_SCHEMAS = {
    "Create Dashboard": {
        "personas": [""],
        "decisions": [""],
        "kpis": [{"name": "", "def": "", "formula": "", "grain": "", "owner": ""}],
        "visuals": [{"title": "", "chart": "", "fields": [""], "notes": ""}],
        "layout": {"sections": [""], "notes": ""},
        "sources": [""],
        "impl": {"queries": [""], "notes": [""], "risks": [""]},
    },
    "Analyze Code": {
        "summary": "",
        "issues": [
            {"type": "bug|sec|perf|style", "loc": "", "desc": "", "sev": "low|med|high", "fix": ""}
        ],
        "complexity": {"cognitive": "", "cyclomatic": "", "hotspots": [""]},
        "tests": [{"name": "", "given": "", "when": "", "then": ""}],
        "refactors": [{"step": "", "why": ""}],
        "risks": [""],
    },
    "Rewrite Code": {
        "code": "```lang\n...\n```",
        "changes": [{"before": "", "after": "", "why": ""}],
        "compat": [""],
        "tests": [{"name": "", "given": "", "when": "", "then": ""}],
        "migration": [""],
    },
}


PROMPT_FRAMEWORKS = {
    "(None)": None,
    "TAG": ["Task", "Action", "Goal"],
    "RTF": ["Role", "Task", "Format"],
    "CARE": ["Context", "Action", "Result", "Example"],
    "RISE": ["Role", "Input", "Steps", "Expectation"],
    "RACE": ["Role", "Action", "Context", "Expectation"],
    "APE": ["Action", "Purpose", "Expectation"],
    "CRISPE": ["Capacity", "Insight", "Statement", "Personality", "Experiment"],
    "COAST": ["Context", "Objective", "Actions", "Scenario", "Task"],
    "TRACE": ["Task", "Request", "Action", "Context", "Example"],
    "ROSES": ["Role", "Objective", "Scenario", "Expected Solution", "Steps"],
    "PECRA": ["Purpose", "Expectation", "Context", "Request", "Action"],
    "5W1H": ["Who", "What", "When", "Where", "Why", "How"],
    "BAB": ["Before", "After", "Bridge"],
    "STAR": ["Situation", "Task", "Action", "Result"],
    "GRADE": ["Goals", "Request", "Action", "Detail", "Examples"],
}


def build_prompt(
    input_text: str,
    task_type: str,
    tone: str,
    output_format: str,
    ask_questions: bool,
    structured_reasoning: bool,
    extra_requirements: str,
    token_efficient: bool,
) -> str:
    spec = TASK_SPECS[task_type]
    guidelines = spec["guidelines"].copy()

    if ask_questions:
        guidelines.insert(0, "If unclear, ask max 3 clarifying questions")
    if structured_reasoning:
        guidelines.append("Use structured headings/bullets")

    if token_efficient:
        guidelines.append("Be concise: minimize tokens, maximize clarity")

    sections = [
        f"Task: {task_type}",
        f"Role: {spec['role']}",
        f"Goal: {spec['goal']}",
        f"Tone: {tone.lower()}",
    ]

    if input_text.strip():
        sections.append(f"Context:\n{input_text.strip()}")
    if extra_requirements.strip():
        sections.append(f"Requirements:\n{extra_requirements.strip()}")

    sections.append("Guidelines:\n" + "\n".join(f"- {g}" for g in guidelines))

    if output_format == "JSON":
        schema = JSON_SCHEMAS.get(task_type, JSON_SCHEMAS["Rewrite Code"])
        sections.append(
            f"Output: JSON only (no markdown). Schema:\n{json.dumps(schema, ensure_ascii=False)}"
        )
    else:
        sections.append("Output: Summary → Sections → Assumptions/Risks")

    sections.append("Quality: Precise, actionable, self-contained")

    return "\n\n".join(sections)


# UI
st.set_page_config(page_title="Prompt Builder", page_icon="🧰", layout="wide")

st.title("🧰 Prompt Builder")

with st.sidebar:
    st.header("Settings")
    task_type = st.selectbox(
        "Task type", options=list(TASK_SPECS.keys()), index=0
    )
    tone = st.selectbox("Tone", ["Concise", "Detailed"], index=0)
    output_format = st.selectbox("Format", ["Plain text", "JSON"], index=0)
    ask_questions = st.checkbox("Ask clarifying questions", value=True)
    structured_reasoning = st.checkbox("Structured reasoning", value=True)
    token_efficient = st.checkbox("Token-efficient prompts", value=True)

    extra_requirements = st.text_area(
        "Extra requirements", height=80, placeholder="Constraints, style notes..."
    )

    st.header("Frameworks")
    framework = st.selectbox(
        "Prompt framework",
        options=list(PROMPT_FRAMEWORKS.keys()),
        help="Select a framework to structure your prompt. This will insert a template.",
    )

    if framework and framework != "(None)" and st.button(f"Apply {framework} framework"):
        template_fields = PROMPT_FRAMEWORKS[framework]
        template = "\n".join(f"**{field}:** " for field in template_fields)
        st.session_state.framework_template = template

col_in, col_out = st.columns([0.55, 0.45])

with col_in:
    st.subheader("Input")
    
    # File upload
    uploaded_files = st.file_uploader(
        "Upload files", 
        type=["txt", "py", "js", "ts", "json", "md", "sql", "csv"],
        accept_multiple_files=True,
        help="Upload code files, docs, or data files"
    )
    
    file_content = ""
    if uploaded_files:
        for file in uploaded_files:
            file_content += read_uploaded_file(file)
        st.success(f"Loaded {len(uploaded_files)} file(s)")
    
    # Text input
    # Handle framework template insertion
    initial_input = file_content
    if "framework_template" in st.session_state:
        initial_input += st.session_state.pop("framework_template")

    input_text = st.text_area(
        "Or paste context here",
        height=200,
        placeholder="Describe your task, paste code, or add context...",
        value=initial_input,
        key="input_text_area"
    )

    disabled = len(input_text.strip()) == 0
    if st.button("Generate prompt", type="primary", disabled=disabled):
        prompt = build_prompt(
            input_text=input_text,
            task_type=task_type,
            tone=tone,
            output_format=output_format,
            ask_questions=ask_questions,
            structured_reasoning=structured_reasoning,
            extra_requirements=extra_requirements,
            token_efficient=token_efficient,
        )
        st.session_state["generated_prompt"] = prompt
        st.session_state["generated_meta"] = {
            "task": task_type,
            "format": output_format,
            "created_at": datetime.utcnow().isoformat() + "Z",
        }
        
        # Show token estimate prominently
        token_count = estimate_tokens(prompt)
        st.info(f"📊 **Estimated tokens for this task:** ~{token_count:,} tokens")

with col_out:
    st.subheader("Generated Prompt")
    prompt = st.session_state.get("generated_prompt")
    meta = st.session_state.get("generated_meta", {})
    if prompt:
        lang = "json" if meta.get("format") == "JSON" else "markdown"
        st.code(prompt, language=lang)
        fname = f"prompt-{slugify(meta.get('task', 'task'))}-{slugify(meta.get('format', 'plain'))}.txt"
        st.download_button(
            label="Download", data=prompt, file_name=fname, mime="text/plain"
        )
        st.caption(
            f"{len(prompt):,} chars · ~{estimate_tokens(prompt):,} tokens · {meta.get('created_at', '')}"
        )
    else:
        st.info("Generate a prompt to see it here")
