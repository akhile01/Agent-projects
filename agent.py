from langchain.agents import create_agent

from langsmith import Client

import gradio as gr # Add this when the time for deployment comes

from llm import GroqLLM
from lang import web_search_tool, get_weather_update

class AIAgent:
    def __init__(self):
        tools = [web_search_tool, get_weather_update]

        client = Client()
        prompt = client.pull_prompt("hwchase17/react",
                                    dangerously_pull_public_prompt=True)

        prompt_template_string = prompt.template

        groq_llm = GroqLLM()
        llm = groq_llm.get_llm()

        self.react_agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt=prompt_template_string
        )

    def run_agent(self, query: str):
        response = self.react_agent.invoke(
            {"messages": [{"role": "user", "content": query}]}
        )

        print("\n\n\nACTUAL RESPONSE WITH TOOLS\n\n\n", response)

        return response["messages"][-1].content

    def deploy_agent(self):
        iface = gr.Interface(
            fn=self.run_agent,
            inputs=gr.Textbox(
                label="Ask a question to your AI Agent",
                placeholder="e.g., Find the capital of Madhya Pradesh, then find it's current weather condition",
                lines=2
            ),
            outputs=gr.Textbox(label="Response", lines=10),
            title="AI Agent with Web Access",
            description="This AI Agent has access to the internet. You can ask anything and it will search the web to get you your answer.",
            examples=[
                ["Differentiate between VectorDB and Vector Store"],
                ["What is RAG model?"],
                ["What is the current market cap of NVIDIA"]
            ]
        )

        iface.launch(share=True)

if __name__ == "__main__":
    ai_agent = AIAgent()

    # response = ai_agent.run_agent("Find the capital of Madhya Pradesh, then find it's current weather condition")

    # print(response)

    ai_agent.deploy_agent()