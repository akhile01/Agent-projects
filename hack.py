import os
import ast
import operator
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.tools import tool
from langchain.agents import create_agent

import gradio as gr

load_dotenv()


# Define tools at module level
@tool
def analyze_job_description(job_description: str) -> str:
    """
    Analyze a job description and extract important skills,
    responsibilities and ATS keywords.
    """
    skills_database = [
        "python", "java", "c++", "javascript",
        "react", "node", "sql", "mysql",
        "mongodb", "aws", "docker", "kubernetes",
        "git", "machine learning", "deep learning",
        "ai", "genai", "rag", "langchain",
        "nlp", "pandas", "numpy", "tensorflow",
        "pytorch", "flask", "fastapi"
    ]

    found = []
    jd = job_description.lower()

    for skill in skills_database:
        if skill in jd:
            found.append(skill.title())

    return f"""
Job Description Analysis

Detected Skills:
{', '.join(found) if found else "No common skills detected"}

Total Skills Found: {len(found)}

Recommendation:
Focus your resume on these skills and include projects demonstrating them.
"""


@tool
def career_coach(question: str) -> str:
    """
    Gives career guidance, interview preparation,
    resume advice and learning roadmap.
    """
    return f"""
Career Coaching Advice

Question: {question}

General Advice:

• Build 3-5 strong projects.
• Keep your resume one page.
• Practice DSA regularly.
• Learn System Design basics.
• Contribute to GitHub.
• Customize your resume for every company.
• Prepare STAR-format interview answers.
• Continue learning AI Agents, RAG, LangChain and Cloud.

For personalized answers, combine this with resume information.
"""


@tool
def calculator(expression: str) -> str:
    """
    Evaluate mathematical expressions.
    Example: 20*40+50
    """
    allowed = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg
    }

    def eval_(node):
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.BinOp):
            return allowed[type(node.op)](
                eval_(node.left),
                eval_(node.right)
            )
        elif isinstance(node, ast.UnaryOp):
            return allowed[type(node.op)](
                eval_(node.operand)
            )
        else:
            raise TypeError()

    try:
        tree = ast.parse(expression, mode="eval")
        result = eval_(tree.body)
        return f"Answer = {result}"
    except Exception as e:
        return f"Error in calculation: {str(e)}"


