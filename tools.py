#Individual agent tools

import json
import os
from groq import Groq
from dotenv import load_dotenv
from models import MatchScore, GapAnalysis, ResumeSuggestions, ATSKeywords, SemanticScore

load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"


def _call_groq(system_prompt: str, user_prompt: str) -> str:
    """Base Groq call - returns raw text content."""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
    )
    content = response.choices[0].message.content
    return content.strip() if content else ""


def _parse_json(raw: str) -> dict:
    """Strip markdown fences and parse JSON."""
    clean = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(clean)


# Tool 1: Match Scoring 

def score_match(resume_text: str, job_description: str) -> MatchScore:
    system = """You are an expert technical recruiter and resume evaluator.
Analyze how well a resume matches a job description and return ONLY valid JSON.
No preamble, no explanation outside the JSON."""

    user = f"""Resume:
{resume_text}

Job Description:
{job_description}

Return JSON in exactly this format:
{{
  "score": <integer 0-100>,
  "reasoning": "<2-3 sentence explanation of the score>",
  "strong_matches": ["<skill or experience that matches well>", ...],
  "weak_matches": ["<skill or experience that partially matches>", ...]
}}"""

    raw = _call_groq(system, user)
    data = _parse_json(raw)
    return MatchScore(**data)


# Tool 2: Gap Analysis 

def analyze_gaps(resume_text: str, job_description: str, llm_score: float, semantic: SemanticScore) -> GapAnalysis:
    system = """You are an expert ATS system and career coach.
Identify gaps between a resume and job description. Return ONLY valid JSON."""

    user = f"""Resume:
{resume_text}

Job Description:
{job_description}

Current LLM Match Score: {llm_score}%

Semantic Similarity: {semantic.percentage}%

Use both scores when generating suggestions:
- If semantic similarity is high but the LLM score is low, focus on ATS keywords and wording.
- If both are low, recommend adding relevant experience, projects, and skills.

Return JSON in exactly this format:
{{
  "missing_skills": ["<technical skill required but not in resume>", ...],
  "missing_experience": ["<type of experience required but missing>", ...],
  "missing_keywords": ["<ATS keyword not present in resume>", ...],
  "priority_gaps": ["<top 3 most critical gaps to fix first>", ...]
}}"""

    raw = _call_groq(system, user)
    data = _parse_json(raw)
    return GapAnalysis(**data)


# Tool 3: Resume Suggestions 

def suggest_improvements(resume_text: str, job_description: str, gaps: GapAnalysis, semantic: SemanticScore,
    llm_score: float,) -> ResumeSuggestions:
    system = """You are a professional resume writer specializing in tech roles.
Give specific, actionable resume improvements. Return ONLY valid JSON."""

    user = f"""Resume:
{resume_text}

Job Description:
{job_description}

Known Gaps:
- Missing skills: {gaps.missing_skills}
- Missing keywords: {gaps.missing_keywords}
- Priority gaps: {gaps.priority_gaps}

Return JSON in exactly this format:
{{
  "suggestions": [
    {{
      "section": "<Resume section e.g. Experience, Skills, Summary>",
      "original": "<existing bullet point or text if rewriting, else null>",
      "suggestion": "<improved or new text to add>",
      "reason": "<why this helps match the job>"
    }}
  ],
  "summary_advice": "<2-3 sentences of overall strategic advice for this application>"
}}"""

    raw = _call_groq(system, user)
    data = _parse_json(raw)
    return ResumeSuggestions(**data)


#  Tool 4: ATS Keyword Suggestions 

def suggest_ats_keywords(
    resume_text: str,
    job_description: str,
    llm_score: int,
    semantic_percentage: int,
) -> ATSKeywords:
    """
    Extracts high-value ATS keywords from the job description that are absent
    from the resume, prioritises them, and gives concrete usage examples.
    Always runs, but flags score_gap_detected when divergence >= 15 points.
    """
    score_gap = llm_score - semantic_percentage
    gap_detected = score_gap >= 15

    system = """You are an expert ATS (Applicant Tracking System) specialist.
Your job is to identify the exact keywords and phrases from a job description
that are missing from a resume, and show the candidate precisely how to add them.
Return ONLY valid JSON. No preamble."""

    user = f"""Resume:
{resume_text}

Job Description:
{job_description}

LLM Match Score: {llm_score}/100
Semantic Similarity Score: {semantic_percentage}/100
Score Gap: {score_gap} points {"(SIGNIFICANT — ATS vocabulary mismatch detected)" if gap_detected else ""}

Task: Extract the most important ATS keywords from the job description that are
MISSING or UNDERREPRESENTED in the resume. For each keyword:
- Identify its priority based on how often/prominently it appears in the JD
- Suggest exactly which resume section to add it to
- Write a ready-to-use example sentence the candidate can drop into their resume

Return JSON in exactly this format:
{{
  "score_gap_detected": {str(gap_detected).lower()},
  "keywords": [
    {{
      "keyword": "<exact keyword or phrase from JD>",
      "priority": "<high|medium|low>",
      "where_to_add": "<Skills / Experience / Summary / Projects>",
      "usage_example": "<A ready-to-paste resume bullet using this keyword>"
    }}
  ],
  "rewrite_advice": "<One concrete paragraph explaining how to align resume vocabulary with the JD to improve ATS pass rate>"
}}

Return 8-12 keywords total. Prioritise exact phrases over single words where possible."""

    raw = _call_groq(system, user)
    data = _parse_json(raw)
    return ATSKeywords(**data)