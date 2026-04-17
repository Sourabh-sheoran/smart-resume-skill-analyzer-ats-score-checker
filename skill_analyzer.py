"""Core skill analysis logic and ATS score calculation for resumes."""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, Sequence

import pandas as pd

DEFAULT_SKILL_PATTERNS: Mapping[str, Sequence[str]] = {
    "Python": (r"\bpython\b",),
    "SQL": (r"\bsql\b", r"\bpostgresql\b", r"\bmysql\b", r"\bsqlite\b"),
    "Power BI": (r"\bpower\s*bi\b",),
    "Excel": (r"\bexcel\b", r"\bms\s*excel\b", r"\bmicrosoft\s*excel\b"),
    "Machine Learning": (
        r"\bmachine\s*learning\b",
        r"\bmachine-learning\b",
        r"\bml\s+models?\b",
    ),
    "HTML": (r"\bhtml5?\b",),
    "CSS": (r"\bcss3?\b",),
    "JavaScript": (r"\bjavascript\b", r"\bjs\b"),
    "AWS": (r"\baws\b", r"\bamazon\s+web\s+services\b"),
    "Git": (r"\bgit\b", r"\bgithub\b", r"\bgitlab\b", r"\bbitbucket\b"),
    "Pandas": (r"\bpandas\b",),
    "NumPy": (r"\bnumpy\b",),
}

ROLE_SKILLS_MAP: Mapping[str, List[str]] = {
    "Data Analyst": ["Python", "SQL", "Power BI", "Excel", "Pandas", "NumPy", "Git"],
    "Data Scientist": [
        "Python",
        "SQL",
        "Machine Learning",
        "Pandas",
        "NumPy",
        "AWS",
        "Git",
    ],
    "Business Intelligence Analyst": [
        "SQL",
        "Power BI",
        "Excel",
        "Python",
        "Pandas",
        "Git",
    ],
    "Machine Learning Engineer": [
        "Python",
        "Machine Learning",
        "SQL",
        "Pandas",
        "NumPy",
        "AWS",
        "Git",
    ],
    "Frontend Developer": ["HTML", "CSS", "JavaScript", "Git", "AWS"],
}


@dataclass
class AnalysisResult:
    required_skills: List[str]
    detected_skills: List[str]
    missing_skills: List[str]
    skill_frequency: Dict[str, int]
    skill_coverage_percentage: float
    keyword_density: float
    total_words: int
    ats_score: int
    score_breakdown: Dict[str, float]
    suggestions: List[str]


def count_words(text: str) -> int:
    """Count words in extracted resume text."""
    return len(re.findall(r"\b[a-zA-Z0-9\+#]+\b", text))


def _default_pattern_for_skill(skill: str) -> str:
    return rf"\b{re.escape(skill.lower())}\b"


def count_skill_frequency(text: str, required_skills: Iterable[str]) -> Dict[str, int]:
    """Count occurrences for each target skill using regex patterns."""
    frequencies: Dict[str, int] = {}
    normalized_text = text.lower()

    for skill in required_skills:
        patterns = DEFAULT_SKILL_PATTERNS.get(skill, (_default_pattern_for_skill(skill),))
        total_matches = 0
        for pattern in patterns:
            total_matches += len(re.findall(pattern, normalized_text, flags=re.IGNORECASE))
        frequencies[skill] = total_matches

    return frequencies


def _score_skill_coverage(detected_count: int, required_count: int) -> float:
    if required_count == 0:
        return 0.0
    return (detected_count / required_count) * 60.0


def _score_resume_length(total_words: int) -> float:
    """
    Score resume length from 0 to 15.
    Sweet spot is generally between ~300 and ~900 words.
    """
    if total_words <= 0:
        return 0.0
    if total_words < 150:
        return (total_words / 150.0) * 7.0
    if total_words < 300:
        return 7.0 + ((total_words - 150) / 150.0) * 5.0
    if total_words <= 900:
        return 12.0 + ((total_words - 300) / 600.0) * 3.0
    if total_words <= 1200:
        return 15.0 - ((total_words - 900) / 300.0) * 5.0
    return 8.0


def _score_keyword_density(density: float) -> float:
    """
    Score keyword density from 0 to 25.
    Ideal density range is around 2-3.5% for this ATS approximation.
    """
    if density <= 0:
        return 0.0
    if density <= 0.03:
        return (density / 0.03) * 25.0
    if density <= 0.08:
        return 25.0 - ((density - 0.03) / 0.05) * 6.0
    return 18.0


