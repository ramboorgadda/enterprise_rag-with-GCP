import logfire
from app.agents.state import AgentState
from app.gateway import portkey_client, extract_cache_status

# def _get_llm() -> ChatGroq | None:
#    key = (settings.GROQ_API_KEY or "").strip()
#    if not key:
#        return None
#    return ChatGroq(
#        model=settings.GROQ_MODEL,
#        api_key=key,
#        temperature=0.1,
#    )

def generate_node(state: AgentState):
    """
    Synthesizes a response using both Documentation Context AND Conversation History.

    """
    query = state["current_query"]
    logfire.info(f"Responder node started. query={query}")
    # Construct the prompt for GROQ based on the agent's state
    history=f""
    for msg in state["messages"][:-1]:
        role = "User" if msg["role"] == "user" else "Assistant"
        content = msg.get("content", "")
        history += f"{role}: {content}\n"
    user_message = state["messages"][-1]["content"] if state["messages"] else ""
    if query == "CONVERSATIONAL":
            logfire.info("Responder mode: conversational (memory only).")
            prompt = f"""
            You are a friendly and helpful Enterprise AI Assistant.
            Answer the user's latest message using the CONVERSATION HISTORY below.
        
            CONVERSATION HISTORY:
            {history}
        
            LATEST MESSAGE:
            "{user_message}"
            """
    else:
            logfire.info("Responder mode: technical RAG.")
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
    with logfire.span("🧠 Responder Node - Synthesizing Response", query=query, docs_count=len(state.get("documents", []))):
        try:
            response = portkey_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                temperature = 0.1
            )
            logfire.info("Response generated successfully.")
            content = response.choices[0].message.content
            cache_status = extract_cache_status(response)
            is_cache_hit = cache_status == "HIT"
            if is_cache_hit:
                logfire.info("⚡ Gateway Cache Hit — response served from Portkey cache.")
                plan_update = state["plan"] + ["Cache: Hit ⚡"]
                status = "Cache hit — instant response."
            else:
                logfire.info("✅ Response synthesised via LLM.")
                plan_update = state["plan"]
                status = "Response generated."
            return {
                "final_answer": content,
                "status": status,
                "plan": plan_update,
                "messages": [{"role": "assistant", "content": content}]
            }
        except Exception as e:
            logfire.warning(f"LLM unavailable during response generation, using retrieval fallback: {e}")
            return {
                "final_answer": "I could not generate a response right now. Please try again later.",
                "status": "Response generation failed.",
                "messages": [{"role": "assistant", "content": "I could not generate a response right now. Please try again later."}],
            }