# 🎓 Scholarship AI Suite & RAG Advisor (Vercel Ready)

An intelligent, serverless scholarship assistant and grant calculation suite powered by **Groq Llama 3.3 70B** and **FastAPI**, designed for instant deployment on **Vercel**.

---

## ⚡ Features
1. **💬 Smart Q&A**: Real-time synthesized answers from official 2025 scholarship documents with source verification.
2. **⚡ Instant Eligibility & Grant Calculator**: Evaluates candidate eligibility and calculates total financial aid across the full degree duration (Tuition + Book allowances).
3. **✍️ AI Statement of Purpose (SOP) Drafter**: Generates personalized, committee-ready application essays.

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
3. Set **Root Directory** to `scholarship-ai-app`.
4. In **Environment Variables**, add:
   - `GROQ_API_KEY`: your Groq API key
5. Click **Deploy**!

### Option 2: Via Vercel CLI
```bash
cd scholarship-ai-app
vercel
```
Follow the CLI prompts and add `GROQ_API_KEY` when prompted.
