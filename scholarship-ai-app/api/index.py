import os
import re
from urllib.parse import parse_qs
from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

app = FastAPI(title="Scholarship AI Suite API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VercelPathCorrectionMiddleware:
    """Corrects rewritten paths in Vercel serverless functions so FastAPI routes match properly."""
    def __init__(self, asgi_app):
        self.asgi_app = asgi_app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            current_path = scope.get("path", "")
            headers = dict(scope.get("headers", []))
            header_map = {k.decode("latin1").lower(): v.decode("latin1") for k, v in headers.items()}
            
            matched_path = (
                header_map.get("x-matched-path") or 
                header_map.get("x-forwarded-uri") or 
                header_map.get("x-real-path")
            )
            
            query_path = None
            query_string = scope.get("query_string", b"").decode("latin1")
            if "__path__=" in query_string:
                qs = parse_qs(query_string)
                if "__path__" in qs and qs["__path__"]:
                    query_path = qs["__path__"][0]

            resolved_path = None
            if matched_path and not matched_path.endswith("index.py"):
                resolved_path = matched_path.split("?")[0]
            elif query_path:
                resolved_path = query_path.split("?")[0]

            if resolved_path and resolved_path != current_path:
                scope["path"] = resolved_path
                scope["raw_path"] = resolved_path.encode("latin1")

        await self.asgi_app(scope, receive, send)

app.add_middleware(VercelPathCorrectionMiddleware)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

SCHOLARSHIP_CONTEXT = """
Title: Scholarship Information 2025

1. Eligibility:
- Open to students in India pursuing undergraduate degrees.
- Annual family income must be below ₹6,00,000.
- Minimum 60% marks in the last qualifying examination.

2. Documents Required:
- Income certificate
- Aadhaar card
- Bank passbook
- Marksheet

3. Deadline: October 15, 2025

4. Benefits:
- ₹10,000 per semester for tuition
- Book allowance of ₹3,000 per year

5. How to Apply:
Visit https://scholarships.gov.in and register under the NSP portal (National Scholarship Portal).
"""

def get_groq_client():
    key = os.getenv("GROQ_API_KEY") or GROQ_API_KEY
    if not key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY is not configured.")
    return Groq(api_key=key)


class ChatRequest(BaseModel):
    query: str

class CalculateRequest(BaseModel):
    degree: str
    annual_income: float
    marks_percentage: float
    course_years: int
    selected_documents: list[str] = []

class SopRequest(BaseModel):
    student_name: str
    course_name: str
    financial_background: str = ""
    career_goals: str = ""
    tone: str = "Professional & Sincere"


router = APIRouter()

@router.get("/")
@router.get("/health")
def health():
    return {"status": "ok", "service": "Scholarship AI Suite"}


@router.post("/chat")
def chat(req: ChatRequest):
    query = req.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    client = get_groq_client()
    system_prompt = f"""You are the official AI Advisor for Scholarship Information 2025.
Use ONLY the official scholarship details below to answer the user's question accurately, concisely, and professionally.
If information is not provided in the source text, state clearly that it is not covered.

Official Scholarship Context:
{SCHOLARSHIP_CONTEXT}
"""

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            temperature=0.3,
            max_tokens=600,
        )
        answer = completion.choices[0].message.content
        return {
            "answer": answer,
            "sources": [
                {
                    "title": "Scholarship Information 2025 Document",
                    "snippet": "Eligibility: Undergrad in India, Income < ₹6L, Min 60% marks. Benefits: ₹10k/sem tuition + ₹3k/yr books. Deadline: Oct 15, 2025. Portal: scholarships.gov.in"
                }
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calculate")
def calculate(req: CalculateRequest):
    is_undergrad = req.degree.strip().lower() == "undergraduate"
    income_pass = req.annual_income < 600000
    marks_pass = req.marks_percentage >= 60.0

    required_docs = ["Income Certificate", "Aadhaar Card", "Bank Passbook", "Marksheet"]
    selected_set = set(req.selected_documents)
    missing_docs = [doc for doc in required_docs if doc not in selected_set]

    semesters = int(req.course_years) * 2
    tuition_total = semesters * 10000
    books_total = int(req.course_years) * 3000
    total_grant = tuition_total + books_total

    all_passed = is_undergrad and income_pass and marks_pass

    status = "ELIGIBLE" if all_passed else ("PARTIALLY_ELIGIBLE" if (income_pass or marks_pass) else "INELIGIBLE")

    return {
        "status": status,
        "is_undergrad": is_undergrad,
        "income_pass": income_pass,
        "marks_pass": marks_pass,
        "all_passed": all_passed,
        "tuition_per_sem": 10000,
        "tuition_total": tuition_total,
        "books_per_year": 3000,
        "books_total": books_total,
        "total_grant": total_grant,
        "course_years": req.course_years,
        "semesters": semesters,
        "missing_docs": missing_docs,
        "completed_docs": list(selected_set.intersection(required_docs)),
        "deadline": "October 15, 2025",
        "portal_url": "https://scholarships.gov.in"
    }


@router.post("/generate-sop")
def generate_sop(req: SopRequest):
    if not req.student_name or not req.course_name:
        raise HTTPException(status_code=400, detail="Student name and course are required.")

    client = get_groq_client()
    prompt = f"""
Write a formal, compelling, and sincere Statement of Purpose (SOP) / Financial Need Essay for an applicant applying to the Scholarship 2025 program.

Applicant Profile:
- Full Name: {req.student_name}
- Course / Degree: {req.course_name}
- Financial Background & Need: {req.financial_background or 'Coming from a low-to-middle income household with high dedication to higher education'}
- Career Goals & Aspirations: {req.career_goals or 'To excel in my academic field and contribute to societal growth'}
- Desired Tone: {req.tone}

Key Guidelines:
1. Clear opening stating intent to apply for the Scholarship 2025 on the National Scholarship Portal.
2. Outline academic commitment and why this degree is pivotal for their trajectory.
3. Transparently address financial need, mentioning how the ₹10,000/semester tuition fee grant and ₹3,000/year book allowance will enable them to focus on academics.
4. Conclude with a promise of academic excellence and social impact.
5. Keep it professional, heartfelt, and structured across 4-5 well-composed paragraphs (350-450 words).
"""

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800,
        )
        sop_text = completion.choices[0].message.content
        return {"sop": sop_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Mount routes both with and without /api prefix for maximum compatibility across environments
app.include_router(router)
app.include_router(router, prefix="/api")
