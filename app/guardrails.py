import re
import os
import logfire
from pathlib import Path
import asyncio
from typing import Optional
from langchain_groq import ChatGroq
import nest_asyncio
from nemoguardrails import RailsConfig, LLMRails
nest_asyncio.apply()
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=ROOT_DIR / ".env", override=True)

load_dotenv(dotenv_path="../.env")

GROQ_API_KEY   = os.getenv("GROQ_API_KEY")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")

llm = ChatGroq(api_key=GROQ_API_KEY,
        model="llama-3.3-70b-versatile",
        temperature=0)  # Initialize the Groq client
print("Groq client initialized.")

def chat(rails,message):
    """Send a message through the rails and print input + output."""
    print(f"\n{'-'*62}")
    print(f"User : {message}")
    response = rails.generate(messages=[{"role": "user", "content": message}])
    print(f"Bot  : {response}")
    print(f"{'-'*62}")
    return response
COLANG_EXP2 = """
define user ask off topic
  \"tell me a joke\"
  \"what is the capital of france\"
  \"write me a poem\"
  \"what is 2 plus 2\"
  \"what should I eat for dinner\"
  \"who won the game yesterday\"
  \"recommend a movie\"

define bot refuse off topic
  \"I'm an Enterprise IT Assistant focused on Kubernetes, Intel hardware, and networking. I can't help with that — but ask me anything technical!\"

define flow handle off topic
  user ask off topic
  bot refuse off topic
"""
# ─────────────────────────────────────────────────────────────
# YAML: LLM backend config + system instructions
# We put engine=openai as a placeholder — it is overridden by llm= param below
# ─────────────────────────────────────────────────────────────
YAML_BASE = """
models:
  - type: main
    engine: openai
    model: gpt-3.5-turbo

instructions:
  - type: general
    content: |
      You are an Enterprise IT Assistant specialising in:
      - Kubernetes (deployment, scaling, operators, networking)
      - Intel hardware (CPUs, FPGAs, NICs, SRIOV)
      - Enterprise networking (SDN, VLANs, BGP, routing)
      Only answer questions about these topics. Be professional and concise.
"""
print("Guardrails configured.")