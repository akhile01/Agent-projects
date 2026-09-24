import os
import re
from pathlib import Path
from dotenv import load_dotenv

import gradio as gr
from langchain_core.tools import tool
from langchain.agents import create_agent
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_groq import ChatGroq
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document

# 1. Environment and Path Initialization
base_dir = Path(__file__).resolve().parent
env_path = base_dir / ".env"
load_dotenv(dotenv_path=env_path)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class CareerPilotCore:
    def __init__(self):
        self.vector_db_dir = base_dir / "vector_db_careerpilot"
        self.vector_store = None
        self.agent = None
        
        # Initialize Embeddings and LLM
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="gemini-embedding-001",
            api_key=GEMINI_API_KEY
        )
        self.llm = ChatGroq(
            model="openai/gpt-oss-120b",
            api_key=GROQ_API_KEY,
            temperature=0.5
        )
        
        # Automatically process resume if DB doesn't exist
        self.initialize_vector_db()
        self.setup_agent()
        
    def initialize_vector_db(self):
        """Loads and processes Profile.pdf if the vector database is not already initialized."""
        if self.vector_db_dir.exists():
            # Load existing
            self.vector_store = Chroma(
                embedding_function=self.embeddings,
                collection_name="careerpilot_collection",
                persist_directory=str(self.vector_db_dir)
            )
            return
            
        # If DB doesn't exist, search for Profile.pdf
        pdf_path = base_dir / "Profile.pdf"
        if not pdf_path.exists():
            # Create a mock document if Profile.pdf is missing
            print("Profile.pdf not found. Creating a generic resume document.")
            documents = [Document(
                page_content="Name: Akhil. Experience: Python Developer, Machine Learning Engineer. Skills: LangChain, ChromaDB, Gradio, Gemini API.",
                metadata={"source": "generic"}
            )]
        else:
            print(f"Processing PDF resume: {pdf_path}")
            loader = PyPDFLoader(str(pdf_path))
            documents = loader.load()
            
        splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=100)
        chunks = splitter.split_documents(documents)
        
        self.vector_store = Chroma(
            embedding_function=self.embeddings,
            collection_name="careerpilot_collection",
            persist_directory=str(self.vector_db_dir)
        )
        self.vector_store.add_documents(chunks)
        print(f"Successfully processed {len(chunks)} chunks into vector DB.")

    def get_resume_context(self, query: str) -> str:
        """Retrieves matching paragraphs from the user's resume."""
        if not self.vector_store:
            return "No resume data available."
        try:
            docs = self.vector_store.similarity_search(query, k=3)
            return "\n\n".join([d.page_content for d in docs])
        except Exception as e:
            return f"Error retrieving resume data: {str(e)}"

    def setup_agent(self):
        """Binds the RAG tool and creates the LangChain ReAct agent."""
        @tool
        def get_resume_data(query: str) -> str:
            """
            Retrieves background information, skills, experience, and projects from the candidate's resume.
            """
            return self.get_resume_context(query)
            
        tools = [get_resume_data]
        
        system_prompt = """You are CareerPilot AI, a helpful digital career assistant. You have access to the user's resume.
Answer questions about the candidate's skills, experience, projects, and career choices. Make sure to represent their qualifications accurately.
When asked to evaluate jobs or match descriptions, suggest how their experience lines up. Use professional markdown formatting including headers, tables, and bullet points in your responses."""
        
        self.agent = create_agent(
            model=self.llm,
            tools=tools,
            system_prompt=system_prompt
        )

    def query_agent(self, query: str) -> str:
        """Queries the ReAct agent and returns its final response."""
        if not query or len(query.strip()) == 0:
            return "Please input a career query."
        try:
            response = self.agent.invoke({"messages": [{"role": "user", "content": query}]})
            return response["messages"][-1].content
        except Exception as e:
            print(f"Agent execution failed: {e}. Falling back to standard RAG query.")
            # Fallback direct QA query
            context = self.get_resume_context(query)
            fallback_prompt = f"""
            You are CareerPilot AI. Answer this query based on the following resume context.
            Context:
            {context}
            
            Query: {query}
            """
            try:
                res = self.llm.invoke(fallback_prompt)
                return str(getattr(res, "content", res))
            except Exception as ex:
                return f"Error answering query: {str(ex)}"

# Initialize CareerPilot core
core = CareerPilotCore()

# --- Gradio UI Layout (Matching the screenshot layout) ---
demo = gr.Interface(
    fn=core.query_agent,
    inputs=gr.Textbox(
        label="Ask CareerPilot AI",
        placeholder="e.g., What are your technical skills? OR Analyze this job description...",
        lines=3
    ),
    outputs=gr.Textbox(
        label="Response",
        lines=12
    ),
    title="CareerPilot AI - Your Digital Career Assistant",
    description="AI-powered assistant with resume analysis, job matching, career coaching, and more. Upload your resume first for best results.",
    examples=[
        ["Tell me about yourself"],
        ["What are your key projects?"],
        ["What's your experience with Python and machine learning?"],
        ["How should I prepare for a software engineer interview?"]
    ]
)

if __name__ == "__main__":
    demo.launch(share=False)
