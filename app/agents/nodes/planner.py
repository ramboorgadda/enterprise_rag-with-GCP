from langchain_groq import ChatGroq
from app.agents.state import AgentState
from app.config import settings
import logfire


def _get_llm() -> ChatGroq | None:
    key = (settings.GROQ_API_KEY or "").strip()
    if not key:
        return None
    return ChatGroq(model=settings.GROQ_MODEL, api_key=key)

def planner_node(state: AgentState):
    """
    The Planner Node takes the current state of the agent, including the conversation history and retrieved knowledge,
    and generates a response to the user. It uses the GROQ reasoning engine to analyze the context and produce
    a coherent and relevant reply.

    Args:
        state (AgentState): The current state of the agent, containing conversation history and retrieved knowledge.

    """
        # Construct the prompt for GROQ based on the agent's state
    llm = _get_llm()
    if llm is None:
        user_message = state["messages"][-1]["content"] if state["messages"] else ""
        return {
            "current_query": user_message,
            "status": "GROQ_API_KEY missing. Falling back to direct retrieval query.",
            "plan": ["Intent: Fallback", "Planner LLM unavailable"],
        }

    history=f""
    for msg in state["messages"][:-1]:
        role = "User" if msg["role"] == "user" else "Assistant"
        content = msg.get("content", "")
        history += f"{role}: {content}\n"
    user_message = state["messages"][-1]["content"] if state["messages"] else ""
    prompt = f"""
        You are an intelligent Assistant Planner. 
        Analyze the conversation history and the latest user message.
        CONVERSATION HISTORY:
        {history}
    
        LATEST MESSAGE:
        "{user_message}"
    
        Task:
        1. If the latest message is a greeting (hi, hello) or a question that can be answered using ONLY the conversation history above (e.g., "what is my name"), respond with 'CONVERSATIONAL'.
        2. If it is a technical question about Kubernetes, Intel, or Networking that requires fresh documentation, output a refined search query.
    
        Output ONLY 'CONVERSATIONAL' or the search query.
        """

    try:
        with logfire.span("🧠 Planner Node - Generating Response", prompt=prompt):
            decision_raw = llm.invoke(prompt)
            decision = (getattr(decision_raw, "content", str(decision_raw)) or "").strip()
            logfire.info(f"Intent identified: {decision}")
    except Exception as e:
        logfire.error(f"Planner generation failed, using fallback retrieval route: {e}")
        return {
            "current_query": user_message,
            "status": "Planner LLM failed. Falling back to direct retrieval query.",
            "plan": ["Intent: Fallback", "Planner invocation failed"],
        }

    if decision.upper() == "CONVERSATIONAL":
        return {
        "current_query": "CONVERSATIONAL",
        "status": "Handling conversationally (using memory)...",
        "plan": ["Intent: Conversational/Memory", "Retrieval: Skipped"]
        }

    return {
    "current_query": decision or user_message,
    "status": f"Technical research needed. Searching for: {decision or user_message}",
    "plan": ["Intent: Technical", f"Search Term: {decision or user_message}"]
    }