# AI Resume + Job Match Agent

An agentic system that analyzes how well a resume matches a job description — then tells you exactly what to fix.

Built with Groq (Llama 3.3 70B) + FastAPI. Three specialized LLM tools run in sequence, each focused on one task.

---

## What it does

1. **Scores the match** (0–100) with reasoning and skill breakdown
2. **Identifies gaps** — missing skills, experience, and ATS keywords
3. **Suggests resume improvements** — specific rewrites tailored to the job

---

## Architecture

```
User Request
     │
     ▼
┌─────────────┐
│  FastAPI    │  ← /match (text) or /match/pdf (PDF upload)
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────┐
│              Agent Orchestrator         │
│                                         │
│  Tool 1: score_match()                  │
│    └─ Groq LLM → MatchScore             │
│                                         │
│  Tool 2: analyze_gaps()                 │
│    └─ Groq LLM → GapAnalysis            │
│                                         │
│  Tool 3: suggest_improvements()         │
│    └─ Groq LLM (uses gap context)       │
│         → ResumeSuggestions             │
└─────────────────────────────────────────┘
       │
       ▼
  Structured JSON Response (Pydantic validated)
```

---

## Setup

```bash
git clone https://github.com/yourusername/resume-job-match-agent
cd resume-job-match-agent
pip install -r requirements.txt
```

Create a `.env` file:

```
GROQ_API_KEY=your_groq_api_key_here
```

Get a free Groq API key at [console.groq.com](https://console.groq.com)

---

## Run

```bash
uvicorn main:app --reload
```

API docs available at: `http://localhost:8000/docs`

---

## Example: Text Input

```bash
curl -X POST http://localhost:8000/match \
  -H "Content-Type: application/json" \
  -d '{
    "resume_text": "Python developer with 3 years experience in Django and REST APIs...",
    "job_description": "We are looking for a Senior AI Engineer with experience in LLMs, LangChain..."
  }'
```

## Example: PDF Upload

```bash
curl -X POST http://localhost:8000/match/pdf \
  -F "resume_pdf=@your_resume.pdf" \
  -F "job_description=We are looking for a Senior AI Engineer..."
```

---

## Sample Response

```json
{
  "match_score": {
    "score": 62,
    "reasoning": "Strong Python and API background, but lacks LLM and agentic AI experience required for this role.",
    "strong_matches": ["Python", "REST APIs", "backend development"],
    "weak_matches": ["AI experience", "cloud deployment"]
  },
  "gap_analysis": {
    "missing_skills": [
      "LangChain",
      "LangGraph",
      "vector databases",
      "prompt engineering"
    ],
    "missing_experience": ["LLM application development", "RAG pipelines"],
    "missing_keywords": ["agentic AI", "embeddings", "fine-tuning"],
    "priority_gaps": [
      "LLM frameworks",
      "RAG experience",
      "AI project portfolio"
    ]
  },
  "resume_suggestions": {
    "suggestions": [
      {
        "section": "Skills",
        "original": null,
        "suggestion": "Add: LangChain, Groq API, Prompt Engineering, Vector Databases (FAISS/Chroma)",
        "reason": "These are core ATS keywords listed in the job description"
      },
      {
        "section": "Experience",
        "original": "Built REST APIs using Django",
        "suggestion": "Built and deployed REST APIs using Django, integrating LLM-powered endpoints for automated data processing",
        "reason": "Reframes existing experience to highlight AI relevance"
      }
    ],
    "summary_advice": "Your backend foundation is solid. Focus on adding 1-2 LLM projects to your portfolio and reframe existing work to highlight automation and AI-adjacent experience."
  }
}
```

---

## Tech Stack

| Component           | Tool                             |
| ------------------- | -------------------------------- |
| LLM                 | Groq API — Llama 3.3 70B         |
| Agent orchestration | Sequential tool calling (Python) |
| API framework       | FastAPI                          |
| PDF parsing         | PyMuPDF                          |
| Schema validation   | Pydantic v2                      |

---

## Project Structure

```
resume-job-match-agent/
├── main.py          # FastAPI app and endpoints
├── agent.py         # Agent orchestration logic
├── tools.py         # Three LLM tools (score, gaps, suggestions)
├── models.py        # Pydantic input/output schemas
├── utils.py         # PDF text extraction
├── requirements.txt
└── README.md
```
