import os
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
import argparse
import subprocess
import socket

# Get Windows host IP from WSL
def get_windows_host_ip():
    # Method 1: Try WSL2 bridge interface (default route)
    try:
        result = subprocess.run(
            ["ip", "route", "show", "default"],
            capture_output=True,
            text=True
        )
        for line in result.stdout.split('\n'):
            if 'default' in line and 'via' in line:
                parts = line.split()
                via_index = parts.index('via')
                ip = parts[via_index + 1]
                # Test if Ollama is accessible at this IP
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    sock.connect((ip, 11434))
                    sock.close()
                    print(f"✓ Found Ollama at {ip} (WSL default gateway)")
                    return ip
                except:
                    print(f"✗ Port 11434 not accessible at {ip}")
    except Exception as e:
        print(f"✗ Method 1 failed: {e}")
    
    # Method 2: Try /etc/resolv.conf nameserver
    try:
        result = subprocess.run(
            ["cat", "/etc/resolv.conf"],
            capture_output=True,
            text=True
        )
        for line in result.stdout.split('\n'):
            if 'nameserver' in line:
                ip = line.split()[1]
                # Test if Ollama is accessible at this IP
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    sock.connect((ip, 11434))
                    sock.close()
                    print(f"✓ Found Ollama at {ip} (resolv.conf)")
                    return ip
                except:
                    print(f"✗ Port 11434 not accessible at {ip}")
    except Exception as e:
        print(f"✗ Method 2 failed: {e}")
    
    # Fallback to localhost
    print("⚠ Falling back to localhost")
    return "127.0.0.1"

def html_table_formatter(text: str) -> str:
    system = SystemMessage(
        content="""
        You are a HTML Table to Markdown Table formatter. 
        Only format the following HTML Table to a proper Markdown Table without adding or removing anything .
        Retain all of the other markdown structures
        """
    )
    human = HumanMessage(content=text)
    resp = LLM.invoke(input=[system, human])
    return resp.content

WINDOWS_HOST_IP = get_windows_host_ip()

LLM = ChatOllama(base_url=f"http://{WINDOWS_HOST_IP}:11434",
                 model="qwen3:4b-instruct-2507-q8_0",
                 temperature=0,
                 max_tokens=32768)

def main(input_dir: str, output_dir: str):
    for folder in os.listdir(f"{input_dir}"):
        for filename in os.listdir(f"{input_dir}/{folder}"):
            if filename.endswith(".md"):
                filepath = f"{input_dir}/{folder}/{filename}"
                
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()

                    if content.count("<table") >= 1:
                        formatted_content = html_table_formatter(content)

                        output_folder = os.path.join(output_dir, folder)
                        os.makedirs(output_folder, exist_ok=True)
                        output_filepath = os.path.join(output_folder, filename)
                        
                        with open(output_filepath, "w", encoding="utf-8") as f:
                            f.write(formatted_content)
                        
                        print(f"Processed: {filename}")
                    else:
                        pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Format HTML Table to a proper Markdown Table"
    )
    parser.add_argument(
        "--input_dir",
        required=True,
        help="The input directory to be processed"
    )
    parser.add_argument(
        "--output_dir",
        required=True,
        help="The output directory for processed files"
    )
    args = parser.parse_args()
    
    main(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
    )