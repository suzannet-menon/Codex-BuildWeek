import json
import os
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List
from models import MatchResult

load_dotenv()
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
MODEL = "gpt-5.6"

class SuggestionEval(BaseModel):
    suggestion_index: int
    quality_score: int          # 0–10
    is_specific: bool           # Does it give concrete text, not vague advice?
    is_actionable: bool         # Can a candidate act on it immediately?
    flag: str                   # "good" | "vague" | "hallucinated" | "weak"


class EvalReport(BaseModel):
    overall_quality: float        # 0–10 average
    evaluations: List[SuggestionEval]
    eval_summary: str           # Judge's overall verdict


def evaluate_suggestions(result: MatchResult, job_description: str) -> EvalReport:
    """
    A judge LLM independently evaluates the quality of resume suggestions.
    This is the self-eval / evals layer — checks if suggestions are actually useful.
    """

    suggestions_text = "\n".join([
        f"[{i}] Section: {s.section} | Suggestion: {s.suggestion} | Reason: {s.reason}"
        for i, s in enumerate(result.resume_suggestions.suggestions)
    ])

    system = """You are a strict quality evaluator for AI-generated resume advice.
Your job is to evaluate whether resume suggestions are genuinely useful or vague/hallucinated.
Return ONLY valid JSON. No preamble."""

    user = f"""Job Description:
{job_description}

Resume Suggestions to Evaluate:
{suggestions_text}

For each suggestion, evaluate:
- quality_score: 0-10 (10 = excellent, specific, directly tied to JD)
- is_specific: does it give concrete text to add/change, not just "add more X"?
- is_actionable: can a candidate do this immediately without more guidance?
- flag: "good" if quality >= 7, "vague" if generic advice, "hallucinated" if fabricated skills, "weak" if low quality

Return JSON in exactly this format:
{{
  "overall_quality": <average score 0-10>,
  "evaluations": [
    {{
      "suggestion_index": 0,
      "quality_score": <int>,
      "is_specific": <bool>,
      "is_actionable": <bool>,
      "flag": "<good|vague|hallucinated|weak>"
    }}
  ],
  "eval_summary": "<2 sentence verdict on overall suggestion quality>"
}}"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )

    choice = response.choices[0]
    message = getattr(choice, "message", None)
    content = getattr(message, "content", None)
    if not content:
        raise ValueError("No content returned from model response")

    raw = content.strip()
    clean = raw.replace("```json", "").replace("```", "").strip()
    data = json.loads(clean)
    return EvalReport(**data)