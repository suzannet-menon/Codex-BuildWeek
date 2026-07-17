#Pydantic schemas

from pydantic import BaseModel, Field
from typing import List, Optional


# Input Models 

class MatchRequest(BaseModel):
    resume_text: str = Field(..., description="Plain text content of the resume")
    job_description: str = Field(..., description="Full job description text")


# Tool Output Models (what each agent tool returns) 

class MatchScore(BaseModel):
    score: int = Field(..., ge=0, le=100, description="Match score from 0 to 100")
    reasoning: str = Field(..., description="Why this score was given")
    strong_matches: List[str] = Field(..., description="Skills/experience that match well")
    weak_matches: List[str] = Field(..., description="Skills/experience that partially match")


class GapAnalysis(BaseModel):
    missing_skills: List[str] = Field(..., description="Skills required but not found in resume")
    missing_experience: List[str] = Field(..., description="Experience gaps for this role")
    missing_keywords: List[str] = Field(..., description="ATS keywords missing from resume")
    priority_gaps: List[str] = Field(..., description="Top 3 gaps to address first")


class ResumeSuggestion(BaseModel):
    section: str = Field(..., description="Which resume section this applies to e.g. Experience, Skills")
    original: Optional[str] = Field(None, description="Original bullet or text if rewriting")
    suggestion: str = Field(..., description="Improved version or new addition")
    reason: str = Field(..., description="Why this change improves the match")


class ResumeSuggestions(BaseModel):
    suggestions: List[ResumeSuggestion]
    summary_advice: str = Field(..., description="Overall strategic advice for this application")


# Semantic Similarity 

class SemanticScore(BaseModel):
    score: float
    percentage: int
    interpretation: str


# Eval Report 

class SuggestionEval(BaseModel):
    suggestion_index: int
    quality_score: int
    is_specific: bool
    is_actionable: bool
    flag: str


class EvalReport(BaseModel):
    overall_quality: float
    evaluations: List[SuggestionEval]
    eval_summary: str


# ATS Keywords 
 
class ATSKeyword(BaseModel):
    keyword: str
    priority: str           # "high" | "medium" | "low"
    where_to_add: str       # which resume section to add it to
    usage_example: str      # example sentence using the keyword
 
 
class ATSKeywords(BaseModel):
    score_gap_detected: bool
    keywords: List[ATSKeyword]
    rewrite_advice: str     # concrete paragraph on vocabulary alignment


# Response Model 

class MatchResult(BaseModel):
    match_score: MatchScore
    gap_analysis: GapAnalysis
    resume_suggestions: ResumeSuggestions
    semantic_similarity: Optional[SemanticScore] = None
    ats_keywords: Optional[ATSKeywords] = None
    eval_report: Optional[EvalReport] = None
