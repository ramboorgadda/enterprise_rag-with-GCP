import logfire
from langchain_groq import ChatGroq
from app.agents.state import AgentState
from app.config import settings

def _get_llm() -> ChatGroq | None:
    key = (settings.GROQ_API_KEY or "").strip()
    if not key:
        return None
    return ChatGroq(
        model=settings.GROQ_MODEL,
        api_key=key,
        temperature=0.1,
    )


def generate_node(state: AgentState):
    """
    Synthesizes a response using both Documentation Context AND Conversation History.

    """
    query = state["current_query"]
    llm = _get_llm()
    if llm is None:
        msg = "GROQ_API_KEY is missing. Set it in your .env to enable response generation."
        logfire.error(msg)
        return {
            "final_answer": "I cannot generate a response right now because GROQ_API_KEY is not configured.",
            "status": msg,
            "messages": [{"role": "assistant", "content": "Please configure GROQ_API_KEY and retry."}],
        }

    # Construct the prompt for GROQ based on the agent's state
    history=f""
    for msg in state["messages"][:-1]:
        role = "User" if msg["role"] == "user" else "Assistant"
        content = msg.get("content", "")
        history += f"{role}: {content}\n"
    user_message = state["messages"][-1]["content"] if state["messages"] else ""
    if query == "CONVERSATIONAL":
            logfire.info("Handling conversational query using memory only.")
            prompt = f"""
            You are a friendly and helpful Enterprise AI Assistant.
            Answer the user's latest message using the CONVERSATION HISTORY below.
        
            CONVERSATION HISTORY:
            {history}
        
            LATEST MESSAGE:
            "{user_message}"
            """
    else:
            logfire.info("Generating technical RAG response.")
            max_context_chars = 25000
            full_context = ""
            for doc in state["documents"]:
                text = doc.get("content", "") if isinstance(doc, dict) else str(doc)
                if len(full_context) + len(text) <= max_context_chars:
                    full_context += text + "\n\n"
                else:
                    logfire.warning("Context truncated to fit Groq TPM limits.")
                    break
            prompt = f"""
        You are a Senior Technical Architect. 
        Answer the question using the TECHNICAL CONTEXT provided. 
        
        TECHNICAL CONTEXT:
        {full_context}
        
        CONVERSATION HISTORY:
        {history}
        
        USER QUESTION:
        "{user_message}"
        """
    with logfire.span("🧠 Generate Node - Synthesizing Response"):
        try:
            response = llm.invoke(prompt)
            logfire.info("Response generated successfully.")
            return {
                "final_answer": response.content,
                "status": "Response generated successfully.",
                "messages": [{"role": "assistant", "content": response.content}]
            }
        except Exception as e:
            logfire.warning(f"LLM unavailable during response generation, using retrieval fallback: {e}")
            return {
                "final_answer": "I could not generate a response right now. Please try again later.",
                "status": "Response generation failed.",
                "messages": [{"role": "assistant", "content": "I could not generate a response right now. Please try again later."}],
            }