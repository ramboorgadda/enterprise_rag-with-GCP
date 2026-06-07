from langchain_groq import ChatGroq
from app.agents.state import AgentState
from app.config import settings
import logfire
llm = ChatGroq(model=settings.GROQ_MODEL, api_key=settings.GROQ_API_KEY)

def planner_node(state: AgentState):
    """
    The Planner Node takes the current state of the agent, including the conversation history and retrieved knowledge,
    and generates a response to the user. It uses the GROQ reasoning engine to analyze the context and produce
    a coherent and relevant reply.

    Args:
        state (AgentState): The current state of the agent, containing conversation history and retrieved knowledge.

    """
        # Construct the prompt for GROQ based on the agent's state
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
        
        with logfire.span("🧠 Planner Node - Generating Response", prompt=prompt):
            decision = llm.invoke(prompt)
            logfire.info(f"Intent identified: {decision}")
        if decision == "CONVERSATIONAL":
            return {
            "current_query": "CONVERSATIONAL",
            "status": "Handling conversationally (using memory)...",
            "plan": ["Intent: Conversational/Memory", "Retrieval: Skipped"]
            }
        return {
        "current_query": decision,
        "status": f"Technical research needed. Searching for: {decision}",
        "plan": ["Intent: Technical", f"Search Term: {decision}"]
        }