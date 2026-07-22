# ResumePilot — AI Resume and Candidate Evaluation Engine

> Paste or upload your resume, provide a job description, and receive. Get a match score, a gap analysis, ATS keyword suggestions, tailored resume rewrites, mock interview questions with answers, and a downloadable, professionally formatted PDF report — all in one pass.

Built during **OpenAI Build Week — Cafe Codex, Pune**.

---

## What this project does

ResumePilot is an end-to-end job-application assistant for students, early-career candidates, and job seekers applying to multiple roles. It doesn't just tell you *whether* your resume matches a job — it tells you *why*, *what's missing*, and *exactly how to fix it*, then backs that up with a self-graded quality check so the advice isn't just generic filler.

Given a **resume** (pasted text or PDF upload) and a **job description**, the system produces:

1. **LLM Match Score** (0–100) — an AI-judged score with reasoning
2. **Semantic Similarity Score** — an independent, embedding-based similarity score, so you get both a "does this sound right" judgment and a "does this literally overlap" measurement
3. **Gap Analysis** — missing skills, missing experience, missing ATS keywords, and a prioritized list of what to fix first
4. **Resume Improvement Suggestions** — section-by-section, before/after rewrites with a stated reason and a self-assigned quality score per suggestion
5. **Self-Eval Judge** — a second pass where the model grades its own suggestions for specificity and usefulness, rather than trusting the first output blindly
6. **Interview Questions with Answers** — mock interview questions generated from both your listed *skills/keywords* and your specific *projects*, each with a short, spoken-style model answer
7. **Downloadable PDF Report** — all of the above compiled into a single, clean PDF with a running header/footer

---

## How it works (user flow)

```
 ┌──────────────┐     ┌───────────────┐     ┌──────────────────┐
 │ Paste resume │ ──▶ │ Paste/upload  │ ──▶ │  Analyze &        │
 │ or upload PDF│     │ job description│     │  Generate Report  │
 └──────────────┘     └───────────────┘     └────────┬──────────┘
                                                       │
                       ┌───────────────────────────────┴───────────────────────────────┐
                       ▼                               ▼                              ▼
              LLM Match Score              Semantic Similarity              Gap Analysis
              (GPT-based reasoning)        (embedding cosine sim)           (skills/exp/ATS)
                       │                               │                              │
                       └───────────────────────────────┬───────────────────────────────┘
                                                        ▼
                                          Resume Suggestions + Self-Eval Judge
                                                        │
                                                        ▼
                                          Interview Questions (Skills + Projects)
                                                        │
                                                        ▼
                                       Downloadable PDF Report (header/footer, ordered sections)
```

**Step-by-step, as seen in the UI:**

1. User pastes resume text **or** uploads a resume PDF
2. User pastes the job description
3. User clicks **"Analyze & Generate Report →"**
4. Backend runs the analysis pipeline (score → semantic similarity → gap analysis → suggestions → self-eval → interview questions)
5. Progress is shown step-by-step (e.g. *"Step 1/7: Scoring match with LLM…"*)
6. Full report renders in-browser, with tabs/sections for each stage (Match Score, Semantic Similarity, Gap Analysis, Resume Suggestions, Self-Eval Judge, Interview Questions)
7. User can download the full report as a **PDF**
---

## Tech stack

| Layer | Technology |
|---|---|
| LLM reasoning | OpenAI API (GPT-based — match scoring, gap analysis, suggestions, interview Q&A) |
| Semantic similarity | Embedding-based cosine similarity using sentence-transformers (all-MiniLM-L6-v2), independent of the LLM's judgment |
| Backend framework | FastAPI |
| PDF generation | ReportLab (custom multi-page reports with dynamic headers & footers) (`SimpleDocTemplate`, `platypus` flowables, per-page header/footer via canvas callbacks) |
| Resume parsing | PDF text extraction (PyMuPDF / pypdf depending on branch) |
| Frontend | Single-page HTML/CSS/JS (`index.html`), served as a static file |
| Schema/validation | Structured data models (`models.py`) for match results, gap analysis, suggestions, and interview questions |

---

## Project structure

```
Codex-BuildWeek/
├── static/
│   └── index.html        # Frontend — resume input, JD input, results display, PDF buttons
├── agent.py              # Orchestration — runs the pipeline of tools in sequence
├── tools.py              # Individual LLM-backed tools (scoring, gap analysis, suggestions, etc.)
├── models.py             # Data models — MatchResult and related structured schemas
├── embeddings.py         # Semantic similarity via embeddings + cosine similarity
├── evaluator.py          # Self-eval / judge pass — grades suggestion quality
├── report.py             # PDF report generation — layout, section ordering, header/footer
├── interview.py          # Generates interview questions and sample answers
├── utils.py              # Shared helpers (e.g. resume text extraction)
├── main.py               # FastAPI app entrypoint and API routes
├── requirements.txt      # Python dependencies
├── runtime.txt           # Python runtime version pin
├── .python-version       # Local Python version pin
├── .gitignore            # Excludes .env, caches, IDE files, logs
└── README.md             # You are here
```

---

## Report structure (PDF output)

The generated PDF follows a fixed, intentional order:

