import os
from pathlib import Path
from dotenv import load_dotenv

import gradio as gr
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

try:
    from langchain_classic.chains import RetrievalQA
except ImportError:
    try:
        from langchain.chains import RetrievalQA
    except ImportError:
        from langchain_community.chains import RetrievalQA

from llm import GroqLLM

load_dotenv()


class RAGChainChat:
    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent
        self.vector_db_dir = self.base_dir / "vector_db"

        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is not set. Add it to your environment or .env file.")

        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="gemini-embedding-001",
            api_key=gemini_api_key,
        )
        self.vector_store = Chroma(
            embedding_function=self.embeddings,
            collection_name="scholarship_data",
            persist_directory=str(self.vector_db_dir),
        )
        self.groq_llm = GroqLLM()

    def _resolve_pdf_path(self, file_path: str | None = None) -> str:
        if file_path is None:
            file_path = "scholarship_info.pdf"

        candidate = Path(file_path).expanduser()
        if not candidate.is_absolute():
            candidate = (self.base_dir / candidate).resolve()

        if candidate.exists():
            return str(candidate)

        fallback = (self.base_dir / "scholarship_info.pdf").resolve()
        if fallback.exists():
            return str(fallback)

        raise FileNotFoundError(f"PDF file not found: {file_path}")

    def process_data(self, file_path: str | None = None, force_reload: bool = False):
        if not force_reload:
            try:
                if self.vector_store._collection.count() > 0:
                    return
            except Exception:
                pass

        resolved_path = self._resolve_pdf_path(file_path)
        self.loader = PyPDFLoader(resolved_path)
        pages = self.loader.load()

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=200,
            chunk_overlap=50,
        )

        chunks = self.splitter.split_documents(pages)
        self.vector_store.add_documents(chunks)

    def rag_retriever(self, k: int = 3):
        return self.vector_store.as_retriever(search_kwargs={"k": k})

    def rag_chain_chat(self, query: str) -> tuple[str, str]:
        """Returns answer and formatted source citations"""
        if not query or not query.strip():
            return "Please enter a question about the scholarship.", ""

        try:
            retriever = self.rag_retriever(k=3)
            llm = self.groq_llm.get_llm()

            rag_chain = RetrievalQA.from_chain_type(
                llm=llm,
                retriever=retriever,
                return_source_documents=True
            )

            response = rag_chain.invoke(query.strip())
            result_text = response.get("result", str(response))
            source_docs = response.get("source_documents", [])

            sources_md = ""
            if source_docs:
                sources_md = "### 📚 Retrieved Context Passages:\n"
                for idx, doc in enumerate(source_docs, 1):
                    src_name = Path(doc.metadata.get("source", "Document")).name
                    page_num = doc.metadata.get("page", 0) + 1
                    sources_md += f"\n**Source {idx}** (`{src_name}`, Page {page_num}):\n> {doc.page_content.strip()}\n"

            return result_text, sources_md
        except Exception as e:
            return f"Error answering question: {str(e)}", ""

    def check_eligibility_and_benefits(
        self,
        degree: str,
        annual_income: float,
        marks_percentage: float,
        course_years: int,
        selected_documents: list[str]
    ) -> str:
        """Unique Feature: Instant Eligibility Assessment & Total Grant Calculator"""
        is_undergrad = degree.lower() == "undergraduate"
        income_pass = annual_income < 600000
        marks_pass = marks_percentage >= 60.0

        required_docs = ["Income Certificate", "Aadhaar Card", "Bank Passbook", "Marksheet"]
        selected_set = set(selected_documents or [])
        missing_docs = [doc for doc in required_docs if doc not in selected_set]

        # Financial Grant Calculator (10,000 per sem + 3,000 book allowance per year)
        semesters = int(course_years) * 2
        tuition_total = semesters * 10000
        books_total = int(course_years) * 3000
        total_grant = tuition_total + books_total

        all_passed = is_undergrad and income_pass and marks_pass

        # Formatting Output
        status_header = "## ✅ Status: ELIGIBLE FOR SCHOLARSHIP 2025" if all_passed else "## ❌ Status: CURRENTLY INELIGIBLE"
        if not all_passed and (income_pass or marks_pass):
            status_header = "## ⚠️ Status: PARTIALLY ELIGIBLE (Conditions Not Met)"

        report = f"""{status_header}

---

### 📊 Eligibility Criteria Breakdown
| Requirement | Threshold | Your Details | Result |
| :--- | :--- | :--- | :--- |
| **Degree Level** | Undergraduate | {degree} | {'✅ Pass' if is_undergrad else '❌ Must be Undergraduate'} |
| **Annual Family Income** | < ₹6,00,000 | ₹{annual_income:,.0f} | {'✅ Pass' if income_pass else '❌ Exceeds ₹6,00,000'} |
| **Academic Performance** | ≥ 60.0% marks | {marks_percentage:.1f}% | {'✅ Pass' if marks_pass else '❌ Below 60.0%'} |

---

### 💰 Estimated Financial Benefits ({course_years} Year Course)
* **Tuition Assistance**: ₹10,000 / semester × {semesters} semesters = **₹{tuition_total:,.0f}**
* **Annual Book Allowance**: ₹3,000 / year × {course_years} years = **₹{books_total:,.0f}**
* 🎯 **Total Estimated Award Value**: <span style="color:#22c55e; font-size:1.2em; font-weight:bold;">₹{total_grant:,.0f}</span>

---

### 📑 Document Verification Checklist ({len(selected_set)}/{len(required_docs)} Ready)
"""
        for doc in required_docs:
            if doc in selected_set:
                report += f"- ✅ **{doc}**: Ready\n"
            else:
                report += f"- ❌ **{doc}**: Missing - You must arrange this before applying!\n"

        report += """
---
### 🚀 Next Steps & Application Link
* **Deadline**: October 15, 2025
* **Official Portal**: Register under the National Scholarship Portal at [https://scholarships.gov.in](https://scholarships.gov.in)
"""
        return report

    def generate_sop(
        self,
        student_name: str,
        course_name: str,
        financial_background: str,
        career_goals: str,
        tone: str
    ) -> str:
        """Unique Feature: AI Scholarship SOP & Application Essay Generator"""
        if not student_name or not course_name:
            return "Please provide at least your Name and Course Name to generate your Statement of Purpose."

        llm = self.groq_llm.get_llm()
        if not llm:
            return "Groq LLM is not initialized. Please check your GROQ_API_KEY."

        prompt = f"""
You are an expert scholarship advisor helping students win academic grants.
Write a compelling, structured, and heartfelt Scholarship Statement of Purpose (SOP) / Financial Need Essay.

Student Details:
- Name: {student_name}
- Enrolled Course: {course_name}
- Financial Background / Need: {financial_background or "Middle/low-income family striving for higher education"}
- Career Aspirations & Impact: {career_goals or "To contribute significantly to technology and society"}
- Desired Tone: {tone}

Requirements:
1. Include a strong opening expressing intent to apply for the Scholarship 2025.
2. Articulate academic dedication and why this course matters.
3. Sincerely explain the financial background and how the ₹10,000/semester tuition + ₹3,000 book allowance will alleviate burden.
4. Detail long-term vision and commitment to giving back.
5. Professional closing thanking the scholarship committee.

Keep it well-structured with clear paragraphs, professional formatting, and between 300 to 450 words.
"""
        try:
            res = llm.invoke(prompt)
            return str(getattr(res, "content", res))
        except Exception as e:
            return f"Error generating SOP: {str(e)}"

    def upload_and_process_pdf(self, file_obj) -> str:
        """Unique Feature: Live Dynamic PDF Uploader & Indexing"""
        if file_obj is None:
            return "⚠️ Please upload a valid PDF file."

        try:
            pdf_path = file_obj.name if hasattr(file_obj, "name") else str(file_obj)
            loader = PyPDFLoader(pdf_path)
            pages = loader.load()

            splitter = RecursiveCharacterTextSplitter(
                chunk_size=250,
                chunk_overlap=50,
            )
            chunks = splitter.split_documents(pages)
            self.vector_store.add_documents(chunks)

            total_chunks = self.vector_store._collection.count()
            file_name = Path(pdf_path).name

            return (
                f"✅ Successfully ingested `{file_name}`!\n\n"
                f"- **Pages processed**: {len(pages)}\n"
                f"- **New chunks generated**: {len(chunks)}\n"
                f"- **Total indexed chunks in Chroma**: {total_chunks}\n\n"
                f"You can now immediately ask questions about this document in the **Smart Q&A** tab!"
            )
        except Exception as e:
            return f"❌ Failed to process PDF: {str(e)}"

    def build_ui(self):
        """Builds a rich, multi-tab Gradio UI"""
        with gr.Blocks(title="🎓 Scholarship AI Suite (RAG & Advisor)") as demo:
            gr.Markdown(
                """
                # 🎓 Scholarship AI Suite & RAG Advisor
                ### Intelligent Document RAG • Instant Grant Calculator • AI Statement of Purpose Drafter
                """
            )

            with gr.Tabs():
                # TAB 1: SMART Q&A
                with gr.Tab("💬 Smart Scholarship Q&A"):
                    gr.Markdown("Ask anything about eligibility, benefits, requirements, or deadlines from your scholarship knowledge base.")
                    with gr.Row():
                        with gr.Column(scale=3):
                            query_input = gr.Textbox(
                                label="Ask a question",
                                placeholder="e.g. What are the eligibility criteria? What is the deadline?",
                                lines=3
                            )
                            with gr.Row():
                                ask_btn = gr.Button("Ask Assistant", variant="primary")
                                clear_btn = gr.Button("Clear", variant="secondary")

                            gr.Examples(
                                examples=[
                                    ["What are the eligibility criteria for the scholarship?"],
                                    ["What documents are required to apply?"],
                                    ["What is the maximum family income limit?"],
                                    ["What financial benefits and allowances are provided?"],
                                    ["What is the deadline and how to apply?"]
                                ],
                                inputs=query_input
                            )

                        with gr.Column(scale=4):
                            answer_out = gr.Markdown(label="Response")
                            with gr.Accordion("🔍 Retrieved Source Citations", open=False):
                                sources_out = gr.Markdown()

                    ask_btn.click(
                        fn=self.rag_chain_chat,
                        inputs=query_input,
                        outputs=[answer_out, sources_out]
                    )
                    query_input.submit(
                        fn=self.rag_chain_chat,
                        inputs=query_input,
                        outputs=[answer_out, sources_out]
                    )
                    clear_btn.click(
                        fn=lambda: ("", ""),
                        inputs=None,
                        outputs=[answer_out, sources_out]
                    )

                # TAB 2: ELIGIBILITY & BENEFIT CALCULATOR
                with gr.Tab("⚡ Instant Eligibility & Grant Calculator"):
                    gr.Markdown("Check your qualification status instantly against the 2025 Scholarship criteria and compute your total grant over your degree duration.")
                    with gr.Row():
                        with gr.Column(scale=3):
                            degree_input = gr.Dropdown(
                                choices=["Undergraduate", "Postgraduate", "Diploma", "High School (12th)"],
                                value="Undergraduate",
                                label="Current Degree Level"
                            )
                            income_input = gr.Slider(
                                minimum=50000,
                                maximum=1500000,
                                step=25000,
                                value=350000,
                                label="Annual Family Income (₹)"
                            )
                            marks_input = gr.Slider(
                                minimum=30.0,
                                maximum=100.0,
                                step=0.5,
                                value=75.0,
                                label="Previous Exam Marks (%)"
                            )
                            years_input = gr.Radio(
                                choices=[1, 2, 3, 4, 5],
                                value=4,
                                label="Course Duration (Years)"
                            )
                            docs_input = gr.CheckboxGroup(
                                choices=["Income Certificate", "Aadhaar Card", "Bank Passbook", "Marksheet"],
                                value=["Income Certificate", "Aadhaar Card", "Marksheet"],
                                label="Documents You Currently Have"
                            )
                            calc_btn = gr.Button("Evaluate Eligibility & Calculate Grant", variant="primary")

                        with gr.Column(scale=4):
                            report_out = gr.Markdown(label="Assessment Report")

                    calc_btn.click(
                        fn=self.check_eligibility_and_benefits,
                        inputs=[degree_input, income_input, marks_input, years_input, docs_input],
                        outputs=report_out
                    )

                # TAB 3: AI ESSAY / SOP GENERATOR
                with gr.Tab("✍️ AI Scholarship SOP Drafter"):
                    gr.Markdown("Struggling to write your Statement of Purpose (SOP) or financial hardship letter? Let AI draft a personalized application letter.")
                    with gr.Row():
                        with gr.Column(scale=3):
                            name_input = gr.Textbox(label="Full Name", placeholder="e.g. Akhil Sharma")
                            course_input = gr.Textbox(label="Course & College", placeholder="e.g. B.Tech Computer Science, ABC Institute of Technology")
                            background_input = gr.Textbox(
                                label="Financial Background / Need",
                                placeholder="e.g. Farmer family from rural area, single earning parent, seeking tuition assistance",
                                lines=3
                            )
                            goals_input = gr.Textbox(
                                label="Career Goals & Aspirations",
                                placeholder="e.g. Aspire to become a Machine Learning Engineer and develop AI tools for agriculture",
                                lines=3
                            )
                            tone_input = gr.Dropdown(
                                choices=["Professional & Sincere", "Passionate & Inspiring", "Academic & Focused"],
                                value="Professional & Sincere",
                                label="Desired Essay Tone"
                            )
                            sop_btn = gr.Button("Generate Scholarship SOP", variant="primary")

                        with gr.Column(scale=4):
                            sop_out = gr.Markdown(label="Generated Statement of Purpose")

                    sop_btn.click(
                        fn=self.generate_sop,
                        inputs=[name_input, course_input, background_input, goals_input, tone_input],
                        outputs=sop_out
                    )

                # TAB 4: LIVE PDF INGESTION
                with gr.Tab("📁 Upload New Scholarship PDF"):
                    gr.Markdown("Upload any new scholarship notification PDF or circular to index it live into the Chroma vector database.")
                    with gr.Row():
                        with gr.Column(scale=3):
                            pdf_upload = gr.File(label="Upload Scholarship PDF", file_types=[".pdf"])
                            upload_btn = gr.Button("Index Document into RAG", variant="primary")
                        with gr.Column(scale=4):
                            upload_status = gr.Markdown()

                    upload_btn.click(
                        fn=self.upload_and_process_pdf,
                        inputs=pdf_upload,
                        outputs=upload_status
                    )

        return demo

    def deploy_gradio(self, share: bool = False, server_port: int = 7861):
        demo = self.build_ui()
        demo.launch(share=share, server_port=server_port)


if __name__ == "__main__":
    try:
        rag_chat = RAGChainChat()
        rag_chat.process_data()
    except (RuntimeError, FileNotFoundError) as exc:
        print(f"\nUnable to start the RAG pipeline: {exc}")
    else:
        print("\nStarting Gradio interface...")
        rag_chat.deploy_gradio(share=False)