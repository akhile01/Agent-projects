# 🤖 Agent Projects

A collection of AI Agent and RAG (Retrieval-Augmented Generation) applications powered by **LangChain**, **Google Gemini Embeddings**, **ChromaDB**, and **Groq LLMs**, built with interactive **Gradio** user interfaces.

---

## 🚀 Projects Included

### 1. 🎓 Scholarship AI Suite & RAG Advisor (`rag.py`)
An intelligent RAG assistant and evaluation tool for scholarship discovery and application:
* **💬 Smart Q&A**: Ask questions regarding eligibility, deadlines, and benefits with source citations directly retrieved from scholarship documents.
* **⚡ Instant Eligibility & Grant Calculator**: Evaluates candidate eligibility (income threshold, academic percentage, degree level) and computes the total financial grant value across the complete degree duration.
* **✍️ AI Statement of Purpose (SOP) Drafter**: Automatically drafts tailored, compelling scholarship essays and financial need statements.
* **📁 Live Dynamic PDF Ingestion**: Drag-and-drop any new scholarship circular or brochure PDF to index it into ChromaDB in real-time.

### 2. 🚀 CareerPilot AI (`hack.py`)
An autonomous digital career coach and interview preparation assistant:
* **Resume RAG**: Semantic retrieval of candidate projects, experience, and background.
* **Job Description Analyzer**: Extracts technical keywords, required tools, and ATS alignment.
* **Mock Interview Simulator**: Conducts multi-turn mock interviews, scores answers (0–10), and gives actionable feedback.
* **Career Coaching & Calculator**: Generates career roadmaps and evaluates technical/mathematical expressions.

---

## 🛠️ Tech Stack
* **LLM Engine**: Groq (`openai/gpt-oss-120b`, `llama-3.3-70b-versatile`)
* **Vector Embeddings**: Google Generative AI (`gemini-embedding-001`)
* **Vector Store**: ChromaDB
* **Agent Framework**: LangChain & LangChain Classic
* **Web Interface**: Gradio

---

## 📦 Setup & Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/akhile01/Agent-projects.git
   cd Agent-projects
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure API Keys:**
   Create a `.env` file in the root directory (refer to `.env.example`):
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

---

## 🎯 Running the Applications

### Run the Scholarship AI Suite:
```bash
python rag.py
```
Open [http://127.0.0.1:7861](http://127.0.0.1:7861) in your browser.

### Run CareerPilot AI:
```bash
python hack.py
```
Open [http://127.0.0.1:7860](http://127.0.0.1:7860) in your browser.
