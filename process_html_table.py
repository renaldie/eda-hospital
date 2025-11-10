import os
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
import argparse

LLM = ChatOllama(model="qwen3:4b-instruct-2507-q8_0",
                 temperature=0,
                 max_tokens=8096)

def html_table_formatter(text: str) -> str:
    system = SystemMessage(
        content="""
        You are a HTML Table to Markdown Table formatter. 
        Only format the following HTML Table to a proper Markdown Table without adding or removing anything .
        Retain all of the other markdown structure
        """
    )
    human = HumanMessage(content=text)
    resp = LLM.invoke(input=[system, human])
    return resp.content

def main(input_dir: str):
    for folder in os.listdir(f"{input_dir}"):
        for filename in os.listdir(f"{input_dir}/{folder}"):
            if filename.endswith(".md"):
                filepath = f"{input_dir}/{folder}/{filename}"
                
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                
                formatted_content = html_table_formatter(content)
                
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(formatted_content)
                
                print(f"Processed: {filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Format HTML Table to a proper Markdown Table"
    )
    parser.add_argument(
        "--input_dir",
        required=True,
        help="The input directory to be processed"
    )
    args = parser.parse_args()
    
    main(
        input_dir=args.input_dir,
    )