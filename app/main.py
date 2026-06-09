import logfire
import os
from dotenv import load_dotenv

load_dotenv()


def configure_logfire() -> None:
    enable_remote = (os.getenv("LOGFIRE_ENABLE_REMOTE") or "false").strip().lower() == "true"
    token = (os.getenv("LOGFIRE_TOKEN") or "").strip()
    placeholder = token.lower() in {"", "your-logfire-token", "none", "null"}

    if not enable_remote:
        logfire.configure(send_to_logfire=False)
        return

    if placeholder:
        logfire.configure(send_to_logfire=False)
        return

    try:
        logfire.configure(token=token)
    except Exception:
        # Keep the API running locally even when the token is invalid.
        logfire.configure(send_to_logfire=False)


configure_logfire()
from fastapi import FastAPI,Response
from app.agents.graph import rag_agent

from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="Enterprise Agentic RAG API")

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
        response = rag_agent.invoke(initial_state, config=config)
        return {
            "question": q,
            "answer": response.get("final_answer"),
            "thought_process": response.get("plan"),
            "status": response.get("status"),
            "sources": response.get("documents", [])
            }
    except Exception as e:
        logfire.error(f"Error processing query: {e}")
        return {
            "question": q,
            "answer": "I apologize, but I encountered an internal error while processing your request. Please try again later.",
            "thought_process": ["Error encountered during execution."],
            "status": "Error",
            "sources": []
        }