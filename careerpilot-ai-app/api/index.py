import os
import ast
import operator
from urllib.parse import parse_qs
from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

app = FastAPI(title="CareerPilot AI API", version="1.0.0")

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

RESUME_CONTEXT = """
Candidate Profile:
Role: AI & Software Engineer, Automation Specialist
Background:
- Experience building AI Voice Agents for Automated Sales Conversations.
- Designed & deployed Custom GPTs and enterprise recommendation systems.
- Developed Cold DM Copywriting AI agents scaling high-conversion outreach.
- Engineered high-traffic Telegram Chatbots with automated workflows.
- Active hackathon participant, builder of functional AI solutions and modern web applications.
- Core Skills: Python, LangChain, Generative AI, RAG, ChromaDB, FastAPI, React, SQL, Cloud & APIs.
"""

SKILLS_DATABASE = [
    "python", "java", "c++", "javascript", "typescript",
    "react", "node", "sql", "mysql", "postgresql",
    "mongodb", "aws", "docker", "kubernetes", "git",
    "machine learning", "deep learning", "ai", "genai",
    "rag", "langchain", "nlp", "pandas", "numpy",
    "tensorflow", "pytorch", "flask", "fastapi"
]

def get_groq_client():
    key = os.getenv("GROQ_API_KEY") or GROQ_API_KEY
    if not key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY is not configured.")
    return Groq(api_key=key)


class ChatRequest(BaseModel):
    query: str

class JdRequest(BaseModel):
    job_description: str

class InterviewStartRequest(BaseModel):
    role: str = "Software Engineer"

class InterviewEvalRequest(BaseModel):
    question: str
    answer: str

class CoachRequest(BaseModel):
    question: str


router = APIRouter()

@router.get("/")
@router.get("/health")
def health():
    return {"status": "ok", "service": "CareerPilot AI"}


@router.post("/chat")
def chat(req: ChatRequest):
    query = req.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    client = get_groq_client()
    system_prompt = f"""You are CareerPilot AI, a professional Digital Career Assistant representing the candidate.
Speak with confidence, professionalism, and conciseness.
Answer questions about skills, projects, and experience using the candidate context below.
If a question is about career advice or interviews, offer strategic guidance.

Candidate Context:
{RESUME_CONTEXT}
"""

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            temperature=0.6,
            max_tokens=600,
        )
        return {"response": completion.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-jd")
def analyze_jd(req: JdRequest):
    jd = req.job_description.strip()
    if not jd:
        raise HTTPException(status_code=400, detail="Job description cannot be empty.")

    jd_lower = jd.lower()
    found_skills = [s.title() for s in SKILLS_DATABASE if s in jd_lower]
    
    candidate_skills = {"Python", "Git", "Machine Learning", "Ai", "Genai", "Rag", "Langchain", "Fastapi", "React", "Sql"}
    matching_skills = [s for s in found_skills if s in candidate_skills]
    missing_skills = [s for s in found_skills if s not in candidate_skills]
    
    match_percentage = int((len(matching_skills) / max(len(found_skills), 1)) * 100) if found_skills else 0

    client = get_groq_client()
    prompt = f"""
Analyze this job description and provide 3 strategic recommendations for optimizing a resume for it.

Job Description:
{jd[:1500]}

Detected Skills: {', '.join(found_skills) if found_skills else 'General software skills'}
Matching Candidate Skills: {', '.join(matching_skills)}
Missing / Skills to Highlight: {', '.join(missing_skills)}

Provide your response in 3 structured sections:
1. Keyword & ATS Alignment Strategy
2. Relevant Projects to Emphasize
3. Interview Focus Area
"""
    try:
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=500,
        )
        advice = res.choices[0].message.content
    except Exception:
        advice = "Focus your resume on demonstrating quantifiable impact with the required skills."

    return {
        "detected_skills": found_skills,
        "matching_skills": matching_skills,
        "missing_skills": missing_skills,
        "match_percentage": match_percentage,
        "total_skills_count": len(found_skills),
        "advice": advice
    }


@router.post("/mock-interview/start")
def start_interview(req: InterviewStartRequest):
    role = req.role.strip() or "Software Engineer"
    client = get_groq_client()

    prompt = f"""
Generate 5 targeted, high-yield interview questions for a {role} candidate.
Include:
- 2 Technical / Architecture questions
- 1 System Design / Problem Solving question
- 1 Behavioral / STAR question
- 1 Project-based question

Return ONLY a numbered list (1 to 5), with no conversational filler.
"""
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500,
        )
        raw_text = completion.choices[0].message.content
        questions = []
        for line in raw_text.split("\n"):
            line = line.strip()
            if line and line[0].isdigit() and "." in line:
                q = line.split(".", 1)[1].strip()
                if q:
                    questions.append(q)
        return {"role": role, "questions": questions[:5]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mock-interview/evaluate")
def evaluate_interview(req: InterviewEvalRequest):
    if not req.question or not req.answer:
        raise HTTPException(status_code=400, detail="Question and answer are required.")

    client = get_groq_client()
    prompt = f"""
You are an expert FAANG hiring manager evaluating a candidate's interview response.

Question Asked:
{req.question}

Candidate's Answer:
{req.answer}

Provide an honest, constructive critique:
1. Score (out of 10)
2. What was done well (Strengths)
3. What was missing or could be improved (Weaknesses)
4. An Exemplary Model Answer (How a Staff Engineer would answer)

Keep the formatting clean and impactful.
"""
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=700,
        )
        return {"evaluation": completion.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/career-coach")
def career_coach(req: CoachRequest):
    q = req.question.strip()
    if not q:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    client = get_groq_client()
    prompt = f"""
You are a Principal Engineer and Elite Career Mentor.
Provide an actionable, structured coaching plan for this question:

Question: {q}

Include:
1. Executive Summary & Strategy
2. Step-by-Step 30-60-90 Day Action Plan or Technical Roadmap
3. Common Pitfalls to Avoid
4. Recommended Books/Resources/Certifications
"""
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=750,
        )
        return {"coaching": completion.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Mount routes both with and without /api prefix for maximum compatibility across environments
app.include_router(router)
app.include_router(router, prefix="/api")
