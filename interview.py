from models import InterviewQuestions
from tools import generate_interview_questions


def generate_interview(
    resume_text: str,
    job_description: str,
) -> InterviewQuestions:

    return generate_interview_questions(
        resume_text,
        job_description,
    )