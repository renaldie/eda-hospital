from langchain_ollama import ChatOllama
from langchain_openai import AzureChatOpenAI, ChatOpenAI
import os
from dotenv import load_dotenv
load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# llm = AzureChatOpenAI(
#     azure_endpoint="https://models.inference.ai.azure.com",
#     azure_deployment="gpt-4.1-mini",
#     openai_api_version="2025-03-01-preview", 
#     model_name="gpt-4.1-mini",
#     temperature=0.8,
#     api_key=GITHUB_TOKEN,
#     # output_version="responses/v1",
# )

llm = ChatOpenAI(
    model="gpt-5-nano",
    temperature=0.8,
    api_key=OPENAI_API_KEY,
    output_version="responses/v1",
    reasoning_effort="minimal",
)

# llm = ChatOllama(model="llama3.2:1b-instruct-q4_K_M", temperature=0.1)

for chunk in llm.stream("What is the capital of France?"):
    if isinstance(chunk.content, list):
        for item in chunk.content:
            if isinstance(item, dict) and item.get('type') == 'text' and 'text' in item:
                print(item['text'], end="", flush=True)
    elif isinstance(chunk.content, str):
        print(chunk.content, end="", flush=True)