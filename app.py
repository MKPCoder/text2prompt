import json
import re
from datetime import datetime

import streamlit as st


def slugify(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "prompt"


def estimate_tokens(text: str) -> int:
    # Very rough approximation (~4 chars per token)
    return max(1, (len(text) + 3) // 4)


def task_specs(task_type: str) -> dict:
    specs = {
        "Create Dashboard": {
            "role": "You are a senior analytics engineer and dashboard designer.",
            "goal": "Design a practical, decision-focused dashboard from the provided context.",
            "guidelines": [
                "Identify primary personas and their key decisions.",
                "Derive 5–8 KPIs with clear definitions, formulas, and grain.",
                "Recommend visuals and layout; specify filters, drilldowns, and interactions.",
                "State data sources, assumptions, and data quality considerations.",
                "Include performance, accessibility, and maintenance notes.",
                "Provide a concise implementation plan (queries/measures or pseudo-SQL).",
            ],
        },
        "Analyze Code": {
            "role": "You are a principal software engineer and code reviewer.",
            "goal": "Analyze the provided code or description and produce actionable findings.",
            "guidelines": [
                "Summarize responsibilities, control flow, and dependencies.",
                "List bugs, edge cases, security, and performance issues with severity and fixes.",
                "Recommend refactors with rationale and complexity impact.",
                "Propose focused tests (given/when/then).",
                "Call out risks, trade-offs, and unknowns.",
            ],
        },
        "Rewrite Code": {
            "role": "You are a senior software engineer rewriting code while preserving behavior.",
            "goal": "Rewrite the code to improve readability, safety, and performance without changing intended behavior unless instructed.",
            "guidelines": [
                "Preserve public API and semantics unless otherwise specified.",
                "Use modern idioms, secure patterns, and project-typical style.",
                "Validate inputs; improve error handling and edge-case coverage.",
                "Add minimal docstrings/comments to clarify intent (no verbose narration).",
                "Provide tests and migration notes if signatures change.",
            ],
        },
    }
    return specs[task_type]


def json_schema_for(task_type: str) -> dict:
    if task_type == "Create Dashboard":
        return {
            "personas": [""],
            "decision_questions": [""],
            "kpis": [
                {
                    "name": "",
                    "definition": "",
                    "formula": "",
                    "granularity": "",
                    "owner": "",
                }
            ],
            "visuals": [
                {
                    "title": "",
                    "chart": "",
                    "fields": [""],
                    "interactions": [""],
                    "notes": "",
                }
            ],
            "layout": {"sections": [""], "notes": ""},
            "data_sources": [""],
            "implementation": {
                "queries": [""],
                "measures": [""],
                "performance_notes": [""],
            },
            "risks": [""],
            "assumptions": [""],
        }
    if task_type == "Analyze Code":
        return {
            "summary": "",
            "issues": [
                {
                    "type": "bug|security|performance|style",
                    "location": "",
                    "description": "",
                    "severity": "low|medium|high",
                    "fix": "",
                    "references": [""],
                }
            ],
            "complexity": {"cognitive": "", "cyclomatic": "", "hotspots": [""]},
            "tests": [{"name": "", "given": "", "when": "", "then": ""}],
            "refactor_plan": [{"step": "", "rationale": ""}],
            "risks": [""],
            "assumptions": [""],
        }
    # Rewrite Code
    return {
        "rewritten_code": "```language\n...\n```",
        "change_log": [{"before": "", "after": "", "reason": ""}],
        "compatibility_notes": [""],
        "tests": [{"name": "", "given": "", "when": "", "then": ""}],
        "migration_steps": [""],
        "assumptions": [""],
    }


def build_prompt(
    input_text: str,
    task_type: str,
    tone: str,
    output_format: str,
    ask_questions: bool,
    structured_reasoning: bool,
    extra_requirements: str,
) -> str:
    spec = task_specs(task_type)
    guidelines = list(spec["guidelines"])  # copy

    if ask_questions:
        guidelines.insert(
            0,
            "If the context is ambiguous, ask up to 3 targeted clarifying questions before proceeding.",
        )
    if structured_reasoning:
        guidelines.append(
            "Use concise, structured reasoning in headings/bullets (avoid revealing internal chain-of-thought)."
        )

    sections = []
    sections.append(f"Task: {task_type}")
    sections.append(f"Role: {spec['role']}")
    sections.append(f"Objective: {spec['goal']}")
    sections.append(f"Tone: {tone.lower()}")

    if input_text.strip():
        sections.append("Context:\n" + input_text.strip())
    if extra_requirements.strip():
        sections.append("Additional requirements:\n" + extra_requirements.strip())

    # Guidelines
    gl_text = "\n".join([f"- {g}" for g in guidelines])
    sections.append("Guidelines:\n" + gl_text)

    # Output format
    if output_format == "JSON":
        schema = json_schema_for(task_type)
        schema_text = json.dumps(schema, indent=2, ensure_ascii=False)
        sections.append(
            "Output format:\n"
            "- Respond with ONLY valid JSON matching the schema below.\n"
            "- Do not include markdown fences or commentary outside the JSON.\n"
            f"Schema:\n{schema_text}"
        )
        sections.append(
            "Validation:\n- Ensure fields are complete and consistent. Use empty strings or arrays where unknown."
        )
    else:
        sections.append(
            "Output format (plain text):\n"
            "- Start with a brief summary.\n"
            "- Use clear section headings and bullet points.\n"
            "- Include assumptions and risks at the end."
        )

    sections.append(
        "Quality bar:\n"
        "- Be precise, unambiguous, and actionable.\n"
        "- Prefer specifics over generalities.\n"
        "- Keep the response self-contained."
    )

    return "\n\n".join(sections).strip()


# UI
st.set_page_config(page_title="Prompt Builder", page_icon="🧰", layout="wide")

st.title("🧰 Prompt Builder")

with st.sidebar:
    st.header("Settings")
    task_type = st.selectbox(
        "Task type",
        options=["Create Dashboard", "Analyze Code", "Rewrite Code"],
        index=0,
    )
    tone = st.selectbox("Tone/level", ["Concise", "Detailed"], index=0)
    output_format = st.selectbox("Output format", ["Plain text", "JSON"], index=0)
    ask_questions = st.checkbox(
        "If ambiguous, ask clarifying questions first", value=True
    )
    structured_reasoning = st.checkbox(
        "Use structured reasoning (headings/bullets)", value=True
    )

    extra_requirements = st.text_area(
        "Additional requirements (optional)", height=120, placeholder="Constraints, style guides, domain notes, etc."
    )

col_in, col_out = st.columns([0.55, 0.45])

with col_in:
    input_text = st.text_area(
        "Your input/context",
        height=260,
        placeholder=(
            "Describe your data/business need for a dashboard, paste code to analyze, or the code you want rewritten.\n"
            "You can also include goals, constraints, or target audience."
        ),
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
        )
        st.session_state["generated_prompt"] = prompt
        st.session_state["generated_meta"] = {
            "task": task_type,
            "format": output_format,
            "created_at": datetime.utcnow().isoformat() + "Z",
        }

with col_out:
    st.subheader("Generated Prompt")
    prompt = st.session_state.get("generated_prompt")
    meta = st.session_state.get("generated_meta", {})
    if prompt:
        lang = "json" if meta.get("format") == "JSON" else "markdown"
        st.code(prompt, language=lang)
        fname = f"prompt-{slugify(meta.get('task', 'task'))}-{slugify(meta.get('format', 'plain'))}.txt"
        st.download_button(
            label="Download prompt",
            data=prompt,
            file_name=fname,
            mime="text/plain",
        )
        st.caption(
            f"Length: {len(prompt):,} chars · ~{estimate_tokens(prompt):,} tokens · Generated {meta.get('created_at', '')}"
        )
    else:
        st.info("Generate a prompt to see it here. You can download it once generated.")