class AiAgent:
    def __init__(self):
        self.GROQ_API_KEY = os.getenv("GROQ_API_KEY")
        self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        self.vector_store = None
        self.retriever = None
        self.interview_state = {
            "active": False,
            "questions": [],
            "current": 0,
            "score": 0
        }

        self.llm = ChatGroq(
            model="openai/gpt-oss-120b",
            temperature=0.5,
            max_tokens=512,
            api_key=self.GROQ_API_KEY
        )

    def process_pdf(self, file_path: str = "Profile.pdf") -> None:
        """Process PDF and store embeddings in vector database"""
        try:
            loader = PyPDFLoader(file_path)
            pages = loader.load()

            splitter = RecursiveCharacterTextSplitter(
                chunk_size=200,
                chunk_overlap=150
            )
            chunks = splitter.split_documents(pages)

            embeddings = GoogleGenerativeAIEmbeddings(
                model="gemini-embedding-001",
                api_key=self.GEMINI_API_KEY
            )

            self.vector_store = Chroma(
                embedding_function=embeddings,
                collection_name="profile_collection",
                persist_directory="./Hackathon/vector_db"
            )

            self.vector_store.add_documents(chunks)
            self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})
            print(f"Successfully processed {len(chunks)} chunks from {file_path}")
        except Exception as e:
            print(f"Error processing PDF: {str(e)}")

    def get_resume_data(self, query: str) -> str:
        """Retrieve resume data using vector similarity search"""
        try:
            if self.vector_store is None:
                embeddings = GoogleGenerativeAIEmbeddings(
                    model="gemini-embedding-001",
                    api_key=self.GEMINI_API_KEY
                )
                self.vector_store = Chroma(
                    embedding_function=embeddings,
                    collection_name="profile_collection",
                    persist_directory="./Hackathon/vector_db"
                )
                self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})

            results = self.retriever.invoke(query)
            return str(results) if results else "No relevant information found in resume"
        except Exception as e:
            return f"Error retrieving resume data: {str(e)}"

    def generate_interview_questions(self, user_request: str) -> str:
        """
        Generate personalized interview questions based on the resume
        and optionally a job description.
        """
        try:
            resume_data = self.get_resume_data(user_request)

            prompt = f"""
You are an experienced Senior Software Engineering interviewer.

Candidate Resume:
{resume_data}

User Request:
{user_request}

Generate:
1. 5 Technical Questions
2. 3 HR Questions
3. 2 Project-Based Questions
4. 2 Coding Questions

For each question include:
- Question:
- Why interviewer asks it:
- What makes a good answer:

Format everything nicely."""

            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            return f"Error generating interview questions: {str(e)}"

    def start_mock_interview(self, role: str) -> str:
        """
        Starts a mock interview.
        """
        try:
            resume_data = self.get_resume_data(role)

            prompt = f"""
You are a FAANG interviewer.

Candidate Resume:
{resume_data}

Role: {role}

Generate ONLY 10 interview questions.

Mix:
- Technical
- HR
- Resume
- Projects
- Problem Solving

Return them as a numbered list only."""

            response = self.llm.invoke(prompt).content

            questions = []
            for line in response.split("\n"):
                line = line.strip()
                if line and line[0].isdigit() and "." in line:
                    q = line.split(".", 1)[1].strip()
                    if q:
                        questions.append(q)

            self.interview_state["active"] = True
            self.interview_state["questions"] = questions[:10]
            self.interview_state["current"] = 0
            self.interview_state["score"] = 0

            return f"""
🎯 Mock Interview Started

Question 1/{len(questions)}:

{questions[0] if questions else "No questions generated"}

(Type your answer below)
"""
        except Exception as e:
            return f"Error starting mock interview: {str(e)}"

    def evaluate_interview_answer(self, answer: str) -> str:
        """
        Evaluate the user's interview answer and proceed to next question.
        """
        try:
            if not self.interview_state["active"] or not self.interview_state["questions"]:
                return "No active interview. Say 'Start Mock Interview' to begin."

            current_q_idx = self.interview_state["current"]
            current_question = self.interview_state["questions"][current_q_idx]

            # Evaluate answer
            prompt = f"""
You are evaluating an interview answer.

Question: {current_question}

Candidate's Answer: {answer}

Provide:
1. Score (0-10)
2. Strengths
3. Weaknesses
4. Better Answer

Format it nicely."""

            evaluation = self.llm.invoke(prompt).content

            # Update state for next question
            self.interview_state["current"] += 1

            # Check if interview is complete
            if self.interview_state["current"] >= len(self.interview_state["questions"]):
                self.interview_state["active"] = False
                summary = f"""
✅ Mock Interview Completed!

{evaluation}

📊 All {len(self.interview_state['questions'])} questions completed.

Great practice session! Keep improving!
"""
                return summary

            # Ask next question
            next_question = self.interview_state["questions"][self.interview_state["current"]]
            return f"""{evaluation}

---

Question {self.interview_state["current"] + 1}/{len(self.interview_state["questions"])}:

{next_question}

(Type your answer below)
"""
        except Exception as e:
            return f"Error evaluating answer: {str(e)}"

    def react_agent_with_tools(self, query: str) -> str:
        """Process user query with AI agent and tools"""
        try:
            # Check if user wants to start/continue interview
            query_lower = query.lower()
            if any(keyword in query_lower for keyword in ["start mock interview", "take my interview", "conduct interview", "interview me", "practice interview"]):
                # Extract role if mentioned
                role = query_lower.replace("start mock interview for ", "").replace("interview for ", "").strip() or "Software Engineer"
                return self.start_mock_interview(role)

            # Check if interview is active
            if self.interview_state["active"]:
                return self.evaluate_interview_answer(query)

            # Check if user wants interview questions generated
            if any(keyword in query_lower for keyword in ["generate interview questions", "interview questions for"]):
                return self.generate_interview_questions(query)

            # Normal agent flow
            @tool
            def get_resume_data_tool(question: str) -> str:
                """
                Get information about the person's background, experience and projects from the resume.
                Use this for questions about the person's skills, education, projects, or work experience.
                """
                return self.get_resume_data(question)

            # Create tools list
            tools = [
                get_resume_data_tool,
                analyze_job_description,
                career_coach,
                calculator
            ]

            # Create system prompt
            prompt_template_string = """You are CareerPilot AI, a professional AI Career Assistant.

You have multiple capabilities:

1. Resume RAG - Answer questions using the uploaded resume. Speak in first person as if you are the resume owner.

2. Job Description Analyzer - Analyze job descriptions and extract required skills, responsibilities, ATS keywords.

3. Career Coach - Help with internship/placement preparation, learning roadmaps, interview advice.

4. Calculator - Solve mathematical expressions when required.

5. Mock Interview - Say "Start Mock Interview" to begin a practice interview session.

Guidelines:
- Always determine whether a tool is needed
- Use Resume Tool for resume questions
- Use Job Analyzer when a user pastes a job description
- Use Calculator for numerical calculations
- Use Career Coach for interview, roadmap, career planning advice
- Be professional, friendly, concise, and accurate
- If resume information is unavailable, state that clearly
- Never fabricate experience or information"""

            # Create and invoke agent
            react_agent = create_agent(
                model=self.llm,
                tools=tools,
                system_prompt=prompt_template_string
            )

            response = react_agent.invoke(
                {"messages": [{"role": "user", "content": query}]}
            )

            return response["messages"][-1].content
        except Exception as e:
            return f"Error processing query: {str(e)}"

    def deploy_agent(self):
        """Deploy the AI agent as a Gradio interface"""
        iface = gr.Interface(
            fn=self.react_agent_with_tools,
            inputs=gr.Textbox(
                label="Ask CareerPilot AI",
                placeholder="e.g., Tell me about yourself OR Start a mock interview OR Generate interview questions",
                lines=3
            ),
            outputs=gr.Textbox(
                label="Response",
                lines=12
            ),
            title="🚀 CareerPilot AI - Your Digital Career Assistant",
            description="AI-powered assistant with resume analysis, job matching, career coaching, mock interviews, and more. Upload your resume first for best results.",
            examples=[
                ["Tell me about yourself"],
                ["What are your key projects?"],
                ["Analyze this job description: Python, SQL, Docker, AWS, FastAPI"],
                ["Generate interview questions for an AI Engineer role"],
                ["Start a mock interview for Software Engineer"],
                ["How should I prepare for Google interviews?"],
                ["Calculate 25*400+1200"]
            ]
        )

        iface.launch(share=True)


if __name__ == "__main__":
    ai_agent = AiAgent()

    # 1. FIRST TIME SETUP - Uncomment to process your resume PDF
    # ai_agent.process_pdf("Profile.pdf")

    # 2. Deploy the AI Agent
    ai_agent.deploy_agent()
