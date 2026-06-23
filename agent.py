#!/usr/bin/env python3
"""
JARVIS.AI - Local command agent with HTTP backend.

Run CLI mode:
  python agent.py

Run API server mode:
  pip install -r requirements.txt
  python agent.py serve

The API server exposes:
  GET /status
  POST /command
"""

import os
import sys
import time
import platform
import datetime
import webbrowser
import subprocess
import io
import zipfile
from typing import Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

VERSION = "1.2"
PORT = 8000

# Placeholder for future API keys / config
AI_CONFIG = {
    "openai_api_key": os.environ.get("OPENAI_API_KEY"),
    "anthropic_api_key": os.environ.get("ANTHROPIC_API_KEY"),
    "ollama_model": os.environ.get("OLLAMA_MODEL", "jarvis"),
}

app = FastAPI(title="JARVIS.AI Local Agent")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


class CommandRequest(BaseModel):
    command: str


class CommandResponse(BaseModel):
    response: str


@app.get("/status")
async def status() -> Dict[str, str]:
    return {"status": "online", "version": VERSION}


@app.post("/command", response_model=CommandResponse)
async def command_endpoint(payload: CommandRequest) -> CommandResponse:
    if not payload.command.strip():
        raise HTTPException(status_code=400, detail="Command cannot be empty.")

    if any(keyword in payload.command.lower() for keyword in ["create folder", "make folder", "create file", "make file", "open", "system", "info"]):
        result = execute_system_command(payload.command)
    else:
        result = simulate_ai_response(payload.command)

    return CommandResponse(response=result)


