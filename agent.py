#Agentic logic + tool calls

from typing import cast
from models import MatchRequest, MatchResult, EvalReport
from tools import score_match, analyze_gaps, suggest_improvements, suggest_ats_keywords
from interview import generate_interview
from embeddings import compute_semantic_similarity
from evaluator import evaluate_suggestions


def run_match_agent(request: MatchRequest) -> MatchResult:
    """
    Seven-step agentic pipeline:
    1. LLM match scoring
    2. Semantic similarity (embeddings)
    3. Gap analysis
    4. ATS keyword suggestions  ← new
    5. Resume suggestions (ATS-aware)
    6. Interview question generation
    7. Self-eval judge
    """

    print("🔍 Step 1/7: Scoring match...")
    match_score = score_match(request.resume_text, request.job_description)

    print("📐 Step 2/7: Computing semantic similarity...")
    semantic = compute_semantic_similarity(request.resume_text, request.job_description)

    print("🔎 Step 3/7: Analyzing gaps...")
    gap_analysis = analyze_gaps(
        request.resume_text,
        request.job_description,
        llm_score=match_score.score,
        semantic=semantic,
    )

    score_gap = match_score.score - semantic.percentage
    if score_gap >= 15:
        print(f"⚠️  Score divergence: {match_score.score} LLM vs {semantic.percentage} semantic — ATS vocabulary gap detected")

    print("🏷️ Step 4/7: Extracting ATS keywords...")
    ats_keywords = suggest_ats_keywords(
        request.resume_text,
        request.job_description,
        llm_score=match_score.score,
        semantic_percentage=semantic.percentage,
    )

    print("✍️ Step 5/7: Generating resume suggestions...")
    suggestions = suggest_improvements(
        request.resume_text,
        request.job_description,
        gap_analysis,
        semantic=semantic,
        llm_score=match_score.score,
    )

    print("🎤 Step 6/7: Generating interview questions...")

    interview_questions = generate_interview(
    request.resume_text,
    request.job_description,
    )

    result = MatchResult(
    match_score=match_score,
    gap_analysis=gap_analysis,
    resume_suggestions=suggestions,
    semantic_similarity=semantic,
    ats_keywords=ats_keywords,
    interview_questions=interview_questions,
    )

    print("⚖️ Step 7/7: Running self-eval on suggestions...")

    eval_report = evaluate_suggestions(result, request.job_description)
    result.eval_report = cast(EvalReport, eval_report)

    return result

