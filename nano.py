import argparse
import sys
import json
import time
import os
from llama_cpp import Llama

# Default configuration
DEFAULT_MODEL = "Nano-Analyst-1.5B-v1.Q4_K_M.gguf"

def load_model(model_path):
    if not os.path.exists(model_path):
        print(f"Error: Model file '{model_path}' not found.")
        sys.exit(1)
    print(f"Loading {model_path} (runs on CPU)...")
    return Llama(model_path=model_path, n_ctx=2048, verbose=False)

def analyze_line(llm, line):
    prompt = f"<|im_start|>system\nExtract logs to JSON.<|im_end|>\n<|im_start|>user\n{line}<|im_end|>\n<|im_start|>assistant\n"
    output = llm(prompt, max_tokens=256, stop=["<|im_end|>"], echo=False)
    try:
        text = output['choices'][0]['text'].strip()
        if text.startswith("```"): text = text.replace("```json", "").replace("```", "")
        return json.loads(text)
    except:
        return {"raw": text}

def mode_watch(args):
    """Simulates 'tail -f' on a file and analyzes new lines."""
    llm = load_model(args.model)
    print(f"👀 Watching file: {args.file}")
    print("------------------------------------------------")
    
    # Open file and seek to the end (so we don't parse old history)
    try:
        with open(args.file, 'r') as f:
            f.seek(0, os.SEEK_END)
            while True:
                line = f.readline()
                if not line:
                    time.sleep(0.5) # Wait for new data
                    continue
                
                if line.strip(): # Ignore empty lines
                    print(f"⚡ Detecting: {line.strip()[:50]}...")
                    result = analyze_line(llm, line)
                    print(json.dumps(result, indent=2))
                    print("-" * 30)
    except FileNotFoundError:
        print(f"Error: File '{args.file}' not found.")

def mode_scan(args):
    """Analyzes a single string provided in the command line."""
    llm = load_model(args.model)
    result = analyze_line(llm, args.text)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Nano-Analyst: Edge AI Log Parser")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Command: watch
    # Usage: python nano.py watch server.log
    watch_parser = subparsers.add_parser("watch", help="Tail a log file and analyze in real-time")
    watch_parser.add_argument("file", help="Path to the log file")
    watch_parser.add_argument("--model", default=DEFAULT_MODEL, help="Path to GGUF model")

    # Command: scan
    # Usage: python nano.py scan "Oct 12 error..."
    scan_parser = subparsers.add_parser("scan", help="Analyze a single log string")
    scan_parser.add_argument("text", help="Log string to analyze")
    scan_parser.add_argument("--model", default=DEFAULT_MODEL, help="Path to GGUF model")

    args = parser.parse_args()
    
    if args.command == "watch":
        mode_watch(args)
    elif args.command == "scan":

        mode_scan(args)