def generate_suggestions(
    missing_skills: List[str],
    total_words: int,
    keyword_density: float,
    ats_score: int,
) -> List[str]:
    """Create dynamic suggestions based on detected gaps."""
    suggestions: List[str] = []

    if missing_skills:
        summary = ", ".join(missing_skills[:6])
        suggestions.append(
            f"Add role-relevant keywords you genuinely know: {summary}."
        )
        for skill in missing_skills:
            suggestions.append(
                f"If you have practical experience, include {skill} with measurable project outcomes."
            )

    if total_words < 300:
        suggestions.append(
            "Resume is short for ATS parsing; add quantified accomplishments and project context."
        )
    elif total_words > 1100:
        suggestions.append(
            "Resume is quite long; tighten less relevant content to improve readability and focus."
        )

    if keyword_density < 0.01:
        suggestions.append(
            "Keyword density is low; weave target skills naturally into experience bullets."
        )
    elif keyword_density > 0.08:
        suggestions.append(
            "Keyword density is high; reduce repetition and keep wording natural."
        )

    if ats_score >= 85:
        suggestions.append(
            "Strong ATS profile. Next step: tailor role-specific achievements for each job application."
        )

    return suggestions


def analyze_resume(text: str, required_skills: Iterable[str] | None = None) -> AnalysisResult:
    """
    Analyze resume text, detect skills, and compute a 0-100 ATS-style score.

    Score components:
    - Skill coverage: 60 points
    - Resume length: 15 points
    - Keyword density: 25 points
    """
    if required_skills is None:
        required = list(DEFAULT_SKILL_PATTERNS.keys())
    else:
        required = [skill.strip() for skill in required_skills if skill and skill.strip()]
        required = list(dict.fromkeys(required))  # keep order, remove duplicates
        if not required:
            required = list(DEFAULT_SKILL_PATTERNS.keys())

    frequencies = count_skill_frequency(text, required)
    detected = [skill for skill, count in frequencies.items() if count > 0]
    missing = [skill for skill in required if frequencies.get(skill, 0) == 0]

    total_words = count_words(text)
    total_skill_mentions = sum(frequencies.values())
    keyword_density = (total_skill_mentions / total_words) if total_words else 0.0
    coverage_pct = (len(detected) / len(required) * 100.0) if required else 0.0

    skill_score = _score_skill_coverage(len(detected), len(required))
    length_score = _score_resume_length(total_words)
    density_score = _score_keyword_density(keyword_density)

    raw_score = skill_score + length_score + density_score
    ats_score = int(round(max(0.0, min(100.0, raw_score))))

    breakdown = {
        "skill_coverage_score": round(skill_score, 2),
        "resume_length_score": round(length_score, 2),
        "keyword_density_score": round(density_score, 2),
    }

    suggestions = generate_suggestions(
        missing_skills=missing,
        total_words=total_words,
        keyword_density=keyword_density,
        ats_score=ats_score,
    )

    return AnalysisResult(
        required_skills=required,
        detected_skills=detected,
        missing_skills=missing,
        skill_frequency=frequencies,
        skill_coverage_percentage=round(coverage_pct, 2),
        keyword_density=keyword_density,
        total_words=total_words,
        ats_score=ats_score,
        score_breakdown=breakdown,
        suggestions=suggestions,
    )


def build_skill_frequency_dataframe(skill_frequency: Mapping[str, int]) -> pd.DataFrame:
    """Create a DataFrame view for frequencies."""
    rows = [
        {
            "Skill": skill,
            "Frequency": frequency,
            "Detected": "Yes" if frequency > 0 else "No",
        }
        for skill, frequency in skill_frequency.items()
    ]
    return pd.DataFrame(rows)


def highlight_keywords(text: str, keywords: Iterable[str]) -> str:
    """Return HTML text with highlighted keywords for Streamlit display."""
    highlighted = html.escape(text)
    clean_keywords = sorted(
        {kw.strip() for kw in keywords if kw and kw.strip()},
        key=len,
        reverse=True,
    )

    for keyword in clean_keywords:
        pattern = re.compile(rf"(?i)\b({re.escape(keyword)})\b")
        highlighted = pattern.sub(
            (
                "<mark style='background-color:#fde68a; "
                "padding:0 2px; border-radius:2px;'>\\1</mark>"
            ),
            highlighted,
        )

    return highlighted.replace("\n", "<br>")


__all__ = [
    "AnalysisResult",
    "DEFAULT_SKILL_PATTERNS",
    "ROLE_SKILLS_MAP",
    "analyze_resume",
    "build_skill_frequency_dataframe",
    "count_skill_frequency",
    "highlight_keywords",
]
