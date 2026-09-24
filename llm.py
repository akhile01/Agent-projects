from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os
load_dotenv()
class GroqLLM:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.llm = None

        if self.api_key:
            self.llm = ChatGroq(
                model="openai/gpt-oss-120b",
                temperature=0.5,
                max_tokens=512,
                api_key=self.api_key,
            )

    def run_llm(self, query: str) -> str:
        if self.llm is None:
            raise RuntimeError("GROQ_API_KEY is not set. Add it to your environment or .env file.")

        response = self.llm.invoke(query)
        return str(getattr(response, "content", response))

    def get_llm(self):
        return self.llm


if __name__ == "__main__":
    user_input = input("Ask a question to the LLM:\n")

    llm = GroqLLM()
    try:
        response = llm.run_llm(user_input)
    except RuntimeError as exc:
        print(f"\n\nUnable to run the model: {exc}")
    else:
        print("\n\n\nCLEAN RESPONSE\n\n\n", response)
