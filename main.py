# FastAPI app

import os
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles

from models import MatchRequest, MatchResult
from agent import run_match_agent
from utils import extract_text_from_pdf
from report import generate_pdf_report

app = FastAPI(
    title="AI Resume + Job Match Agent",
    description="Agentic system with semantic similarity, gap analysis, suggestions, and self-eval.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def serve_frontend():
    return FileResponse("static/index.html")


@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/match", response_model=MatchResult)
def match_text(request: MatchRequest):
    try:
        return run_match_agent(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/match/pdf-upload", response_model=MatchResult)
async def match_pdf(
    resume_pdf: UploadFile = File(...),
    job_description: str = Form(...),
):
    if not resume_pdf.filename or not resume_pdf.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    try:
        pdf_bytes = await resume_pdf.read()
        resume_text = extract_text_from_pdf(pdf_bytes)
        if not resume_text:
            raise HTTPException(status_code=400, detail="Could not extract text from PDF.")
        return run_match_agent(MatchRequest(resume_text=resume_text, job_description=job_description))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/match/report")
def match_and_download(request: MatchRequest):
    """Run the agent and return a downloadable PDF report."""
    try:
        result = run_match_agent(request)
        pdf_bytes = generate_pdf_report(result)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=match_report.pdf"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/match/report-pdf-upload")
async def match_pdf_and_download(
    resume_pdf: UploadFile = File(...),
    job_description: str = Form(...),
):
    """Upload PDF resume, get a downloadable match report."""
    if not resume_pdf.filename or not resume_pdf.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files supported.")
    try:
        pdf_bytes = await resume_pdf.read()
        resume_text = extract_text_from_pdf(pdf_bytes)
        if not resume_text:
            raise HTTPException(status_code=400, detail="Could not extract text from PDF.")
        result = run_match_agent(MatchRequest(resume_text=resume_text, job_description=job_description))
        report_bytes = generate_pdf_report(result)
        return Response(
            content=report_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=match_report.pdf"},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


app.mount("/static", StaticFiles(directory="static"), name="static")