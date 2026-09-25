# 🚀 NextRole AI - Digital Career Copilot (Vercel Ready)

An autonomous AI Career Copilot and interview simulator powered by **Groq Ultra-Fast AI** and **FastAPI**, designed for zero-config serverless deployment on **Vercel**.

---

## ⚡ Features
1. **💬 Candidate Assistant**: Semantic profile and resume Q&A highlighting key AI agent projects, stack proficiencies, and architecture designs.
2. **🎯 Job Description & ATS Scanner**: Extracts required keywords, computes candidate match rate, and generates targeted resume optimization tips.
3. **🎙️ FAANG-Grade Mock Interview Simulator**: Dynamic role-specific question generation and hiring-manager evaluation with scores (0–10) and model answers.
4. **🧭 Career Coach & Strategic Roadmaps**: Tailored 30-60-90 day learning plans and interview tactics.

---

## 🚀 Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   Create a `.env` file:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ```

3. **Run local server:**
   ```bash
   uvicorn api.index:app --reload --port 8000
   ```
   Open `public/index.html` or visit `http://127.0.0.1:8000`.

---

## 🌐 Deploy to Vercel

### Option 1: Via Vercel Dashboard (Easiest)
1. Push your repository to GitHub: `https://github.com/akhile01/Agent-projects`.
2. Go to [vercel.com/new](https://vercel.com/new) and import `Agent-projects`.
3. Set **Root Directory** to `careerpilot-ai-app`.
4. In **Environment Variables**, add:
   - `GROQ_API_KEY`: your Groq API key
5. Click **Deploy**!

### Option 2: Via Vercel CLI
```bash
cd careerpilot-ai-app
vercel
```
Follow the CLI prompts and add `GROQ_API_KEY` when prompted.
