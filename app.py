"""Streamlit application: Smart Resume Skill Analyzer & ATS Score Checker."""

from __future__ import annotations

import html
from typing import List

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from resume_reader import ResumeReadError, extract_text_from_pdf
from skill_analyzer import (
    DEFAULT_SKILL_PATTERNS,
    ROLE_SKILLS_MAP,
    analyze_resume,
    build_skill_frequency_dataframe,
    highlight_keywords,
)

st.set_page_config(
    page_title="Smart Resume Skill Analyzer & ATS Score Checker",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .main-title {
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.2rem;
        }
        .subtitle {
            color: #475569;
            margin-bottom: 1rem;
        }
        .panel {
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 0.8rem 1rem;
        }
        .highlight-box {
            border: 1px solid #e2e8f0;
            background: #ffffff;
            border-radius: 10px;
            max-height: 360px;
            overflow-y: auto;
            padding: 1rem;
            line-height: 1.55;
            font-size: 0.92rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def _parse_custom_keywords(raw_keywords: str) -> List[str]:
    return [token.strip() for token in raw_keywords.split(",") if token.strip()]


def _skill_badges(skills: List[str], color: str) -> str:
    if not skills:
        return "<span style='color:#64748b;'>None</span>"

    badges = []
    for skill in skills:
        safe_skill = html.escape(skill)
        badges.append(
            (
                "<span style='display:inline-block; margin:4px 6px 0 0; padding:4px 10px; "
                f"border-radius:999px; border:1px solid {color}; color:{color}; "
                "background:rgba(255,255,255,0.9); font-size:0.82rem;'>"
                f"{safe_skill}</span>"
            )
        )
    return "".join(badges)


st.markdown(
    "<div class='main-title'>Smart Resume Skill Analyzer & ATS Score Checker</div>",
    unsafe_allow_html=True,
)
st.markdown(
    (
        "<div class='subtitle'>Upload a resume PDF to evaluate ATS-readiness, "
        "skill match, keyword density, and missing skill suggestions.</div>"
    ),
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Analysis Configuration")
    role_options = ["General"] + sorted(ROLE_SKILLS_MAP.keys())
    selected_role = st.selectbox("Target job role", role_options)
    role_default_skills = (
        list(DEFAULT_SKILL_PATTERNS.keys())
        if selected_role == "General"
        else ROLE_SKILLS_MAP[selected_role]
    )

    selected_skills = st.multiselect(
        "Skills to check",
        options=list(DEFAULT_SKILL_PATTERNS.keys()),
        default=role_default_skills,
    )
    custom_keywords_raw = st.text_input(
        "Additional keywords (comma-separated)",
        placeholder="Tableau, Airflow, Docker",
    )
    st.caption("Tip: Customize role keywords to produce targeted ATS suggestions.")

uploaded_pdf = st.file_uploader("Upload Resume (PDF only)", type=["pdf"])

if uploaded_pdf is None:
    st.info("Upload a PDF resume to start analysis.")
    st.stop()

try:
    with st.spinner("Extracting text and calculating ATS score..."):
        resume_text = extract_text_from_pdf(uploaded_pdf)
        custom_keywords = _parse_custom_keywords(custom_keywords_raw)
        required_skills = list(dict.fromkeys(selected_skills + custom_keywords))
        if not required_skills:
            required_skills = list(DEFAULT_SKILL_PATTERNS.keys())
        analysis = analyze_resume(resume_text, required_skills=required_skills)

    st.subheader("ATS Score Indicator")
    st.progress(analysis.ats_score / 100)

    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    metric_col1.metric("ATS Score", f"{analysis.ats_score}/100")
    metric_col2.metric(
        "Skills Matched",
        f"{len(analysis.detected_skills)}/{len(analysis.required_skills)}",
    )
    metric_col3.metric("Skill Coverage", f"{analysis.skill_coverage_percentage:.1f}%")
    metric_col4.metric("Keyword Density", f"{analysis.keyword_density * 100:.2f}%")

    result_col1, result_col2 = st.columns(2)
    with result_col1:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.markdown("#### Detected Skills")
        st.markdown(
            _skill_badges(analysis.detected_skills, "#15803d"),
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with result_col2:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.markdown("#### Missing Skills")
        st.markdown(
            _skill_badges(analysis.missing_skills, "#b91c1c"),
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    st.subheader("Dynamic Suggestions")
    if analysis.suggestions:
        for suggestion in analysis.suggestions:
            st.markdown(f"- {suggestion}")
    else:
        st.success("No major gaps detected. Your resume aligns well with selected keywords.")

    st.subheader("Skill Frequency & Percentage View")
    frequency_df = build_skill_frequency_dataframe(analysis.skill_frequency)
    total_skills = max(len(analysis.required_skills), 1)
    detected_count = len(analysis.detected_skills)
    percentage_score = (detected_count / total_skills) * 100

    st.metric("Skill Percentage Score", f"{percentage_score:.2f}%")
    st.dataframe(frequency_df, use_container_width=True, hide_index=True)

    st.bar_chart(
        frequency_df.set_index("Skill")["Frequency"],
        use_container_width=True,
        color="#2563eb",
    )

    with st.expander("Matplotlib Skill Distribution Chart"):
        fig, ax = plt.subplots(figsize=(10, 4))
        bar_colors = [
            "#2563eb" if val > 0 else "#cbd5e1"
            for val in frequency_df["Frequency"].tolist()
        ]
        ax.bar(frequency_df["Skill"], frequency_df["Frequency"], color=bar_colors)
        ax.set_title("Skill Occurrence Distribution")
        ax.set_xlabel("Skills")
        ax.set_ylabel("Frequency")
        ax.grid(axis="y", linestyle="--", alpha=0.35)
        ax.tick_params(axis="x", rotation=40)
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

    st.subheader("ATS Score Breakdown")
    breakdown_df = pd.DataFrame(
        {
            "Component": list(analysis.score_breakdown.keys()),
            "Score": list(analysis.score_breakdown.values()),
        }
    )
    st.bar_chart(
        breakdown_df.set_index("Component")["Score"],
        use_container_width=True,
        color="#0f766e",
    )

    st.subheader("Keyword Highlighting in Resume")
    highlighted_html = highlight_keywords(resume_text, analysis.detected_skills)
    st.markdown(
        f"<div class='highlight-box'>{highlighted_html}</div>",
        unsafe_allow_html=True,
    )

    with st.expander("Preview extracted resume text"):
        st.text_area("Extracted Resume Text", value=resume_text, height=280)

except ResumeReadError as exc:
    st.error(str(exc))
except Exception as exc:  # noqa: BLE001
    st.error(f"Unexpected error during analysis: {exc}")