1. **LLM Match Score** + **Semantic Similarity** + **Self-Eval Quality** (summary header)
2. **Match Analysis** (narrative explanation)
3. **Strong Matches** / **Partial Matches**
4. **Semantic Similarity** detail (cosine score + interpretation)
5. **Gap Analysis** — Missing Skills, Missing Experience, Missing ATS Keywords, Priority Gaps
6. **Resume Improvement Suggestions**, grouped by section, in this fixed order:
   - Summary / Skills / Experience (as generated)
   - **Leadership & Community**
   - **Certifications & Achievements**
   - **Projects**
7. **Interview Questions — Skills & Keywords** (5 questions, each with a short spoken-style answer)
8. **Interview Questions — Projects** (5 questions, each with a short spoken-style answer)
9. **Self-Eval Summary** — always the final section in the document

Every page carries a running **header** (candidate name, report title, target role) and **footer** (page number, generation date), rendered via ReportLab's per-page canvas callback so it updates correctly across a multi-page document.

---

## Setup

### 1. Clone and install

```bash
git clone https://github.com/suzannet-menon/Codex-BuildWeek.git
cd Codex-BuildWeek
pip install -r requirements.txt

> Recommended: Python 3.11
> Note: Python 3.14 is currently not fully supported by `sentence-transformers` on most deployment platforms.
```

### 2. Add your environment variables

Create a `.env` file in the project root (same folder as `main.py`):

```
OPENAI_API_KEY=your_actual_key_here
```

`.env` is already excluded via `.gitignore`, so your key won't be committed.

---

## Alternative: Using Grok Instead of OpenAI

If you don't have an OpenAI API key or your OpenAI credits have been exhausted, the project can also run using the **Grok (xAI) API** with only a few configuration changes.

### Step 1: Obtain a Grok API Key

1. Create an account on **xAI**.
2. Generate an API key from the developer dashboard.

---

### Step 2: Configure Environment Variables

Instead of using an OpenAI key, add the following to your `.env` file:

```env
OPENAI_API_KEY=your_grok_api_key
OPENAI_BASE_URL=https://api.x.ai/v1
```

The project is written using the OpenAI Python SDK, which is compatible with Grok by simply changing the API endpoint.

---

### Step 3: Update `tools.py`

Replace:

```python
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
```

with:

```python
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url=os.environ.get(
        "OPENAI_BASE_URL",
        "https://api.openai.com/v1"
    ),
)
```

This allows the project to work with either OpenAI or Grok without changing the rest of the code.

---

### Step 4: Change the Model Name

Replace:

```python
MODEL = "gpt-5.6"
```

with the Grok model you wish to use, for example:

```python
MODEL = "grok-4-fast-reasoning"
```

> **Note:** Model names may change over time. Refer to the latest xAI documentation for currently available Grok models.

---

### Step 5: Run the Application

Start the backend as usual:

```bash
uvicorn main:app --reload
```

No additional code changes are required.

---

### Files to Modify

If switching from OpenAI to Grok, only the following need to be updated:

| File | Changes |
|------|---------|
| `.env` | Add `OPENAI_BASE_URL=https://api.x.ai/v1` and your Grok API key |
| `tools.py` | Update the `OpenAI()` client to use `base_url` |
| `interview.py` | *(Only if it creates its own `OpenAI()` client)* |
| `evaluator.py` | *(Only if it creates its own `OpenAI()` client)* |

If these files reuse the same client from `tools.py`, no further modifications are necessary.

---

### Verification Checklist

After making the changes:

- ✅ Backend starts successfully
- ✅ Resume analysis works
- ✅ Match score is generated
- ✅ Gap analysis is generated
- ✅ ATS keyword suggestions are generated
- ✅ Resume suggestions are generated
- ✅ Interview questions are generated
- ✅ PDF report downloads successfully

If all of the above work correctly, the application has been successfully migrated from OpenAI to Grok.

### 3. Run the server

```bash
uvicorn main:app --reload
```

The app will be available at `http://localhost:8000`.

## Deployment Notes

This project can be deployed on Render.

Vercel currently has limitations for FastAPI applications using sentence-transformers because the model must be downloaded during deployment and exceeds the serverless function constraints.

If deploying on Vercel, consider disabling semantic similarity or replacing it with an API-based embedding provider.
--

## API endpoints (high level)

| Purpose | Description |
|---|---|
| Resume upload | Accepts pasted text or PDF upload, extracts resume text |
| Match analysis | Runs LLM scoring, semantic similarity, gap analysis, and suggestions |
| Interview questions | Generates skill-based and project-based questions with short answers |
| Report download | Compiles the full analysis into a formatted PDF |

---

## How did Codex and GPT 5.6 help us ?

Codex was central to building ResumePilot end to end. It helped scaffold the FastAPI backend and structured the agentic pipeline across scoring, gap analysis, and suggestion generation; debug and fix the PDF report generation logic (including a color-rendering bug that was breaking every export). GPT-5.6 powers the reasoning layer throughout for match scoring, gap analysis, ATS keyword extraction, resume rewrite suggestions, interview question generation, and the self-eval judge that grades suggestion quality before it reaches the user.

## Known limitations / next steps

- Currently supports PDF resume uploads only.
- Semantic similarity requires downloading the `all-MiniLM-L6-v2` embedding model on first run.
- No authentication or persistence layer is included; the application is stateless by design.
- Additional resume formats (e.g. DOCX) and deployment optimizations are planned for future versions.

---

*Built at OpenAI Build Week — Cafe Codex, Pune.*
