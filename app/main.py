from app.guardrails import chat, COLANG_EXP2, YAML_BASE
from nemoguardrails import RailsConfig, LLMRails
import logfire
import os
from pathlib import Path
from dotenv import load_dotenv
import asyncio
from typing import Optional
from langchain_groq import ChatGroq


ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=ROOT_DIR / ".env", override=True)


def configure_logfire() -> None:
    send_pref = (os.getenv("LOGFIRE_SEND_TO_LOGFIRE") or os.getenv("LOGFIRE_ENABLE_REMOTE") or "if-token-present").strip().lower()
    if send_pref in {"1", "true", "yes", "on"}:
        send_to_logfire = True
    elif send_pref in {"0", "false", "no", "off"}:
        send_to_logfire = False
    else:
        send_to_logfire = "if-token-present"

    token = (os.getenv("LOGFIRE_TOKEN") or "").strip()
    placeholder = token.lower() in {"", "your-logfire-token", "none", "null"}

    try:
        if not placeholder:
            logfire.configure(
                token=token,
                service_name="enterprise-backend-service",
                send_to_logfire=send_to_logfire,
            )
            print(f"[Logfire] Backend configured (send_to_logfire={send_to_logfire}).")
        else:
            logfire.configure(
                service_name="enterprise-backend-service",
                send_to_logfire=False,
            )
            print("[Logfire] Backend local only (LOGFIRE_TOKEN missing/placeholder).")
    except Exception as exc:
        # Keep the API running locally even when tracing export fails.
        logfire.configure(
            service_name="enterprise-backend-service",
            send_to_logfire=False,
        )
        print(f"[Logfire] Backend tracing disabled due to configuration error: {exc}")


configure_logfire()


def log_info(message: str) -> None:
    """Send info to Logfire and always mirror to local console."""
    try:
        logfire.info(message)
    except Exception:
        pass
    print(f"[INFO] {message}")


def log_error(message: str) -> None:
    """Send error to Logfire and always mirror to local console."""
    try:
        logfire.error(message)
    except Exception:
        pass
    print(f"[ERROR] {message}")


from fastapi import FastAPI,Response
from app.agents.graph import rag_agent

from pydantic import BaseModel
from typing import Optional


# Load .env from project root (one level up from notebooks/)
load_dotenv(dotenv_path="../.env")
ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=ROOT_DIR / ".env", override=True)

load_dotenv(dotenv_path="../.env")

GROQ_API_KEY   = os.getenv("GROQ_API_KEY")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")

llm = ChatGroq(api_key=GROQ_API_KEY,
        model="llama-3.3-70b-versatile",
        temperature=0)  # Initialize the Groq client
print("Groq client initialized.")

app = FastAPI(title="Enterprise Agentic RAG API")

try:
    logfire.instrument_fastapi(app)
except Exception:
    # Do not fail API startup if instrumentation is unavailable in local env.
    pass

class QueryRequest(BaseModel):
    query: str
    thread_id: Optional[str] = "default user"

@app.get("/")
def home():
    return {"message": "Welcome to the Enterprise Agentic RAG API. Send POST requests to /query with your questions."}


@app.get("/graph")
def get_graph_image():
    try:
        graph_image = rag_agent.get_graph().draw_mermaid_png()
        return Response(content=graph_image, media_type="image/png")
    except Exception as e:
        return {"error": f"Failed to generate graph image: {e}"}

@app.post("/query")
def query(request: QueryRequest):
    
    q= request.query
    
    thread_id= request.thread_id
    initial_state = {
        "messages": [{"role": "user", "content": q}],
        "current_query": q,
        "documents": [],
        "plan": ["Start"],
        "status": "Initalizing the Graph...",
    }
    config = {"configurable": {"thread_id": thread_id}}
    try:
        config_exp2 = RailsConfig.from_content(colang_content=COLANG_EXP2, yaml_content=YAML_BASE)
        rails_exp2 = LLMRails(config=config_exp2, llm=llm)

        guardrail_response = chat(rails_exp2, q)
        response_str = str(guardrail_response.get("content", ""))
        log_info(f"Guardrail response: {response_str[:200]}")
        
        # Check if the response is a guardrail block (any of the refusal messages)
        block_indicators = [
            "I'm an Enterprise IT Assistant focused on",
            "I maintain consistent guidelines",
            "I can't assist with unauthorised access"
        ]
        
        is_blocked = any(indicator in response_str for indicator in block_indicators) if response_str else False
        
        if is_blocked:
            log_info(f"Query blocked by guardrail: {q}")
            return {
                "question": q,
                "answer": response_str,
                "thought_process": ["Blocked by Guardrail."],
                "status": "Blocked by Guardrail",
                "sources": []
            }
        
        log_info(f"Query passed guardrails, invoking RAG agent: {q}")
        response = rag_agent.invoke(initial_state, config=config)
        return {
            "question": q,
            "answer": response.get("final_answer"),
            "thought_process": response.get("plan"),
            "status": response.get("status"),
            "sources": response.get("documents", [])
            }
    except Exception as e:
        log_error(f"Error processing query: {e}")
        return {
            "question": q,
            "answer": "I apologize, but I encountered an internal error while processing your request. Please try again later.",
            "thought_process": ["Error encountered during execution."],
            "status": "Error",
            "sources": []
        }