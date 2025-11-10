from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
import os
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language
from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain_core.documents import Document
from typing import List
import uuid
import subprocess
import socket
import argparse

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

def markdown_to_document(file_path: str, chunk_size: int, chunk_overlap: int, is_execute: bool = False) -> List[Document]:
    if is_execute:
        # Load metadata
        metadata_loader = UnstructuredMarkdownLoader(file_path, mode="elements")
        metadata_docs = metadata_loader.load()
        
        # Load content
        with open(file_path) as f:
            file = f.read()
        text_splitter = RecursiveCharacterTextSplitter.from_language(language=Language.MARKDOWN, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        documents = text_splitter.create_documents([file], [metadata_docs[0].metadata])

        
        return documents

def combine_list_metadata(document: Document, key_to_combine: str, is_execute: bool = False):
    if is_execute:
        langs = document.metadata.get(key_to_combine)
        if langs is None:
            document.metadata[key_to_combine] = ""
        elif isinstance(langs, str):
            pass
        else:
            try:
                document.metadata[key_to_combine] = ",".join(map(str, langs))
            except TypeError:
                import json
                document.metadata[key_to_combine] = json.dumps(langs)

def add_documents(vector_store: Chroma, documents: List[Document], is_execute: bool = False):
    if is_execute:
        ids = [str(uuid.uuid4()) for _ in documents]
        vector_store.add_documents(documents=documents, ids=ids)

WINDOWS_HOST_IP = get_windows_host_ip()

EMBEDDING = OllamaEmbeddings(base_url=f"http://{WINDOWS_HOST_IP}:11434",
                             model="embeddinggemma:300m")

def main(collection_name: str, persist_directory: str, input_dir: str, dry_run: bool = True):
    if not dry_run:
        vector_store = Chroma(
            collection_name=collection_name,
            embedding_function=EMBEDDING,
            persist_directory=persist_directory,
            create_collection_if_not_exists=True,
        )

        documents = []

        for folder in os.listdir(input_dir):
            for file in os.listdir(f"{input_dir}/{folder}"):
                if file.endswith(".md"):
                    file_path = f"{input_dir}/{folder}/{file}"
                    document = markdown_to_document(file_path=file_path,
                                        chunk_size=2048,
                                        chunk_overlap=200,
                                        is_execute=True)
                    if document is not None:
                        documents.extend(document)

        for document in documents:
            combine_list_metadata(document=document, key_to_combine="languages", is_execute=True)

        add_documents(vector_store=vector_store, documents=documents, is_execute=True)

        print(f"Added: {len(vector_store.get()['documents'])}" documents)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Add files to VectorDB"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually add files (default is dry-run mode)"
    )
    parser.add_argument(
        "--collection_name",
        required=True,
        help="The name of the collecton"
    )
    parser.add_argument(
        "--persist_directory",
        required=True,
        help="Output directory where the VectorDB will be saved"
    )
    parser.add_argument(
        "--input_dir",
        required=True,
        help="The input directory for the VectorDB"
    )
    args = parser.parse_args()
    
    main(
        collection_name=args.collection_name,
        persist_directory=args.persist_directory,
        input_dir=args.input_dir,
        dry_run=not args.execute,
    )