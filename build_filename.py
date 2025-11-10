from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
import os
import json
import subprocess
import socket
import argparse
import re

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

def ch_to_eng(text: str) -> str:
    """Translate Chinese to English"""
    system = SystemMessage(
        content="You are a Mandarin to English translator. Only translate without adding or removing anything"
    )
    human = HumanMessage(content=text)
    resp = LLM.invoke(input=[system, human])
    return resp.content

WINDOWS_HOST_IP = get_windows_host_ip()

LLM = ChatOllama(base_url=f"http://{WINDOWS_HOST_IP}:11434",
                 model="qwen3:4b-instruct-2507-q8_0",
                 temperature=0,
                 max_tokens=4096)

def main(input_dir: str, json_path: str):
    filename_translation = {}

    for folder in os.listdir(input_dir):
        for file in os.listdir(f"{input_dir}/{folder}"):
            base_name = os.path.splitext(file)[0]
            # Remove trailing _0, _1, _2, etc.
            base_name_without_suffix = re.sub(r'_\d+$', '', base_name)
            filename_translation[base_name_without_suffix] = ""

    with open(file=json_path, mode="w", encoding="utf-8") as f:
        json.dump(filename_translation, f, ensure_ascii=False, indent=2)
    
    for filename in list(filename_translation):
        if filename_translation[filename] == "":
            translated_filename = ch_to_eng(filename)
            filename_translation[filename] = translated_filename

            with open(file=json_path, mode="w", encoding="utf-8") as f:
                json.dump(filename_translation, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Translate filenames from Chinese to English")
    parser.add_argument("--input_dir", type=str, required=True, help="Input directory containing folders with files")
    parser.add_argument("--json_path", type=str, required=True, help="Path to save the JSON translation file")
    args = parser.parse_args()

    main(input_dir=args.input_dir, json_path=args.json_path)