def create_agent_zip_bytes() -> bytes:
    """Create an in-memory ZIP containing agent.py, requirements.txt, and start.bat.

    If requirements.txt is missing, include a default minimal requirements file.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    agent_path = os.path.join(base_dir, "agent.py")
    req_path = os.path.join(base_dir, "requirements.txt")

    start_bat = (
        "@echo off\r\n"
        "echo Installing dependencies...\r\n"
        "py -m pip install -r requirements.txt\r\n"
        "echo Starting JARVIS.AI Server...\r\n"
        "py agent.py serve\r\n"
        "pause\r\n"
    )

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # Add agent.py (current file)
        try:
            with open(agent_path, "rb") as f:
                zf.writestr("agent.py", f.read())
        except Exception:
            # Fallback: write current module's source if file read fails
            zf.writestr("agent.py", "".join(open(__file__, "r", encoding="utf-8").readlines()))

        # Add requirements.txt if present, otherwise add a minimal default
        if os.path.exists(req_path):
            with open(req_path, "rb") as f:
                zf.writestr("requirements.txt", f.read())
        else:
            default_reqs = "fastapi\nuvicorn\n"
            zf.writestr("requirements.txt", default_reqs)

        # Add start.bat for Windows convenience
        zf.writestr("start.bat", start_bat)

    return buf.getvalue()


@app.get("/download-agent")
async def download_agent():
    """Return a ZIP package containing the agent sources and helper scripts."""
    data = create_agent_zip_bytes()
    return StreamingResponse(io.BytesIO(data), media_type="application/zip", headers={"Content-Disposition": "attachment; filename=jarvis_agent.zip"})


def execute_system_command(user_input: str) -> str:
    cmd = user_input.lower().strip()

    if "create folder" in cmd or "make folder" in cmd:
        parts = user_input.split()
        folder_name = parts[-1] if len(parts) > 2 else "new_folder"
        try:
            os.makedirs(folder_name, exist_ok=True)
            return f"SUCCESS: Folder '{folder_name}' has been successfully created."
        except Exception as e:
            return f"ERROR: Failed to create folder. Details: {e}"

    if "create file" in cmd or "make file" in cmd:
        parts = user_input.split()
        file_name = parts[-1] if len(parts) > 2 else "new_file.txt"
        try:
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(f"# File created by JARVIS.AI agent on {datetime.datetime.now()}\n")
            return f"SUCCESS: File '{file_name}' has been successfully created."
        except Exception as e:
            return f"ERROR: Failed to create file. Details: {e}"

    if "open web" in cmd or "open" in cmd:
        parts = user_input.split()
        if len(parts) > 1:
            target = parts[-1].lower()
            if "youtube" in target:
                url = "https://www.youtube.com"
            elif "github" in target:
                url = "https://github.com/Tolorue"
            else:
                url = target if target.startswith("http") else f"https://{target}"
            try:
                webbrowser.open(url)
                return f"SUCCESS: Opening browser with URL: {url}"
            except Exception as e:
                return f"ERROR: Failed to open website. Details: {e}"
        return "ERROR: No website specified. (Example: open youtube)"

    if "info" in cmd or "system" in cmd:
        info = (
            f"\n   [OS]: {platform.system()} {platform.release()}\n"
            f"   [Architecture]: {platform.machine()}\n"
            f"   [Current Time]: {datetime.datetime.now().strftime('%H:%M:%S')}"
        )
        return f"System information generated:{info}"

    return f"Request '{user_input}' forwarded to local AI pipeline. (No system action keyword detected)."


def get_response_via_ollama(prompt: str) -> str:
    model = AI_CONFIG.get("ollama_model") or "jarvis"
    try:
        proc = subprocess.run(
            ["ollama", "run", model, prompt],
            capture_output=True,
            text=True,
            timeout=20,
        )
        if proc.returncode == 0:
            return proc.stdout.strip()
        return f"[JARVIS]: Ollama error: {proc.stderr.strip() or 'non-zero exit code'}"
    except FileNotFoundError:
        return "[JARVIS]: Ollama CLI not found. Install Ollama or set USE_OLLAMA=0."
    except Exception as e:
        return f"[JARVIS]: Ollama call failed: {e}"


def get_response_via_openai(prompt: str) -> str:
    # Optional OpenAI example:
    # pip install openai
    # import openai
    # openai.api_key = AI_CONFIG.get("openai_api_key")
    # resp = openai.ChatCompletion.create(
    #     model="gpt-4o-mini",
    #     messages=[{"role": "user", "content": prompt}],
    #     max_tokens=300,
    # )
    # return resp.choices[0].message.content.strip()
    return "[JARVIS]: (OpenAI placeholder) - configure OpenAI to enable this path."


def simulate_ai_response(prompt: str) -> str:
    use_ollama = os.environ.get("USE_OLLAMA", "1")
    if use_ollama != "0":
        response = get_response_via_ollama(prompt)
        if response and not response.startswith("[JARVIS]: Ollama CLI not found"):
            return response

    if AI_CONFIG.get("openai_api_key"):
        return get_response_via_openai(prompt)

    time.sleep(0.6)
    return f"[JARVIS]: Processing your request...\n[JARVIS]: Mock response for '{prompt}'."


def welcome():
    print("=========================================")
    print(f"   JARVIS.AI v{VERSION} - Autonomous OS Agent  ")
    print("=========================================")
    print("Available local commands for testing:")
    print("  -> create folder [name]")
    print("  -> create file [name.js]")
    print("  -> open youtube / open github")
    print("  -> system info")
    print("  -> exit (to terminate session)\n")


def handle_user_input(user_input: str) -> bool:
    cleaned = user_input.strip()
    if cleaned == "":
        return True

    cmd = cleaned.lower()
    if cmd in ["exit", "quit", "q"]:
        print("[JARVIS]: Disconnecting secure local core. Session ended.")
        return False

    if any(keyword in cmd for keyword in ["create folder", "make folder", "create file", "make file", "open", "system", "info"]):
        response = execute_system_command(user_input)
        print(f"[JARVIS]: {response}\n")
        return True

    print("[JARVIS]: Analyzing workspace and executing command...")
    response = simulate_ai_response(cleaned)
    print(f"[JARVIS]: {response}\n")
    return True


def run_cli():
    welcome()
    try:
        while True:
            try:
                user_input = input("user@system:~$ ")
            except (KeyboardInterrupt, EOFError):
                print("\n[JARVIS]: Emergency cutoff triggered. Goodbye.")
                sys.exit(0)

            if not handle_user_input(user_input):
                break
    except Exception as e:
        print(f"[JARVIS]: An error occurred: {e}")
        sys.exit(1)


def run_server():
    import uvicorn
    print(f"Starting JARVIS API server on http://127.0.0.1:{PORT}")
    uvicorn.run("agent:app", host="127.0.0.1", port=PORT, log_level="info")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in {"serve", "server", "api"}:
        run_server()
    else:
        run_cli()
