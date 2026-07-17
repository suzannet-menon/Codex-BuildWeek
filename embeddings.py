from typing import Any

from pydantic import BaseModel
from models import SemanticScore

try:
    from sentence_transformers import SentenceTransformer, util  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - handled at runtime
    SentenceTransformer = None  # type: ignore[assignment]
    util = None  # type: ignore[assignment]

_model = None


def _get_model() -> Any:
    """Lazy-load model so startup is fast."""
    global _model
    if _model is None:
        if SentenceTransformer is None or util is None:
            raise ImportError(
                "sentence-transformers is not installed. Install it with "
                "'pip install sentence-transformers' before using embeddings."
            )
        print("Loading embedding model (first run only)...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


# class SemanticScore(BaseModel):
#     score: float  # 0.0 to 1.0
#     percentage: int  # 0 to 100
#     interpretation: str


def compute_semantic_similarity(resume_text: str, job_description: str) -> SemanticScore:
    """
    Compute cosine similarity between resume and job description embeddings.
    This is a mathematical signal independent of the LLM's opinion.
    """
    model = _get_model()

    resume_embedding = model.encode(resume_text, convert_to_tensor=True)
    job_embedding = model.encode(job_description, convert_to_tensor=True)

    assert util is not None, "sentence-transformers util module must be available"
    similarity = float(util.cos_sim(resume_embedding, job_embedding)[0][0])
    # cosine similarity ranges -1 to 1; clamp to 0–1 for display
    similarity = max(0.0, min(1.0, similarity))
    percentage = round(similarity * 100)

    if percentage >= 75:
        interpretation = "Strong semantic alignment — your resume language closely mirrors the job description."
    elif percentage >= 55:
        interpretation = "Moderate alignment — key themes overlap but vocabulary could be closer to the job description."
    elif percentage >= 35:
        interpretation = "Weak alignment — significant language mismatch. Mirror the job description's terminology more closely."
    else:
        interpretation = "Very low alignment — the resume and job description are talking about very different things."

    return SemanticScore(
        score=round(similarity, 4),
        percentage=percentage,
        interpretation=interpretation,
    )